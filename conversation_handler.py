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

**1.** Masukkan **Kode SA** Anda:
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
        
        elif session.state == ConversationState.WAITING_TELDA:
            await self._handle_telda(update, session, user_message)
        
        elif session.state == ConversationState.WAITING_TANGGAL:
            await self._handle_tanggal(update, session, user_message)
        
        elif session.state == ConversationState.KEGIATAN:
            await self._handle_kegiatan(update, session, user_message)
        
        # Note: WAITING_WITEL and WAITING_KATEGORI ditangani via callback, bukan text message
        
        else:
            # User belum start conversation - show welcome with buttons
            await self._show_welcome_menu(update)
    
    async def _show_welcome_menu(self, update):
        """Show welcome menu with buttons"""
        user_name = update.effective_user.first_name
        
        welcome_text = f"""
**Halo {user_name}!** 👋

🤖**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

Lengkapi setiap pertanyaan yang diberikan dan data akan otomatis tersimpan.
    """
        
        keyboard = [
            [InlineKeyboardButton("Start", callback_data='start_input')],
            [InlineKeyboardButton("Help", callback_data='show_help')]
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
**2.** Masukkan **Nama Lengkap** Anda:
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
**3.** Masukkan **No. Telepon** Anda:
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
        session.set_state(ConversationState.WAITING_WITEL)
        
        # First bubble - confirmation
        confirmation = f"✅ **No. Telepon:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step with buttons
        next_step = f"""
**4.** Pilih **Witel** Anda:
        """
        
        # Create keyboard with 8 Witel options
        keyboard = [
            [InlineKeyboardButton("Bali", callback_data='witel_bali')],
            [InlineKeyboardButton("Jatim Barat", callback_data='witel_jatim_barat')],
            [InlineKeyboardButton("Jatim Timur", callback_data='witel_jatim_timur')],
            [InlineKeyboardButton("Nusa Tenggara", callback_data='witel_nusa_tenggara')],
            [InlineKeyboardButton("Semarang Jateng", callback_data='witel_semarang_jateng')],
            [InlineKeyboardButton("Solo Jateng Timur", callback_data='witel_solo_jateng_timur')],
            [InlineKeyboardButton("Suramadu", callback_data='witel_suramadu')],
            [InlineKeyboardButton("Yogya Jateng Selatan", callback_data='witel_yogya_jateng_selatan')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_witel_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Witel selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract witel name from callback_data
        witel_map = {
            'witel_bali': 'Bali',
            'witel_jatim_barat': 'Jatim Barat',
            'witel_jatim_timur': 'Jatim Timur',
            'witel_nusa_tenggara': 'Nusa Tenggara',
            'witel_semarang_jateng': 'Semarang Jateng',
            'witel_solo_jateng_timur': 'Solo Jateng Timur',
            'witel_suramadu': 'Suramadu',
            'witel_yogya_jateng_selatan': 'Yogya Jateng Selatan'
        }
        
        selected_witel = witel_map.get(query.data)
        
        if not selected_witel:
            await query.message.reply_text("❌ Pilihan Witel tidak valid!")
            return
        
        # Save data and move to next step
        session.add_data('witel', selected_witel)
        session.set_state(ConversationState.WAITING_TELDA)
        
        # Confirmation message
        confirmation = f"✅ **Witel:** {selected_witel}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        # Second bubble - next step
        next_step = f"""
**5.** Masukkan **Telkom Daerah** Anda:
        """
        
        await query.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_telda(self, update, session, telda):
        """Handle Telda input"""
        is_valid, result = self.validator.validate_telda(telda)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Telkom Daerah yang benar:"
            )
            return
        
        # Save data and move to next step
        session.add_data('telda', result)
        session.set_state(ConversationState.WAITING_TANGGAL)
        
        # First bubble - confirmation
        confirmation = f"✅ **Telkom Daerah:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step
        next_step = f"""
**6.** Masukkan **Tanggal** (format: DD/MM/YYYY):
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_tanggal(self, update, session, tanggal):
        """Handle Tanggal input"""
        # Basic validation for date format
        import re
        date_pattern = r'^(\d{1,2})/(\d{1,2})/(\d{4})$'
        
        if not re.match(date_pattern, tanggal):
            await update.message.reply_text(
                "❌ Format tanggal tidak valid. Gunakan format DD/MM/YYYY (contoh: 15/08/2025)"
            )
            return
        
        # Save data and move to next step
        session.add_data('tanggal', tanggal)
        session.set_state(ConversationState.WAITING_KATEGORI)
        
        # First bubble - confirmation
        confirmation = f"✅ **Tanggal:** {tanggal}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step with buttons
        next_step = f"""
**7.** Pilih **Kategori Pelanggan** Anda:
        """
        
        # Create keyboard with 4 Kategori Pelanggan options
        keyboard = [
            [InlineKeyboardButton("Kawasan Industri", callback_data='kategori_kawasan_industri')],
            [InlineKeyboardButton("Desa", callback_data='kategori_desa')],
            [InlineKeyboardButton("Puskesmas", callback_data='kategori_puskesmas')],
            [InlineKeyboardButton("Kecamatan", callback_data='kategori_kecamatan')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_kategori_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Kategori Pelanggan selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract Category name from callback_data
        category_map = {
            'kategori_kawasan_industri': 'Kawasan Industri',
            'kategori_desa': 'Desa',
            'kategori_puskesmas': 'Puskesmas',
            'kategori_kecamatan': 'Kecamatan',
        }
        
        selected_category = category_map.get(query.data)
        
        if not selected_category:
            await query.message.reply_text("❌ Pilihan Kategori tidak valid!")
            return
        
        # Save data and move to next step
        session.add_data('kategori', selected_category)
        session.set_state(ConversationState.KEGIATAN)
        
        # FIXED: Add confirmation message
        confirmation = f"✅ **Kategori Pelanggan:** {selected_category}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        # Continue to next step
        next_step = f"""
**8.** Masukkan **Kegiatan**:
        """
        # Create keyboard with 2 Kategori Kegiatan options
        keyboard = [
            [InlineKeyboardButton("Visit", callback_data='kegiatan_visit')],
            [InlineKeyboardButton("Dealing", callback_data='kegiatan_dealing')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_kegiatan_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Kategori Kegiatan selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract Category name from callback_data
        kegiatan_map = {
            'kegiatan_visit': 'Visit',
            'kegiatan_dealing': 'Dealing',
        }
        
        selected_kegiatan = kegiatan_map.get(query.data)
        
        if not selected_kegiatan:
            await query.message.reply_text("❌ Pilihan Kegiatan tidak valid!")
            return
        
        # Confirmation
        confirmation = f"✅ **Kegiatan:** {kegiatan_map}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
                # Save data and move to next step
        session.add_data('kategori', selected_kegiatan)
        session.set_state(ConversationState.COMPLETED)

        # Process final data
        await self._process_final_data(update, session)
    
    async def _process_final_data(self, update, session):
        """Process final data and save to Google Docs"""
        data = session.data
        
        # First bubble - data completion confirmation
        completion_msg = "✅ **Data Lengkap Berhasil Dikumpulkan!**"
        await update.message.reply_text(completion_msg, parse_mode='Markdown')
        
        # Second bubble - COMPLETE SUMMARY
        summary = f"""
📋 **Ringkasan Data:**
• **Kode SA:** {data['kode_sa']}
• **Nama:** {data['nama']}
• **No. Telepon:** {data['no_telp']}
• **Witel:** {data['witel']}
• **Telkom Daerah:** {data['telda']}
• **Tanggal:** {data['tanggal']}
• **Kategori Pelanggan:** {data['kategori']}
• **Kegiatan:** {data['kegiatan']}
        """
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        
        # Third bubble - saving status
        saving_msg = "⏳ **Menyimpan ke Google Docs...**"
        status_msg = await update.message.reply_text(saving_msg, parse_mode='Markdown')
        
        try:
            # Save to Google Docs with 8 parameters
            success, message = self.docs_handler.add_data_with_kode(
                data['kode_sa'], 
                data['nama'], 
                data['no_telp'], 
                data['witel'],
                data['telda'],
                data['tanggal'],
                data['kategori'],
                data['kegiatan']
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
✅ Data lengkap (8 field) telah tersimpan ke Google Docs
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
        
        # Map states to human readable descriptions
        state_descriptions = {
            ConversationState.WAITING_KODE_SA: "Menunggu Kode SA",
            ConversationState.WAITING_NAMA: "Menunggu Nama Lengkap",
            ConversationState.WAITING_TELEPON: "Menunggu No. Telepon",
            ConversationState.WAITING_WITEL: "Menunggu Pilihan Witel",
            ConversationState.WAITING_TELDA: "Menunggu Telkom Daerah",
            ConversationState.WAITING_TANGGAL: "Menunggu Tanggal",
            ConversationState.WAITING_KATEGORI: "Menunggu Pilihan Kategori",
            ConversationState.KEGIATAN: "Menunggu Kegiatan",
        }
        
        current_step = state_descriptions.get(session.state, "Status tidak dikenal")

        status_msg = f"""
📊 **Status Input Data**

🔄 **Progress:** {completed}/8 {progress_bar}
📍 **Step Saat Ini:** {current_step}

✅ **Data yang Sudah Diisi:**
        """
        
        # Show completed data
        data_display = []
        if session.data.get('kode_sa'):
            data_display.append(f"• Kode SA: {session.data['kode_sa']}")
        if session.data.get('nama'):
            data_display.append(f"• Nama: {session.data['nama']}")
        if session.data.get('no_telp'):
            data_display.append(f"• No. Telepon: {session.data['no_telp']}")
        if session.data.get('witel'):
            data_display.append(f"• Witel: {session.data['witel']}")
        if session.data.get('telda'):
            data_display.append(f"• Telkom Daerah: {session.data['telda']}")
        if session.data.get('tanggal'):
            data_display.append(f"• Tanggal: {session.data['tanggal']}")
        if session.data.get('kategori'):
            data_display.append(f"• Kategori: {session.data['kategori']}")
        if session.data.get('kegiatan'):
            data_display.append(f"• Kegiatan: {session.data['kegiatan']}")
        
        if data_display:
            status_msg += "\n" + "\n".join(data_display)
        else:
            status_msg += "\n• (Belum ada data yang diisi)"
        
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