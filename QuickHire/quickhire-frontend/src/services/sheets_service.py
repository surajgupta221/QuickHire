import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime

def get_sheets_client():
    """Get authenticated Google Sheets client"""
    try:
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            print("⚠️ Google Sheets not configured")
            return None

        creds_dict = json.loads(service_account_json)
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)

    except Exception as e:
        print(f"❌ Sheets auth failed: {e}", flush=True)
        return None


def add_user_to_sheet(user_data: dict):
    """Add new user signup to Google Sheet"""
    try:
        client = get_sheets_client()
        if not client:
            return False

        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        if not sheet_id:
            return False

        sheet = client.open_by_key(sheet_id).sheet1

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            user_data.get("full_name", ""),
            user_data.get("email", ""),
            user_data.get("phone", ""),
            user_data.get("company_name", ""),
            user_data.get("plan", "free"),
            user_data.get("screening_credits", 10),
            "Active"
        ]

        sheet.append_row(row)
        print(f"✅ User added to sheets: {user_data.get('email')}", flush=True)
        return True

    except Exception as e:
        print(f"❌ Sheets update failed: {e}", flush=True)
        return False


def update_user_credits_in_sheet(email: str, credits: int):
    """Update user credits in sheet"""
    try:
        client = get_sheets_client()
        if not client:
            return False

        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        sheet = client.open_by_key(sheet_id).sheet1

        # Find user row by email
        cell = sheet.find(email)
        if cell:
            # Update credits column (G = column 7)
            sheet.update_cell(cell.row, 7, credits)
            print(f"✅ Credits updated in sheet for {email}", flush=True)

        return True

    except Exception as e:
        print(f"❌ Sheet update failed: {e}", flush=True)
        return False