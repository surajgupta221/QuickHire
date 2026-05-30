import gspread
from google.oauth2.service_account import Credentials
import os
import json
from datetime import datetime


def get_sheets_client():
    try:
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not set", flush=True)
            return None
        creds_dict = json.loads(service_account_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"❌ Sheets auth failed: {e}", flush=True)
        return None


def get_sheet():
    """Get the main sheet"""
    client = get_sheets_client()
    if not client:
        return None
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheet_id:
        print("⚠️ GOOGLE_SHEETS_ID not set", flush=True)
        return None
    try:
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        print(f"❌ Cannot open sheet: {e}", flush=True)
        return None


def ensure_headers(sheet):
    """Make sure headers exist in row 1"""
    try:
        first_row = sheet.row_values(1)
        if not first_row or first_row[0] != "Signup Date":
            sheet.insert_row([
                "Signup Date", "Full Name", "Email", "Phone",
                "Company", "Plan", "Credits Left",
                "Total Screenings", "Last Activity", "Status"
            ], 1)
    except Exception as e:
        print(f"Headers check failed: {e}", flush=True)


def add_user_to_sheet(user_data: dict):
    """Add new signup to Google Sheet"""
    try:
        sheet = get_sheet()
        if not sheet:
            return False

        ensure_headers(sheet)

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            user_data.get("full_name", ""),
            user_data.get("email", ""),
            user_data.get("phone", ""),
            user_data.get("company_name", ""),
            user_data.get("plan", "free"),
            user_data.get("screening_credits", 10),
            0,  # Total Screenings
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Active"
        ]

        sheet.append_row(row)
        print(f"✅ User added to sheet: {user_data.get('email')}", flush=True)
        return True

    except Exception as e:
        print(f"❌ Sheet add failed: {e}", flush=True)
        return False


def update_user_in_sheet(email: str, credits: int,
                          plan: str = None,
                          increment_screenings: bool = False):
    """Update user credits and screening count in sheet"""
    try:
        sheet = get_sheet()
        if not sheet:
            return False

        # Find user row by email
        try:
            cell = sheet.find(email)
        except Exception:
            print(f"⚠️ User {email} not found in sheet", flush=True)
            return False

        row = cell.row

        # Update credits (column 7)
        sheet.update_cell(row, 7, credits)

        # Update last activity (column 9)
        sheet.update_cell(row, 9, datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Update plan if changed (column 6)
        if plan:
            sheet.update_cell(row, 6, plan)

        # Increment total screenings (column 8)
        if increment_screenings:
            try:
                current = sheet.cell(row, 8).value
                current_count = int(current) if current else 0
                sheet.update_cell(row, 8, current_count + 1)
            except Exception:
                pass

        print(f"✅ Sheet updated for {email}: {credits} credits", flush=True)
        return True

    except Exception as e:
        print(f"❌ Sheet update failed: {e}", flush=True)
        return False