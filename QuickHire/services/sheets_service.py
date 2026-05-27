import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime


def get_sheets_client():
    try:
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not set")
            return None

        creds_dict = json.loads(service_account_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client

    except Exception as e:
        print(f"❌ Sheets auth failed: {e}", flush=True)
        return None


def add_user_to_sheet(user_data: dict):
    """Add new signup to Google Sheet"""
    try:
        client = get_sheets_client()
        if not client:
            return False

        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        if not sheet_id:
            print("⚠️ GOOGLE_SHEETS_ID not set")
            return False

        sheet = client.open_by_key(sheet_id).sheet1

        # Check if headers exist, add if not
        try:
            first_row = sheet.row_values(1)
            if not first_row:
                sheet.append_row([
                    "Signup", "Date", "Full Name", "Email", "Phone",
                    "Company", "Plan", "Credits Left", "Status"
                ])
        except Exception:
            pass

        row = [
            "New Signup",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            user_data.get("full_name", ""),
            user_data.get("email", ""),
            user_data.get("phone", ""),
            user_data.get("company_name", ""),
            user_data.get("plan", "free"),
            user_data.get("screening_credits", 3),
            "Active"
        ]

        sheet.append_row(row)
        print(f"✅ User added to sheet: {user_data.get('email')}", flush=True)
        return True

    except Exception as e:
        print(f"❌ Sheet add failed: {e}", flush=True)
        return False


def update_user_credits_in_sheet(email: str, credits: int, plan: str = None):
    """Update user credits after payment or usage"""
    try:
        client = get_sheets_client()
        if not client:
            return False

        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        sheet = client.open_by_key(sheet_id).sheet1

        cell = sheet.find(email)
        if cell:
            sheet.update_cell(cell.row, 7, credits)
            if plan:
                sheet.update_cell(cell.row, 6, plan)
            print(f"✅ Sheet updated for {email}: {credits} credits", flush=True)

        return True

    except Exception as e:
        print(f"❌ Sheet update failed: {e}", flush=True)
        return False