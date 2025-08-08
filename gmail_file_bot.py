
import imaplib
import smtplib
import email
from email.message import EmailMessage
import pandas as pd
import io
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv
import os


# === CONFIGURATION ===
load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER")
APP_PASSWORD = os.getenv("APP_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# === LLM SETUP ===
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GEMINI_API_KEY)

# === FETCH EMAILS ===
def fetch_unread_emails():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(GMAIL_USER, APP_PASSWORD)
    mail.select("inbox")

    typ, data = mail.search(None, '(UNSEEN)')
    mail_ids = data[0].split()

    emails = []
    for num in mail_ids[-5:]:
        typ, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        sender = email.utils.parseaddr(msg["From"])[1]
        subject = msg["Subject"]
        body = ""
        attachment_bytes = None
        filename = None

        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                body = part.get_payload(decode=True).decode()
            if part.get("Content-Disposition"):
                filename = part.get_filename()
                if filename:
                    filename = filename.lower()
                    attachment_bytes = part.get_payload(decode=True)

        if attachment_bytes:
            emails.append({
                "sender": sender,
                "subject": subject,
                "body": body,
                "filename": filename,
                "attachment_bytes": attachment_bytes
            })

    mail.logout()
    return emails

# === READ ATTACHMENT ===
def read_attachment(filename, attachment_bytes):
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(attachment_bytes))
        filetype = "csv"
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(attachment_bytes))
        filetype = "excel"
    else:
        raise ValueError(f"Unsupported file type: {filename}")
    return df, filetype

# === GET DYNAMIC PYTHON CODE ===
def get_generated_code(email_body, columns):
    prompt = f"""
You are a data assistant.
The dataset has columns: {columns}

You have access to:
- df: the pandas DataFrame
- send_email(df, to_emails): function that emails the DataFrame as CSV to to_emails

Write Python code to apply these instructions:
"{email_body}"

Rules:
- No imports.
- Only valid Python code (no markdown formatting).
- No file I/O (no open(), no save()).
- Do not use print statements.

Your code:
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    code = response.content.strip()

    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:-1])
    return code

# === EMAIL SENDER ===
def send_email(df, to_emails):
    for to in to_emails:
        msg = EmailMessage()
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg["Subject"] = "Processed DataFrame"
        msg.set_content("Attached is the processed file.")

        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)

        msg.add_attachment(output.read(),
                           maintype="application",
                           subtype="octet-stream",
                           filename="processed.csv")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, APP_PASSWORD)
            server.send_message(msg)

# === RUN GENERATED CODE SAFELY ===
def safe_execute(code, df):
    safe_env = {
        "__builtins__": {},  # no builtins
        "df": df,
        "send_email": send_email
    }
    try:
        exec(code, safe_env)
        df_result = safe_env.get("df", df)
        return df_result
    except Exception as e:
        print(f"⚠️ Error in generated code: {e}")
        return df

# === MAIN ===
def main():
    emails = fetch_unread_emails()
    for mail_data in emails:
        print(f"Processing email from {mail_data['sender']}...")

        try:
            df, filetype = read_attachment(mail_data["filename"], mail_data["attachment_bytes"])
            columns = df.columns.tolist()
            code = get_generated_code(mail_data["body"], columns)
            print("✅ Generated code:\n", code)

            df_processed = safe_execute(code, df)

            # Send to original sender if not already sent
            send_email(df_processed, [mail_data["sender"]])

            print(f"✅ Processed and replied to {mail_data['sender']}")
        except Exception as e:
            print(f"❌ Error processing email from {mail_data['sender']}: {e}")

if __name__ == "__main__":
    main()