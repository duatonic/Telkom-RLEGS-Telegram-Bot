import os.path
import pickle
import config
import logging

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

HEADER_DATA = [
    ["Kode SA", "Nama Lengkap", "Nomor HP SA", "Witel", "Telkom Daerah", "Tanggal Visit", "Kategori Pelanggan", "Nama Tenant / Desa / Puskesmas / Kecamatan yang divisit", "Kegiatan", "Layanan Saat Ini", "Tarif Layanan Saat Ini", "Nama PIC Pelanggan", "Jabatan PIC", "Nomor HP PIC Pelanggan", "Jika Dealing, Paket Berapa Mbps", "Dealing Layanan Bundling", "Foto Evidence Visit"]
]

def append_data(service, new_data: list):
    try:
        if not isinstance(new_data, list):
            raise TypeError("Data passed must be of 'list' type")

        range_to_check = 'Sheet1!A:A'
        result = service.spreadsheets().values().get(
            spreadsheetId=config.SHEET_ID,
            range=range_to_check
        ).execute()

        existing_rows = len(result.get('values', []))
        data_to_append = []
        
        if existing_rows == 0:
            logger.info('sheet is empty, adding header')
            data_to_append = HEADER_DATA + new_data
            target_range = 'Sheet1!A1'
        else:
            data_to_append = new_data
            start_row = existing_rows + 1
            target_range = f'Sheet1!A{start_row}'

        body = {
            'values': data_to_append
        }

        append_result = service.spreadsheets().values().update(
            spreadsheetId=config.SHEET_ID,
            range=target_range,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Foramt header
        if existing_rows == 0:
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1
                    },
                    'cell': { 'userEnteredFormat': { 'textFormat': { 'bold': True }}},
                    'fields': 'userEnteredFormat(textFormat)'
                }
            }]
            body = {'requests': requests}
            service.spreadsheets().batchUpdate(
                spreadsheetId=config.SHEET_ID,
                body=body
            ).execute()
            logger.info("Header formatted.")

        success_message = f"Successfully appended new data."
        logger.info(success_message)
        return True, success_message

    except Exception as e:
        error_msg = f"Error menyimpan data: {e}"
        logger.error(error_msg)
        return False, error_msg
