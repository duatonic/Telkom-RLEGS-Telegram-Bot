import os.path
import pickle
import logging
import config

import drive
import spreadsheet

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleService:
    def __init__(self):
        self.sheet_service = None
        self.drive_service = None
        self.creds = None
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

    def authenticate(self):
        try:
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.CREDENTIALSJSON, self.scopes
                    )
                    self.creds = flow.run_local_server(port=0)

                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)

        except Exception as e:
            logger.error(f"An Error occurred: {e}")

    def build_services(self):
        try:
            self.sheet_service = build('sheets', 'v4', credentials=self.creds)
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            logger.info("Connected to Sheet and Drive services")    

        except Exception as e:
            logger.error(f"An Error occurred: {e}")

    def append_to_sheet(self, new_data: list):
        status, msg = spreadsheet.append_data(self.sheet_service, new_data)
        if status:
            logger.info(f"append to sheet success: {msg}")
        else:
            logger.error(msg)

        return msg

    def upload_to_drive(self, image, image_name):
        try:
            return drive.upload(self.drive_service, image, image_name)

        except Exception as e:
            logger.error(f"An Error occurred: {e}")
