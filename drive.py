import config
import logging

from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

def upload(service, image, image_name):
    try:
        file_metadata = {
            'name': image_name,
            'parents': [config.DRIVE_FOLDER_ID]
        }

        media = MediaIoBaseUpload(image, mimetype='image/jpeg', resumable=True)
        
        logger.info(f"uploading {image_name} to Google Drive folder...")
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()

        file_id = file.get('id')
        file_link = file.get('webViewLink')

        logger.info("image upload successful")
        logger.info(f"file id: {file_id}")
        logger.info(f"link: {file_link}")
        
        return file_link

    except Exception as e:
        logger.error(f"An error occurred: {e}")
