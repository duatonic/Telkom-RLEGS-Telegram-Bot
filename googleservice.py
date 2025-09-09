import os.path
import json
import logging
import config
import time

import drive
import spreadsheet

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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
            if not os.path.exists(config.OAUTH_FILE):
                logger.error("Auth not initialized. Expected 'google_oauth.json' to exist with client_id, client_secret, refresh_token. Please run the 'auth_bootstrap_desktop.py' script to generate the auth credentials.")

                raise RuntimeError(
                    "Auth not initialized. Expected 'google_oauth.json' to exist with client_id, client_secret, refresh_token."
                )

            with open(config.OAUTH_FILE, 'r') as token:
                blob = json.load(token)

            # get creds process
            missing = [k for k in ("client_id", "client_secret", "refresh_token") if not blob.get(k)]
            if missing:
                logger.error(f"Missing fields in {config.OAUTH_FILE}: {missing}")
                raise RuntimeError(f"Missing fields in {config.OAUTH_FILE}: {missing}")

            creds = Credentials(
                token=blob.get("access_token"),  # may be None
                refresh_token=blob["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=blob["client_id"],
                client_secret=blob["client_secret"],
                scopes=self.scopes,
            )

            if not creds.valid:
                req = Request()
                creds.refresh(req)
                blob["access_token"] = creds.token
                blob["scopes"] = self.scopes
                blob["saved_at"] = int(time.time())

                os.makedirs(os.path.dirname(config.OAUTH_FILE), exist_ok=True)
                with open(config.OAUTH_FILE, "w") as f:
                    json.dump(blob, f, indent=2)
                os.chmod(config.OAUTH_FILE, 0o600)

            logger.info('Google Service authentication successful')
            self.creds = creds

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

        return status, msg

    def upload_to_drive(self, image, image_name):
        try:
            return drive.upload(self.drive_service, image, image_name)

        except Exception as e:
            logger.error(f"An Error occurred: {e}")
