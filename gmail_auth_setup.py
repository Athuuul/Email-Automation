from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    profile = service.users().getProfile(userId='me').execute()
    print(f"✅ Authenticated Gmail: {profile['emailAddress']}")

if __name__ == '__main__':
    main()
