import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DOCUMENT_ID = os.getenv('DOCUMENT_ID')
CREDENTIALS_FILE = 'credentials.json'
SHEET_ID = os.getenv('SHEET_ID')
DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')
CREDENTIALSJSON = os.getenv('CREDENTIALSJSON')
