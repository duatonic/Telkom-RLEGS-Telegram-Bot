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
        """Tambahkan data ke Google Docs (method lama untuk backward compatibility)"""
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
    
    def add_data_with_kode(self, kode_sa, nama, no_telp, alamat):
        """Tambahkan data dengan Kode SA ke Google Docs"""
        try:
            if not self.service:
                logger.error("❌ Google Docs service tidak tersedia")
                return False, "Service tidak tersedia"
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format dengan Kode SA di awal
            data_row = f"\n{kode_sa} | {nama} | {no_telp} | {alamat} | {timestamp}"
            
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
            
            logger.info(f"✅ Data berhasil ditambahkan: {kode_sa} - {nama}")
            return True, "Data berhasil disimpan"
            
        except Exception as e:
            error_msg = f"Error menyimpan data: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def init_document(self):
        """Inisialisasi dokumen dengan header yang include Kode SA"""
        try:
            if not self.service:
                logger.error("❌ Service tidak tersedia untuk init document")
                return False
            
            # Test koneksi dengan get document
            document = self.service.documents().get(documentId=config.DOCUMENT_ID).execute()
            logger.info("✅ Berhasil mengakses dokumen Google Docs")
            
            content = document.get('body', {}).get('content', [])
            
            # Cek apakah dokumen sudah memiliki header
            has_header = False
            for element in content:
                if 'paragraph' in element:
                    text_elements = element['paragraph'].get('elements', [])
                    for text_element in text_elements:
                        text_content = text_element.get('textRun', {}).get('content', '')
                        if 'Kode SA |' in text_content or 'DATA REKAP RLEGS' in text_content:
                            has_header = True
                            break
                    if has_header:
                        break
            
            if not has_header:
                header = "\n=== DATA REKAP RLEGS ===\nKode SA | Nama | No. Telepon | Alamat | Timestamp\n" + "-"*80
                
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
                
                logger.info("✅ Header dokumen RLEGS diinisialisasi")
            else:
                logger.info("✅ Header dokumen sudah ada")
            
            return True
            
        except Exception as e:
            error_msg = f"Error init document: {e}"
            logger.error(f"❌ {error_msg}")
            return False