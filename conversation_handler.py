from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from session_manager import SessionManager
from conversation_states import ConversationState
from validators import DataValidator
from google_docs_simple import SimpleGoogleDocs
import logging

logger = logging.getLogger(__name__)

class ConversationHandler:
    """Main handler untuk conversation flow dengan inline keyboard support"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.validator = DataValidator()
        self.docs_handler = SimpleGoogleDocs()
    
    async def start_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start new conversation - bisa dari command atau callback"""
        # Handle both regular message and callback query
        if update.callback_query:
            user_id = update.callback_query.from_user.id
            user_name = update.callback_query.from_user.first_name
            # For callback query, we need to send new message
            send_message = update.callback_query.message.reply_text
        else:
            user_id = update.effective_user.id
            user_name = update.effective_user.first_name
            send_message = update.message.reply_text
        
        # Reset any existing session
        self.session_manager.reset_session(user_id)
        session = self.session_manager.get_session(user_id)
        
        # Set state to waiting for Kode SA
        session.set_state(ConversationState.WAITING_KODE_SA)
        
        welcome_message = f"""
            **Tahap Input Data Dimulai!**
        
            Silahkan jawab seluruh pertanyaan dengan sesuai dan data Anda akan otomatis tersimpan dalam sistem.

            📝 **Pertanyaan 1**
            Silakan masukkan **Kode SA** Anda:
        """
                
        await send_message(welcome_message, parse_mode='Markdown')
        logger.info(f"Started conversation for user {user_id} ({user_name})")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming message based on conversation state"""
        user_id = update.effective_user.id
        user_message = update.message.text.strip()
        
        session = self.session_manager.get_session(user_id)
        
        if session.state == ConversationState.WAITING_KODE_SA:
            await self._handle_kode_sa(update, session, user_message)
        
        elif session.state == ConversationState.WAITING_NAMA:
            await self._handle_nama(update, session, user_message)
        
        elif session.state == ConversationState.WAITING_TELEPON:
            await self._handle_telepon(update, session, user_message)
        
        elif session.state == ConversationState.WAITING_ALAMAT:
            await self._handle_alamat(update, session, user_message)
        
        else:
            # User belum start conversation - show welcome with buttons
            await self._show_welcome_menu(update)
    
    async def _show_welcome_menu(self, update):
        """Show welcome menu with buttons"""
        user_name = update.effective_user.first_name
        
        welcome_text = f"""
            👋 **Halo {user_name}!**

            🤖 **ChatBot Rekapitulasi Data RLEGS III**

            📝 Pilih aksi yang ingin Anda lakukan:
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Mulai Input Data", callback_data='start_input')],
            [InlineKeyboardButton("📊 Lihat Status", callback_data='show_status')],
            [InlineKeyboardButton("❓ Bantuan", callback_data='show_help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _handle_kode_sa(self, update, session, kode_sa):
        """Handle Kode SA input"""
        is_valid, result = self.validator.validate_kode_sa(kode_sa)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Kode SA yang benar:"
            )
            return
        
        # Save data and move to next step
        session.add_data('kode_sa', result)
        session.set_state(ConversationState.WAITING_NAMA)
        
        # First bubble - confirmation
        confirmation = f"✅ **Kode SA:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step
        next_step = f"""
            📝 **Pertanyaan 2**
            Masukkan **Nama Lengkap** Anda:
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_nama(self, update, session, nama):
        """Handle Nama input"""
        is_valid, result = self.validator.validate_nama(nama)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan nama yang benar:"
            )
            return
        
        session.add_data('nama', result)
        session.set_state(ConversationState.WAITING_TELEPON)
        
        # First bubble - confirmation
        confirmation = f"✅ **Nama:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step
        next_step = f"""
            📝 **Pertanyaan 3**
            Masukkan **No. Telepon** Anda:
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_telepon(self, update, session, telepon):
        """Handle Telepon input"""
        is_valid, result = self.validator.validate_telepon(telepon)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan nomor telepon yang benar:"
            )
            return
        
        session.add_data('no_telp', result)
        session.set_state(ConversationState.WAITING_ALAMAT)
        
        # First bubble - confirmation
        confirmation = f"✅ **No. Telepon:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step
        next_step = f"""
            📝 **Pertanyaan 4**
            Sebutkan **Telkom Daerah** Anda:
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_alamat(self, update, session, alamat):
        """Handle Alamat input - Final step"""
        is_valid, result = self.validator.validate_alamat(alamat)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan alamat yang benar:"
            )
            return
        
        session.add_data('alamat', result)
        session.set_state(ConversationState.COMPLETED)
        
        # Show summary and save
        await self._process_final_data(update, session)
    
    async def _handle_witel(self, update, session, witel):
        return

    async def _process_final_data(self, update, session):
        """Process final data and save to Google Docs"""
        data = session.data
        
        # First bubble - data completion confirmation
        completion_msg = "✅ **Data Lengkap Berhasil Dikumpulkan!**"
        await update.message.reply_text(completion_msg, parse_mode='Markdown')
        
        # Second bubble - summary
        summary = f"""
            📋 **Ringkasan Data:**
            • **Kode SA:** {data['kode_sa']}
            • **Nama:** {data['nama']}
            • **No. Telepon:** {data['no_telp']}
            • **Telkom Daerah:** {data['alamat']}
        """
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
        # Third bubble - saving status
        saving_msg = "⏳ **Menyimpan ke Google Docs...**"
        status_msg = await update.message.reply_text(saving_msg, parse_mode='Markdown')
        
        try:
            # Save to Google Docs
            success, message = self.docs_handler.add_data_with_kode(
                data['kode_sa'], 
                data['nama'], 
                data['no_telp'], 
                data['alamat']
            )
            
            if success:
                # Success with menu buttons
                keyboard = [
                    [InlineKeyboardButton("🚀 Input Data Baru", callback_data='start_input')],
                    [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                final_msg = f"""
                    🎉 **Data Berhasil Disimpan!**

                    🆔 Kode SA: {data['kode_sa']}
                    ✅ Data Anda telah tersimpan ke Google Docs
                    🕐 Waktu: Otomatis tercatat
                    ---
                    💡 **Pilih aksi selanjutnya:**
                """
                
                await status_msg.edit_text(final_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
                # Reset session
                session.reset()
                
                logger.info(f"✅ Data saved successfully for user {update.effective_user.id}")
                
            else:
                # Error with retry button
                keyboard = [
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data='start_input')],
                    [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                error_msg = f"""
                    ❌ **Gagal Menyimpan Data**

                    Error: {message}

                    🔄 **Opsi:**
                """
                
                await status_msg.edit_text(error_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Coba Lagi", callback_data='start_input')],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                "❌ **Terjadi kesalahan sistem**\n\n"
                "Silakan pilih opsi di bawah:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def show_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current conversation status - bisa dari command atau callback"""
        # Handle both regular message and callback query
        if update.callback_query:
            user_id = update.callback_query.from_user.id
            send_message = update.callback_query.message.reply_text
        else:
            user_id = update.effective_user.id
            send_message = update.message.reply_text
        
        session = self.session_manager.get_session(user_id)
        
        # Add back to menu button
        keyboard = [
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if session.state == ConversationState.IDLE:
            await send_message(
                "💤 **Status:** Belum ada data yang sedang diproses\n\n"
                "Gunakan button di bawah untuk navigasi:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        completed, total = session.get_progress()
        progress_bar = "🟩" * completed + "⬜" * (total - completed)
        
        current_step = ""
        if session.state == ConversationState.WAITING_KODE_SA:
            current_step = "Menunggu Kode SA"
        elif session.state == ConversationState.WAITING_NAMA:
            current_step = "Menunggu Nama Lengkap"
        elif session.state == ConversationState.WAITING_TELEPON:
            current_step = "Menunggu No. Telepon"
        elif session.state == ConversationState.WAITING_ALAMAT:
            current_step = "Menunggu Telkom Daerah"
        
        status_msg = f"""
            📊 **Status Input Data**

            🔄 **Progress:** {completed}/{total} {progress_bar}
            📍 **Step Saat Ini:** {current_step}

            ✅ **Data yang Sudah Diisi:**
        """
        
        if session.data['kode_sa']:
            status_msg += f"\n• Kode SA: {session.data['kode_sa']}"
        if session.data['nama']:
            status_msg += f"\n• Nama: {session.data['nama']}"
        if session.data['no_telp']:
            status_msg += f"\n• No. Telepon: {session.data['no_telp']}"
        if session.data['alamat']:
            status_msg += f"\n• Telkom Daerah: {session.data['alamat']}"
        
        status_msg += "\n\n💡 **Lanjutkan dengan mengirim data yang diminta**"
        
        await send_message(status_msg, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current conversation - bisa dari command atau callback"""
        # Handle both regular message and callback query
        if update.callback_query:
            user_id = update.callback_query.from_user.id
            send_message = update.callback_query.message.reply_text
        else:
            user_id = update.effective_user.id
            send_message = update.message.reply_text
        
        session = self.session_manager.get_session(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🚀 Mulai Input Baru", callback_data='start_input')],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if session.state == ConversationState.IDLE:
            await send_message(
                "❌ Tidak ada proses yang sedang berjalan\n\n"
                "Pilih aksi di bawah:",
                reply_markup=reply_markup
            )
            return
        
        session.reset()
        
        await send_message(
            "🚫 **Proses input data dibatalkan**\n\n"
            "Semua data yang belum tersimpan telah dihapus.\n"
            "Pilih aksi selanjutnya:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"Conversation cancelled for user {user_id}")
