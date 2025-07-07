# 💸 Finance Agentic Chatbot Prototype

This repository contains a working prototype of a **Finance Agentic Chatbot** developed for submission to [Hackathon Name].  
The chatbot allows users to **conversationally manage expenses/income**, store transactions in **Google Sheets**, and view **interactive analytics** — all powered by **Gemini AI** and **Streamlit**.

---

## 🚀 Features

✅ Conversational interface to log expenses/income  
✅ Google Sheets integration for real-time data storage  
✅ Analytics dashboard with interactive Plotly charts  
✅ Configurable categories and transaction types  
✅ Gemini 1.5 Flash for natural language understanding  
✅ Caching for faster analytics & reduced API calls  

---

## ⚙️ Tech Stack

- **Frontend**: Streamlit  
- **Backend services**: Google Sheets API, Gemini AI API  
- **Visualization**: Plotly Express  
- **Language**: Python  

---

## 🛠 Setup Instructions

### 1️⃣ Clone this repository  
```bash
git clone https://github.com/your-username/finance-agentic-chatbot-prototype.git
cd finance-agentic-chatbot-prototype


python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate


pip install -r requirements.txt

GEMINI_API_KEY=your_gemini_api_key
GOOGLE_SHEETS_CRED_PATH=full_path_to_your_creds.json
GOOGLE_SHEET_ID=your_google_sheet_id




streamlit run Home.py


