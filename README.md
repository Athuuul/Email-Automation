# AI-Powered Email Data Assistant

This project is an AI-driven email automation system that reads unread emails with CSV or Excel attachments, interprets user instructions in the email body using Google's Gemini LLM, generates Python code to process the attached dataset, executes it safely, and replies with the processed file.

---

## Features

- Connects securely to a Gmail inbox using IMAP and SMTP
- Supports CSV and Excel file attachments
- Uses Gemini 1.5 Flash LLM to understand natural language instructions and generate Pandas-based Python code
- Executes the code safely in a restricted environment
- Sends back the processed dataset to the original sender

---

## Requirements

- Python 3.8 or higher
- Gmail account with App Password enabled
- Gemini API Key (Google Generative AI)
- `.env` file configured with necessary credentials

---

## Environment Variables

Create a `.env` file in the project root directory and add the following:

```env
GMAIL_USER=your-email@gmail.com
APP_PASSWORD=your-app-password
GEMINI_API_KEY=your-gemini-api-key
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
