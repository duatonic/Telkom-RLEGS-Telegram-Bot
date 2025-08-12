import logging
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import config

logger = logging.getLogger(__name__)

class SimpleGoogleDocs:
    def __init__(self):
        self.service = None
        self.setup_service()
    
    def setup_service(self):
        """Setup Google Docs API service"""
        try:
            scope = ['https://www.googleapis.com/auth/documents']
            
            creds = Credentials.from_service_account_file(
                config.CREDENTIALS_FILE, 
                scopes=scope
            )
            
            self.service = build('docs', 'v1', credentials=creds)
            logger.info("✅ Google Docs API terhubung")
            
        except Exception as e:
            logger.error(f"❌ Error Google Docs API: {e}")
            self.service = None
    
    def add_data(self, nama, no_telp, alamat):
        """Tambahkan data ke Google Docs"""
        try:
            if not self.service:
                return False, "Service tidak tersedia"
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format data sebagai baris tabel
            data_row = f"\n{nama} | {no_telp} | {alamat} | {timestamp}"
            
            # Insert text ke akhir dokumen
            requests = [{
                'insertText': {
                    'endOfSegmentLocation': {
                        'segmentId': ''
                    },
                    'text': data_row
                }
            }]
            
            # Execute request
            result = self.service.documents().batchUpdate(
                documentId=config.DOCUMENT_ID,
                body={'requests': requests}
            ).execute()
            
            logger.info(f"✅ Data berhasil ditambahkan: {nama}")
            return True, "Data berhasil disimpan"
            
        except Exception as e:
            error_msg = f"Error menyimpan data: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def init_document(self):
        """Inisialisasi dokumen dengan header jika diperlukan"""
        try:
            if not self.service:
                return False
            
            # Cek apakah dokumen sudah memiliki header
            document = self.service.documents().get(documentId=config.DOCUMENT_ID).execute()
            content = document.get('body', {}).get('content', [])
            
            # Jika dokumen kosong atau tidak ada header, tambahkan
            has_header = False
            for element in content:
                if 'paragraph' in element:
                    text = element['paragraph'].get('elements', [{}])[0].get('textRun', {}).get('content', '')
                    if 'Nama |' in text or 'DATA REKAP' in text:
                        has_header = True
                        break
            
            if not has_header:
                header = "\n=== DATA REKAP ===\nNama | No. Telepon | Alamat | Timestamp\n" + "-"*70
                
                requests = [{
                    'insertText': {
                        'endOfSegmentLocation': {
                            'segmentId': ''
                        },
                        'text': header
                    }
                }]
                
                self.service.documents().batchUpdate(
                    documentId=config.DOCUMENT_ID,
                    body={'requests': requests}
                ).execute()
                
                logger.info("✅ Header dokumen diinisialisasi")
            
            return True
            
        except Exception as e:
            logger.error(f"Error init document: {e}")
            return False