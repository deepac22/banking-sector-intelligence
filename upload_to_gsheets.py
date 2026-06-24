import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os

def upload_csv_to_gsheets(csv_file_path, spreadsheet_id, sheet_name):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('google_creds.json', scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(spreadsheet_id)
    
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

    df = pd.read_csv(csv_file_path)
    df = df.replace({float('nan'): None})
    data = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.update(range_name='A1', values=data)
    print(f"Uploaded {len(df)} rows to sheet '{sheet_name}'.")

if __name__ == "__main__":
    SPREADSHEET_ID = "1Sm1-Bl64G26hnFHHMfL14I_NTd6JXDuUBs_HZFmF2G0"
    
    upload_csv_to_gsheets('bank_metrics.csv', SPREADSHEET_ID, 'Bank Metrics')
    upload_csv_to_gsheets('bank_prices_long.csv', SPREADSHEET_ID, 'Bank Prices')
    
    print("All data uploaded to Google Sheets successfully.")