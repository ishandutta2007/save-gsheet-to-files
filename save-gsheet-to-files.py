import os
import re
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --- Configuration ---
# Path to the OAuth 2.0 Client ID JSON file you downloaded
CLIENT_SECRET_FILE = "client_secret_save-gsheet-to-files.json"
# This file will be created automatically after your first successful login
TOKEN_FILE = "token.json"

SPREADSHEET_ID = (
    "1TDcu2t7lhM2zWxuRyIsqX4ofrvrQ9QWk5lxJ2wK6ma8"  # Found in the Google Sheet URL
)
OUTPUT_DIR = "sheet_outputs"
DELIMITER = " "  # Defines how columns are separated in the text file

# We only need read-only access to spreadsheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def sanitize_filename(name: str) -> str:
    """Strips illegal characters to ensure cross-platform OS compatibility."""
    name = str(name).strip()
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def authenticate_google_sheets():
    """Handles OAuth 2.0 authentication and token caching."""
    creds = None

    # Load cached credentials if they exist
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, trigger the login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("No valid token found. Opening browser for OAuth login...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Cache the credentials for future executions
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return gspread.authorize(creds)


def main():
    # 1. Authenticate
    try:
        client = authenticate_google_sheets()
    except Exception as e:
        print(f"Authentication failed. Check your client_secret.json: {e}")
        return

    # 2. Access Data
    try:
        print(f"Connecting to Spreadsheet ID: {SPREADSHEET_ID}...")
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        rows = sheet.get_all_values()
    except gspread.exceptions.APIError as e:
        print(
            f"API Error. Ensure the account you log in with has access to the sheet: {e}"
        )
        return

    # 3. Setup output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Processing {len(rows)} rows...")

    # 4. Process Rows (Iterate starting from 1 if skipping a header row: rows[1:])
    for index, row in enumerate(rows):
        if index == 0:
            continue
        if len(row) >= 3:
            raw_filename = row[2]

            if not raw_filename:
                print(f"Row {index + 1} skipped: 3rd column is empty.")
                continue

            safe_filename = sanitize_filename(raw_filename)
            words = [w.capitalize() for w in re.split(r"[-_\s]+", safe_filename) if w]
            safe_filename = "-".join(words)
            file_path = os.path.join(OUTPUT_DIR, f"{safe_filename}.txt")
            file_ignore_path = os.path.join(OUTPUT_DIR, f"_{safe_filename}.txt")
            if os.path.exists(file_ignore_path):
                print("file_ignore_path exists:", file_ignore_path)
                continue
            github_name = f"$repo_name = 'Awesome_{safe_filename}'".replace("_", "-")
            github_desc = (
                f"$repo_desc = 'Top {safe_filename} 🌟 Star if you like it! 🌟'".replace("-", " ").replace("_", " ").strip()
            )

            # Concatenate all available columns in this specific row
            concatenated_data = DELIMITER.join(str(cell).strip() for cell in row)
            concatenated_data = (
                concatenated_data.replace("Awesome", "").replace("awesome", "").strip()
            )
            concatenated_data = f"I want to create a similar GitHub's readme.md(i.e. strictly in markdown file format) for {concatenated_data} and their equivalent open-source softwares"
            concatenated_data = f"{concatenated_data}. The format should be exactly same as you did this last time"
            concatenated_data = f"{concatenated_data}. Open-source softwares is what I'm primarily emphasizing on, so try to include as many open-sources as possible"
            concatenated_data = f"{concatenated_data}. But keep the 'SaaS/Hosted Platforms' section and 'Open-Source' Section separate. Remember, it must be in markdown format.\n"

            # Write out to text
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(github_name + "\n")
                    f.write(github_desc + "\n\n")
                    f.write(concatenated_data)
                print(f"Saved: {file_path}")
            except IOError as e:
                print(f"I/O Error writing {file_path}: {e}")
        else:
            print(
                f"Row {index + 1} skipped: Has {len(row)} columns (requires at least 3)."
            )


if __name__ == "__main__":
    main()
