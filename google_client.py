import gspread
import time
from rss_client import get_rss_news
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

def sync_rss_to_sheet(rss_url, sheet_name='Mediamirror Bot', worksheet = 0, limit=5):
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open(sheet_name)
    ws = sh.get_worksheet(worksheet)

    existing_urls = ws.col_values(1)

    articles = get_rss_news(rss_url, limit=limit)
    added = 0

    for a in articles:
        url = a['link']
        if url not in existing_urls:
            ws.append_row([url, "", ""])
            added += 1

def get_next_unpublished(sheet_name='Mediamirror Bot', worksheet = 0):
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open(sheet_name)
    ws = sh.get_worksheet(worksheet)

    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        url, status = row[0], row[1] if len(row) > 1 else ""
        if url.startswith('http') and status.strip().lower() != 'publicado':
            return i, url, ws
    return None, None, ws



def get_unpublished_urls(sheet_name='Mediamirror Bot', worksheet = 0):
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open(sheet_name)
    ws = sh.get_worksheet(worksheet)

    rows = ws.get_all_values()
    urls = []
    for i, row in enumerate(rows[1:], start = 2):
        url, status = row[0], row[1] if len(row) > 1 else ""
        if url.startswith('http') and status.strip().lower() != 'publicado':
            urls.append((i, url))
    return urls, ws

def mark_as_published(ws, row):
    ws.update_cell(row, 2, 'Publicado')
    ws.update_cell(row, 3, time.strftime("%Y-%m-%d %H:%M"))  # Fecha
    return 'Google sheets actualizado'
