from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import streamlit as st
from typing import List

@st.cache_resource
def get_sheets_service():
    """Cache Google Sheets service configuration"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_SHEETS_CREDENTIALS'), 
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        raise Exception(f"Failed to connect to Google Sheets: {str(e)}")

def add_transaction(service, sheet_id: str, values: List[List[str]], sheet_name: str) -> bool:
    """Add a transaction to specified sheet"""
    try:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=sheet_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        return True
    except Exception as e:
        raise Exception(f"Failed to add transaction: {str(e)}")