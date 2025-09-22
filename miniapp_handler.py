import json
import logging
import base64
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from validators import DataValidator
from googleservice import GoogleService
from enum import Enum

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """Simplified states for mini app flow"""
    IDLE = "idle"
    PROCESSING_DATA = "processing_data"
    COMPLETED = "completed"

class UserSession:
    """Simplified session class for mini app"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = ConversationState.IDLE
        self.last_message_id = None
        
    def set_state(self, new_state):
        """Update conversation state"""
        self.state = new_state
        
    def reset(self):
        """Reset session to initial state"""
        self.state = ConversationState.IDLE
        self.last_message_id = None

class MiniAppHandler:
    def __init__(self):
        self.validator = DataValidator()
        self.google_service = GoogleService()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - show mini app button"""
        user = update.effective_user
        user_name = user.first_name if user.first_name else "User"
        
        # Initialize Google services
        self.google_service.authenticate()
        self.google_service.build_services()
        
        welcome_message = f"""
👋 Halo *{user_name}*!

Selamat datang di *Rekapitulasi Data 8 Fishing Spot RLEGS III*

📍 _Pendataan Visit Kawasan Industri, Desa, dan Puskesmas_
"""
        
        # Create mini app button
        keyboard = [
            [InlineKeyboardButton(
                "📝 Mulai Input Data", 
                web_app=WebAppInfo(url="https://miniapp-rlegs.netlify.app/")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"Started mini app for user {user.id} ({user_name})")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **Bot Rekap Data - Bantuan**

**Perintah tersedia:**
• `/start` - Memulai bot dan membuka form
• `/help` - Menampilkan bantuan ini

**Cara penggunaan:**
1. Ketik `/start` atau klik tombol "Buka Form Data"
2. Isi semua field yang diperlukan di form
3. Upload foto evidence
4. Submit data

**Jenis data yang dapat diinput:**
• **Visit** - Data kunjungan pelanggan
• **Dealing** - Data penawaran/deal

**Field yang perlu diisi:**
- Kode SA, Nama, No. HP
- Witel, Telkom Daerah, Tanggal
- Kategori Pelanggan, Nama Tenant
- Data PIC Pelanggan
- Foto Evidence

**Dukungan:**
Jika mengalami masalah, hubungi administrator.
        """
        
        keyboard = [
            [InlineKeyboardButton(
                "📝 Buka Form Data", 
                web_app=WebAppInfo(url="https://miniapp-rlegs.netlify.app/")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def handle_back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to menu button callback"""
        query = update.callback_query
        await query.answer()
        
        user_name = query.from_user.first_name if query.from_user.first_name else "User"
        
        message = f"""
🎯 **Halo lagi, {user_name}!**

📋 **Bot Rekap Data Visit & Dealing**

Silakan gunakan form untuk input data baru:
        """
        
        keyboard = [
            [InlineKeyboardButton(
                "📝 Buka Form Data", 
                web_app=WebAppInfo(url="https://miniapp-rlegs.netlify.app/")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def handle_unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        message = """
❓ **Perintah tidak dikenali**

Gunakan perintah berikut:
• `/start` - Memulai bot
• `/help` - Bantuan

Atau klik tombol di bawah untuk membuka form:
        """
        
        keyboard = [
            [InlineKeyboardButton(
                "📝 Mulai Input Data", 
                web_app=WebAppInfo(url="https://miniapp-rlegs.netlify.app/")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    async def process_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process data received from Mini App"""
        try:
            # Parse JSON data from web app
            webapp_data = json.loads(update.message.web_app_data.data)
            user_id = update.effective_user.id
            user_name = update.effective_user.first_name
            
            logger.info(f"Received web app data from user {user_id}: {webapp_data.keys()}")
            
            # Send processing message
            status_msg = await update.message.reply_text("⏳ **Memproses data dari form...**", parse_mode='Markdown')
            
            # Validate all data
            validation_result = await self._validate_form_data(webapp_data)
            
            if not validation_result['is_valid']:
                # Return validation errors
                keyboard = [
                    [InlineKeyboardButton(
                        "📝 Perbaiki Data di Form", 
                        web_app=WebAppInfo(url="https://miniapp-rlegs.netlify.app/")
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await status_msg.edit_text(
                    f"❌ **Validasi Gagal**\n\n{validation_result['message']}\n\n"
                    "Silakan perbaiki data di form dan submit ulang.",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            # Process and save data
            await self._save_data_to_sheets(webapp_data, status_msg, user_id)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await update.message.reply_text(
                "❌ **Error:** Format data tidak valid dari form."
            )
        except Exception as e:
            logger.error(f"Error processing webapp data: {e}")
            await update.message.reply_text(
                "❌ **Error sistem:** Gagal memproses data dari form.\n"
                "Silakan coba lagi."
            )
    
    async def _validate_form_data(self, data):
        """Validate all form data"""
        errors = []
        
        # Validate common fields
        if not self.validator.validate_kode_sa(data.get('kode_sa', ''))[0]:
            errors.append("Kode SA tidak valid")
            
        if not self.validator.validate_nama(data.get('nama', ''))[0]:
            errors.append("Nama tidak valid")
            
        if not self.validator.validate_telepon(data.get('no_telp', ''))[0]:
            errors.append("No. Telepon tidak valid")
            
        if not data.get('witel'):
            errors.append("Witel harus dipilih")
            
        if not self.validator.validate_telda(data.get('telda', ''))[0]:
            errors.append("Telkom Daerah tidak valid")
            
        if not self.validator.validate_tanggal(data.get('tanggal', ''))[0]:
            errors.append("Tanggal tidak valid")
            
        if not data.get('kategori'):
            errors.append("Kategori pelanggan harus dipilih")
            
        if not self.validator.validate_tenant(data.get('tenant', ''))[0]:
            errors.append("Nama tenant tidak valid")
            
        if not data.get('kegiatan'):
            errors.append("Kegiatan harus dipilih")
        
        # Validate activity-specific fields
        kegiatan = data.get('kegiatan')
        
        if kegiatan == 'Visit':
            if not data.get('layanan'):
                errors.append("Layanan harus dipilih untuk Visit")
            if not data.get('tarif'):
                errors.append("Tarif harus dipilih untuk Visit")
        elif kegiatan == 'Dealing':
            if not data.get('paket_deal'):
                errors.append("Paket deal harus dipilih untuk Dealing")
            if not data.get('deal_bundling'):
                errors.append("Deal bundling harus dipilih untuk Dealing")
        
        # Validate PIC fields
        if not self.validator.validate_nama_pic(data.get('nama_pic', ''))[0]:
            errors.append("Nama PIC tidak valid")
            
        if not self.validator.validate_nama_pic(data.get('jabatan_pic', ''))[0]:
            errors.append("Jabatan PIC tidak valid")
            
        if not self.validator.validate_telepon_pic(data.get('telepon_pic', ''))[0]:
            errors.append("Telepon PIC tidak valid")
        
        # Validate photo
        if not data.get('foto_evidence'):
            errors.append("Foto evidence harus diupload")
        
        if errors:
            return {
                'is_valid': False,
                'message': "\n• ".join([""] + errors)
            }
        
        return {'is_valid': True, 'message': 'All data valid'}
    
    async def _save_data_to_sheets(self, data, status_msg, user_id):
        """Save validated data to Google Sheets"""
        try:
            # Initialize Google services
            self.google_service.authenticate()
            self.google_service.build_services()
            
            await status_msg.edit_text("⏳ **Memproses foto...**", parse_mode='Markdown')
            
            # Process photo
            foto_evidence_b64 = data.get('foto_evidence')
            if foto_evidence_b64.startswith('data:image'):
                # Remove data URL prefix
                foto_evidence_b64 = foto_evidence_b64.split(',')[1]
            
            image_bytes = base64.b64decode(foto_evidence_b64)
            image_file = BytesIO(image_bytes)
            image_file.seek(0)

            # Generate filename
            kode_sa_string = data.get('kode_sa', 'unknown').replace('/', '_')
            tanggal_string = data.get('tanggal', 'nodate').replace('/', '_')
            kegiatan_string = data.get('kegiatan', 'data')
            image_file_name = f"{kode_sa_string}_{tanggal_string}_{kegiatan_string}.jpg"

            await status_msg.edit_text("⏳ **Mengupload foto ke Google Drive...**", parse_mode='Markdown')

            # Upload to Drive
            image_link = self.google_service.upload_to_drive(image_file, image_file_name)
            
            await status_msg.edit_text("⏳ **Menyimpan ke Google Sheet...**", parse_mode='Markdown')
            
            # Prepare data for sheets
            kegiatan = data.get('kegiatan')
            
            # Set default values based on activity type
            if kegiatan == 'Visit':
                data['paket_deal'] = data.get('paket_deal', '-')
                data['deal_bundling'] = data.get('deal_bundling', '-')
            else:  # Dealing
                data['layanan'] = data.get('layanan', '-')
                data['tarif'] = data.get('tarif', '-')

            # Standard order for all data: 17 fields total
            ordered_data = [
                data.get('kode_sa', '-'),      # 1
                data.get('nama', '-'),         # 2
                data.get('no_telp', '-'),      # 3
                data.get('witel', '-'),        # 4
                data.get('telda', '-'),        # 5
                data.get('tanggal', '-'),      # 6
                data.get('kategori', '-'),     # 7
                data.get('tenant', '-'),       # 8
                data.get('kegiatan', '-'),     # 9
                data.get('layanan', '-'),      # 10
                data.get('tarif', '-'),        # 11
                data.get('nama_pic', '-'),     # 12
                data.get('jabatan_pic', '-'),  # 13
                data.get('telepon_pic', '-'),  # 14
                data.get('paket_deal', '-'),   # 15
                data.get('deal_bundling', '-'), # 16
                image_link,                    # 17
            ]

            logger.info(f"Data to submit: {ordered_data}")

            # Save to sheets
            success, message = self.google_service.append_to_sheet([ordered_data])
            
            if success:
                # Success message with restart option
                keyboard = [
                    [InlineKeyboardButton("🚀 Input Data Baru", callback_data='back_to_menu')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                activity_text = "Visit" if kegiatan == 'Visit' else "Dealing"
                
                final_msg = f"""🎉 **Data {activity_text} Berhasil Disimpan!**

🆔 **Kode SA:** {data.get('kode_sa', '-')}
✅ **Status:** Data lengkap (17 field) telah tersimpan ke Google Docs
🕐 **Waktu:** Otomatis tercatat
📱 **Input via:** Mini App Form
📷 **Foto:** Tersimpan ke Google Drive

---
💡 **Pilih aksi selanjutnya:**"""
                
                await status_msg.edit_text(final_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
                logger.info(f"✅ Data saved successfully via Mini App for user {user_id}")
                
            else:
                # Error with retry button
                keyboard = [
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data='back_to_menu')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                error_msg = f"❌ **Gagal Menyimpan Data**\n\nError: {message}\n\n🔄 **Opsi:**"
                
                await status_msg.edit_text(error_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error saving Mini App data: {e}")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Coba Lagi", callback_data='back_to_menu')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                "❌ **Terjadi kesalahan sistem**\n\n"
                "Silakan coba lagi.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )