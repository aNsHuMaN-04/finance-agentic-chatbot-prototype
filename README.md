# 💰 Smart Finance Tracker

A modern, AI-powered expense tracking application built with Streamlit that helps you manage your personal finances through natural language input and intelligent categorization.

## ✨ Features

- 🤖 Natural Language Processing for expense/income entry
- 📊 Real-time analytics and visualization
- 💬 Chat-like interface for easy data entry
- 📅 Automatic date detection
- 🗂️ Smart categorization of transactions
- 📈 Google Sheets integration for data storage
- 📱 Responsive design for both desktop and mobile

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google account with Google Sheets API enabled
- Google Cloud credentials (service account key)

### Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd expense_tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Sheets API:
- Create a project in Google Cloud Console
- Enable Google Sheets API
- Create a service account and download the credentials JSON file
- Rename the credentials file to `credentials.json` and place it in the project root

4. Configure environment variables:
Create a `.env` file in the project root with:
```
SHEET_ID=your_google_sheet_id
OPENAI_API_KEY=your_openai_api_key
```

### Running the Application

```bash
streamlit run app.py
```

## 📝 Usage

1. **Adding Transactions**
   - Type natural language commands like:
     - "Spent $50 on groceries yesterday"
     - "Earned $1000 from salary today"
     - "Paid $20 for lunch on Monday"

2. **Viewing Analytics**
   - Click the "Show Analytics" button in the sidebar
   - View spending patterns, category-wise breakdowns, and trends

3. **Managing Categories**
   - Transactions are automatically categorized
   - Select appropriate subcategories from the dropdown

## 🔧 Configuration

### Google Sheet Structure

The application expects the following columns in your Google Sheet:

- Date
- Amount
- Type (Income/Expense)
- Category
- Subcategory
- Description

### Categories

Default categories include:

**Income:**
- Salary
- Investments
- Business
- Other Income

**Expenses:**
- Food & Dining
- Shopping
- Transportation
- Bills & Utilities
- Entertainment
- Health & Wellness
- Other Expenses

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by OpenAI's GPT models
- Uses Google Sheets API for data storage

## 💡 Support

For support, please open an issue in the GitHub repository or contact the maintainers.
