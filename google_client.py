import gspread
from oauth2client.service_account import ServiceAccountCredentials

def google_sheet_data(sheet_name='Mediamirror Bot', worksheet=0):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open(sheet_name).get_worksheet(worksheet)
    rows = sheet.col_values(1)

    return [row for row in rows if row.strip()]

