import streamlit as st
import pandas as pd
import google.generativeai as genai
from googleapiclient.discovery import build
from google.oauth2 import service_account
import plotly.express as px
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
import logging
import sys
from dateutil import parser
import re
from config.constants import TRANSACTION_TYPES, CATEGORIES
# from services.google_sheets import get_sheets_service

# Configure Rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
log = logging.getLogger("expense_tracker")

# Load environment variables
load_dotenv()
log.info("✨ Environment variables loaded")

st.set_page_config (layout='wide')

# Configure Gemini AI
@st.cache_resource
def get_gemini_model():
    """Cache Gemini AI configuration"""
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-pro')
        log.info("🤖 Gemini AI configured successfully")
        return model
    except Exception as e:
        log.error(f"❌ Failed to configure Gemini AI: {str(e)}")
        raise

# Google Sheets setup
@st.cache_resource
def get_sheets_service():
    """Cache Google Sheets service configuration"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_SHEETS_CREDENTIALS'), 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds)
        log.info("📊 Google Sheets API connected successfully")
        return service
    except Exception as e:
        log.error(f"❌ Failed to connect to Google Sheets: {str(e)}")
        raise

# Replace the direct configuration with cached versions
try:
    model = get_gemini_model()
    service = get_sheets_service()
    SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
except Exception as e:
    log.error(f"❌ Failed to initialize services: {str(e)}")
    sys.exit(1)


@st.cache_data(ttl=300)
def get_categories():
    """Cache the categories dictionary to prevent reloading"""
    return CATEGORIES

@st.cache_data
def get_transaction_types():
    """Cache the transaction types to prevent reloading"""
    return TRANSACTION_TYPES

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'messages': [],
        'save_clicked': False,
        'current_amount': None,
        'current_type': None,
        'current_category': None,
        'current_subcategory': None,
        'form_submitted': False,
        'show_analytics': False,  # New state variable for analytics
        'current_transaction': None,  # New state variable for current transaction
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def parse_date_from_text(text):
    try:
        # Convert text to lowercase for easier matching
        text = text.lower()
        current_date = datetime.now()
        
        # Handle relative dates
        relative_dates = {
            'today': current_date,
            'yesterday': current_date - timedelta(days=1),
            'tomorrow': current_date + timedelta(days=1),
            'day before yesterday': current_date - timedelta(days=2),
            'day after tomorrow': current_date + timedelta(days=2)
        }
        
        # Check for relative date references
        for phrase, date in relative_dates.items():
            if phrase in text:
                return date
        
        # Handle "last X days/weeks/months" patterns
        last_pattern = r'last (\d+) (day|week|month)s?'
        match = re.search(last_pattern, text)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            if unit == 'day':
                return current_date - timedelta(days=number)
            elif unit == 'week':
                return current_date - timedelta(weeks=number)
            elif unit == 'month':
                # Approximate month as 30 days
                return current_date - timedelta(days=number * 30)
        
        # Handle "next X days/weeks/months" patterns
        next_pattern = r'next (\d+) (day|week|month)s?'
        match = re.search(next_pattern, text)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            if unit == 'day':
                return current_date + timedelta(days=number)
            elif unit == 'week':
                return current_date + timedelta(weeks=number)
            elif unit == 'month':
                # Approximate month as 30 days
                return current_date + timedelta(days=number * 30)
        
        # Try to find and parse explicit dates
        # First, look for common date patterns
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        match = re.search(date_pattern, text)
        if match:
            return parser.parse(match.group())
        
        # If no explicit date pattern, try general date parsing
        words = text.split()
        for i in range(len(words)-2):  # Look for 3-word combinations that might be dates
            possible_date = ' '.join(words[i:i+3])
            try:
                return parser.parse(possible_date)
            except Exception as e:
                log.error(f"❌ Failed to parse date from text: {str(e)}")
                continue
        
        # If no date is found, return current date
        return current_date
    
    except Exception as e:
        log.warning(f"Failed to parse date from text, using current date. Error: {str(e)}")
        return current_date

def test_sheet_access():
    try:
        # Test write access by appending to the last row instead of clearing
        test_values = [['TEST', 'TEST', 'TEST', 'TEST', 'TEST', 'TEST']]
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range='Expenses',
            valueInputOption='RAW',
            body={'values': test_values}
        ).execute()
        
        # Get the range that was just written
        updated_range = result['updates']['updatedRange']
        
        # Only clear the test row we just added
        service.spreadsheets().values().clear(
            spreadsheetId=SHEET_ID,
            range=updated_range,
            body={}
        ).execute()
        
        log.info("✅ Sheet access test successful")
        return True
    except Exception as e:
        log.error(f"❌ Sheet access test failed: {str(e)}")
        return False

def initialize_sheet():
    try:
        # Create sheets if they don't exist
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        existing_sheets = {s.get("properties", {}).get("title") for s in sheets}
        
        # Initialize Expenses sheet
        if 'Expenses' not in existing_sheets:
            log.info("Creating new Expenses sheet...")
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'Expenses'
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body=body
            ).execute()
            
            headers = [['Date', 'Amount', 'Type', 'Category', 'Subcategory', 'Description']]
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range='Expenses!A1:F1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
        
        # Initialize Pending sheet
        if 'Pending' not in existing_sheets:
            log.info("Creating new Pending sheet...")
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'Pending'
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body=body
            ).execute()
            
            headers = [['Date', 'Amount', 'Type', 'Category', 'Description', 'Due Date', 'Status']]
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range='Pending!A1:G1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
        
        # Test sheet access
        if not test_sheet_access():
            raise Exception("Failed to verify sheet access")
            
        log.info("✨ Sheets initialized and verified")
    except Exception as e:
        log.error(f"❌ Failed to initialize sheets: {str(e)}")
        raise

def add_transaction_to_sheet(date, amount, trans_type, category, subcategory, description):
    try:
        log.info(f"Starting transaction save: {date}, {amount}, {trans_type}, {category}, {subcategory}, {description}")
        
        # Format the date if it's a datetime object
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        
        # Ensure amount is a string
        amount = str(float(amount))
        
        # Prepare the values
        values = [[str(date), amount, trans_type, category, subcategory, description]]
        
        # Changed range to 'Expenses' to let Google Sheets determine the next empty row
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range='Expenses',  # Changed from 'Expenses!A2:F2' to just 'Expenses'
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        
        log.info(f"✅ Transaction saved successfully: {result}")
        return True
        
    except Exception as e:
        log.error(f"❌ Failed to save transaction: {str(e)}")
        return False

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_transactions_data():
    try:
        log.debug("Fetching transactions data from Google Sheets")
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Expenses!A1:F'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            log.warning("No transaction data found in sheet")
            return pd.DataFrame(columns=['Date', 'Amount', 'Type', 'Category', 'Subcategory', 'Description'])
        
        log.info(f"📈 Retrieved {len(values)-1} transaction records")
        return pd.DataFrame(values[1:], columns=['Date', 'Amount', 'Type', 'Category', 'Subcategory', 'Description'])
    except Exception as e:
        log.error(f"❌ Failed to fetch transactions data: {str(e)}")
        raise

def process_user_input(user_input):
    try:
        log.debug(f"Processing user input: {user_input}")
        chat = model.start_chat(history=[])
        
        # Create a more detailed prompt with category hints
        prompt = f"""
        Extract transaction information from this text: '{user_input}'
        
        If the text indicates a future receipt (e.g., "will receive", "getting", "coming", "pending", "next week", "tomorrow"), 
        classify it as a pending transaction with type "To Receive".
        
        If the text indicates a future payment (e.g., "need to pay", "will pay", "have to give", "due"), 
        classify it as a pending transaction with type "To Pay".
        
        For immediate transactions:
        - If it mentions receiving money now -> use 'Income' type
        - If it mentions spending money now -> use 'Expense' type
        
        Always convert relative dates to YYYY-MM-DD format:
        - "next week" -> date 7 days from today
        - "tomorrow" -> date 1 day from today
        - "next month" -> date 30 days from today
        
        Respond in this format only without any quotes:
        type: Income/Expense/To Receive/To Pay
        amount: <number>
        category: <category>
        description: <brief description>
        due_date: <YYYY-MM-DD format>
        """
        
        response = chat.send_message(prompt)
        
        response_text = response.text
        lines = response_text.strip().split('\n')
        extracted_info = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                extracted_info[key.strip()] = value.strip().replace('"', '').replace("'", "")
        
        # Set current date as transaction date
        current_date = datetime.now().strftime('%Y-%m-%d')
        extracted_info['date'] = current_date
        
        # Handle relative dates in due_date
        if extracted_info['type'] in ['To Receive', 'To Pay']:
            if 'due_date' not in extracted_info or not extracted_info['due_date'].strip():
                # Default to 7 days from now if no date provided
                due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                extracted_info['due_date'] = due_date
            else:
                try:
                    # Try to parse the date string
                    parsed_date = parser.parse(extracted_info['due_date'])
                    extracted_info['due_date'] = parsed_date.strftime('%Y-%m-%d')
                except:
                    # If parsing fails, default to 7 days
                    due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                    extracted_info['due_date'] = due_date
        
        log.info(f"🎯 Successfully extracted transaction info: {extracted_info}")
        return extracted_info
    except Exception as e:
        log.error(f"❌ Failed to process user input: {str(e)}")
        raise

def show_analytics():
    try:
        log.info("Generating financial analytics")
        df = get_transactions_data()
        
        if df.empty:
            st.info("No transactions recorded yet. Add some transactions to see analytics!")
            return
            
        df['Amount'] = pd.to_numeric(df['Amount'])
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Calculate totals
        total_income = df[df['Type'] == 'Income']['Amount'].sum()
        total_expenses = df[df['Type'] == 'Expense']['Amount'].sum()
        net_balance = total_income - total_expenses
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Income", f"Rs. {total_income:,.2f}", delta=None)
        with col2:
            st.metric("Total Expenses", f"Rs. {total_expenses:,.2f}", delta=None)
        with col3:
            st.metric("Net Balance", f"Rs. {net_balance:,.2f}", 
                     delta=f"Rs. {net_balance:,.2f}", 
                     delta_color="normal" if net_balance >= 0 else "inverse")
        
        if len(df) > 1:  # Only show charts if we have more than one transaction
            # Income vs Expenses over time
            df_grouped = df.groupby(['Date', 'Type'])['Amount'].sum().unstack(fill_value=0)
            fig_timeline = px.line(df_grouped, 
                                 title='Income vs Expenses Over Time',
                                 labels={'value': 'Amount (Rs. )', 'variable': 'Type'})
            st.plotly_chart(fig_timeline)
            
            # Category breakdown for both income and expenses
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Income Breakdown")
                income_df = df[df['Type'] == 'Income']
                if not income_df.empty:
                    fig_income = px.pie(income_df, values='Amount', names='Category', 
                                      title='Income by Category')
                    st.plotly_chart(fig_income)
                else:
                    st.info("No income transactions recorded yet.")
            
            with col2:
                st.subheader("Expense Breakdown")
                expense_df = df[df['Type'] == 'Expense']
                if not expense_df.empty:
                    fig_expense = px.pie(expense_df, values='Amount', names='Category', 
                                       title='Expenses by Category')
                    st.plotly_chart(fig_expense)
                else:
                    st.info("No expense transactions recorded yet.")
            
            # Monthly summary
            st.subheader("Monthly Summary")
            monthly_summary = df.groupby([df['Date'].dt.strftime('%Y-%m'), 'Type'])['Amount'].sum().unstack(fill_value=0)
            monthly_summary['Net'] = monthly_summary.get('Income', 0) - monthly_summary.get('Expense', 0)
            st.dataframe(monthly_summary.style.format("Rs. {:,.2f}"))
        
        log.info("📊 Analytics visualizations generated successfully")
    except Exception as e:
        log.error(f"❌ Failed to generate analytics: {str(e)}")
        st.error("Failed to generate analytics. Please try again later.")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_sheet_url():
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"

@st.cache_resource  # Cache for the entire session
def initialize_gemini():
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    return genai.GenerativeModel('gemini-pro')

@st.cache_data
def get_subcategories(trans_type, category):
    return CATEGORIES[trans_type][category]

def on_save_click():
    st.session_state.save_clicked = True

def verify_sheet_setup():
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range='Expenses!A1:F1'
        ).execute()
        
        values = result.get('values', [])
        expected_headers = ['Date', 'Amount', 'Type', 'Category', 'Subcategory', 'Description']
        
        if not values or values[0] != expected_headers:
            # Reinitialize headers
            headers = [expected_headers]
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range='Expenses!A1:F1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            log.info("Headers reinitialized")
            
        return True
    except Exception as e:
        log.error(f"Failed to verify sheet setup: {str(e)}")
        return False

def show_success_message(transaction_date, subcategory):
    """Display success message after transaction is saved"""
    emoji = "💰" if st.session_state.current_transaction['type'] == "Income" else "💸"
    confirmation_message = (
        f"{emoji} Transaction recorded:\n\n"
        f"Date: {transaction_date}\n"
        f"Amount: Rs. {float(st.session_state.current_transaction['amount']):,.2f}\n"
        f"Type: {st.session_state.current_transaction['type']}\n"
        f"Category: {st.session_state.current_transaction['category']}\n"
        f"Subcategory: {subcategory}"
    )
    st.success(confirmation_message)
    st.session_state.messages.append({"role": "assistant", "content": confirmation_message})
    log.info("✅ Transaction saved and analytics updated")

def show_transaction_form():
    """Separate function to handle transaction form display and processing"""
    extracted_info = st.session_state.current_transaction
    
    if 'amount' in extracted_info and 'type' in extracted_info:
        # Create form container
        form_container = st.container()
        
        with form_container:
            # Initialize form state
            if 'form_submitted' not in st.session_state:
                st.session_state.form_submitted = False
            
            with st.form(key="transaction_form"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if extracted_info['type'] in ['To Receive', 'To Pay']:
                        # For pending transactions
                        try:
                            # Try to parse the due date if it exists
                            if 'due_date' in extracted_info and extracted_info['due_date']:
                                default_due_date = datetime.strptime(extracted_info['due_date'], '%Y-%m-%d')
                            else:
                                # Default to 7 days from now
                                default_due_date = datetime.now() + timedelta(days=7)
                        except ValueError:
                            # If parsing fails, use 7 days from now
                            default_due_date = datetime.now() + timedelta(days=7)
                        
                        due_date = st.date_input(
                            "Due date",
                            value=default_due_date,
                            key="due_date"
                        )
                    else:
                        # For regular transactions
                        categories = get_categories()
                        subcategories = categories[extracted_info['type']][extracted_info['category']]
                        subcategory = st.selectbox(
                            "Select subcategory",
                            subcategories,
                            key="subcategory_select"
                        )
                    
                    default_date = datetime.strptime(extracted_info['date'], '%Y-%m-%d')
                    transaction_date = st.date_input(
                        "Transaction date",
                        value=default_date,
                        key="transaction_date"
                    )
                
                with col2:
                    submitted = st.form_submit_button(
                        "Save",
                        type="primary",
                        use_container_width=True,
                        on_click=lambda: setattr(st.session_state, 'form_submitted', True)
                    )

            if st.session_state.form_submitted:
                try:
                    if extracted_info['type'] in ['To Receive', 'To Pay']:
                        success = add_pending_transaction_to_sheet(
                            transaction_date,
                            extracted_info['amount'],
                            extracted_info['type'],
                            extracted_info['category'],
                            extracted_info.get('description', ''),
                            due_date
                        )
                    else:
                        success = add_transaction_to_sheet(
                            transaction_date,
                            extracted_info['amount'],
                            extracted_info['type'],
                            extracted_info['category'],
                            subcategory,
                            extracted_info.get('description', '')
                        )
                    
                    if success:
                        show_success_message(transaction_date, subcategory if 'subcategory' in locals() else None)
                        st.session_state.current_transaction = None
                        st.session_state.form_submitted = False
                        st.rerun()
                    else:
                        st.error("Failed to save transaction. Please try again.")
                        st.session_state.form_submitted = False
                except Exception as e:
                    log.error(f"Failed to save transaction: {str(e)}")
                    st.error("An error occurred while saving the transaction. Please try again.")
                    st.session_state.form_submitted = False

def add_pending_transaction_to_sheet(date, amount, trans_type, category, description, due_date):
    try:
        # Verify sheets exist before adding transaction
        if not verify_sheets_setup():
            raise Exception("Failed to verify sheets setup")
            
        log.info(f"Starting pending transaction save: {date}, {amount}, {trans_type}, {category}, {description}, {due_date}")
        
        # Format the dates if they're datetime objects
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        if isinstance(due_date, datetime):
            due_date = due_date.strftime('%Y-%m-%d')
        
        # Ensure amount is a string
        amount = str(float(amount))
        
        # Prepare the values with initial status as 'Pending'
        values = [[str(date), amount, trans_type, category, description, str(due_date), 'Pending']]
        
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range='Pending!A1:G1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        
        log.info(f"✅ Pending transaction saved successfully: {result}")
        return True
        
    except Exception as e:
        log.error(f"❌ Failed to save pending transaction: {str(e)}")
        return False

def verify_sheets_setup():
    """Verify both Expenses and Pending sheets exist with correct headers"""
    try:
        # Get all sheets
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        existing_sheets = {s.get("properties", {}).get("title") for s in sheets}
        
        # Check and initialize Expenses sheet
        if 'Expenses' not in existing_sheets:
            log.info("Creating new Expenses sheet...")
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'Expenses'
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body=body
            ).execute()
            
            headers = [['Date', 'Amount', 'Type', 'Category', 'Subcategory', 'Description']]
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range='Expenses!A1:F1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
        
        # Check and initialize Pending sheet
        if 'Pending' not in existing_sheets:
            log.info("Creating new Pending sheet...")
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': 'Pending'
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body=body
            ).execute()
            
            headers = [['Date', 'Amount', 'Type', 'Category', 'Description', 'Due Date', 'Status']]
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range='Pending!A1:G1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()
            
        log.info("✨ Sheets verified and initialized")
        return True
    except Exception as e:
        log.error(f"❌ Failed to verify/initialize sheets: {str(e)}")
        return False

def main():
    try:
        log.info("🚀 Starting Finance Tracker application")
        
        # Initialize session state
        if 'sheets_verified' not in st.session_state:
            st.session_state.sheets_verified = False
        
        # Only verify sheets once
        if not st.session_state.sheets_verified:
            verify_sheets_setup()
            st.session_state.sheets_verified = True
        
        st.title("💰 Smart Finance Tracker")
        st.markdown(f"📊 [View Google Sheet]({get_sheet_url()})")
        st.divider()
        
        init_session_state()
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Handle chat input
        if prompt := st.chat_input("Tell me about your income or expense..."):
            log.debug(f"Received user input: {prompt}")
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process user input only if we don't have a current transaction
            if not st.session_state.current_transaction:
                extracted_info = process_user_input(prompt)
                st.session_state.current_transaction = extracted_info
                st.rerun()
            
        # Show transaction form if we have extracted info
        if st.session_state.current_transaction:
            show_transaction_form()
    
    except Exception as e:
        log.error(f"❌ Application error: {str(e)}", exc_info=True)
        st.error("An unexpected error occurred. Please try again later.")

if __name__ == "__main__":
    main()