from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from session_manager import SessionManager
from conversation_states import ConversationState
from validators import DataValidator
import logging
from io import BytesIO
import base64
from googleservice import GoogleService


logger = logging.getLogger(__name__)

class ConversationHandler:
    """Main handler untuk conversation flow dengan inline keyboard support"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.validator = DataValidator()
        self.googleservices = GoogleService()
        self.stack_history = []
    
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

        self.googleservices.authenticate()
        self.googleservices.build_services()

        # Set state to waiting for Kode SA
        session.set_state(ConversationState.WAITING_KODE_SA)
        
        welcome_message = f"""
**Tahap Input Data Dimulai!**

**1.** Masukkan **Kode SA** Anda:
        """
                
        await send_message(welcome_message, parse_mode='Markdown')
        logger.info(f"Started conversation for user {user_id} ({user_name})")
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        photo = update.message.photo[-1]
        
        session = self.session_manager.get_session(user_id)

        if session.state == ConversationState.WAITING_FOTO_EVIDENCE:
            await self._handle_image(update, session, photo)
    

    # There is a way to merge button_callback and handle_message update is reset for each interaction, in text callback_query is None and in button, message is None. Use that as the saving grace
    async def handle_interaction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            query = update.callback_query
            await query.answer()
        elif update.message:
            if update.message.text:
                query = update.message.text.strip()
            elif update.message.photo:
                query = update.message.photo[-1]

        handler_dict = {
            ConversationState.IDLE: self._show_welcome_menu,
            ConversationState.WAITING_KODE_SA: self._handle_kode_sa,
            ConversationState.WAITING_NAMA: self._handle_nama,
            ConversationState.WAITING_TELEPON: self._handle_telepon,
            ConversationState.WAITING_WITEL: self._handle_witel,
            ConversationState.WAITING_TELDA: self._handle_telda,
            ConversationState.WAITING_TANGGAL: self._handle_tanggal,
            ConversationState.WAITING_KATEGORI: self._handle_kategori,
            ConversationState.WAITING_KEGIATAN: self._handle_kegiatan,
            ConversationState.WAITING_TENANT: self._handle_tenant,
            ConversationState.WAITING_LAYANAN: self._handle_layanan,
            ConversationState.WAITING_TARIF: self._handle_tarif,
            ConversationState.WAITING_NAMA_PIC: self._handle_nama_pic,
            ConversationState.WAITING_JABATAN_PIC: self._handle_jabatan_pic,
            ConversationState.WAITING_TELEPON_PIC: self._handle_telepon_pic,
            ConversationState.WAITING_PAKET_DEAL: self._handle_paket_deal,
            ConversationState.WAITING_DEAL_BUNDLING: self._handle_deal_bundling,
            ConversationState.WAITING_FOTO_EVIDENCE: self._handle_foto_evidence
        }

    async def button_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()  # Acknowledge the callback
        
        # Handle Witel selection buttons 
        if query.data.startswith('witel_'):
            await self.handle_witel_selection(update, context)
            return
        
        # Handle Kategori selection buttons 
        if query.data.startswith('kategori_'):
            await self.handle_kategori_selection(update, context)
            return
        
        # Handle Kegiatan selection buttons
        if query.data.startswith('kegiatan_'):
            await self.handle_kegiatan_selection(update, context)
            return
        
        # Handle Layanan selection buttons
        if query.data.startswith('layanan_'):
            await self.handle_layanan_selection(update, context)
            return
        
        # Handle Tarif selection buttons
        if query.data.startswith('tarif_'):
            await self.handle_tarif_selection(update, context)
            return
        
        # Handle Paket selection buttons
        if query.data.startswith('paket_'):
            await self.handle_paket_selection(update, context)
            return
        
        # Handle Deal Bundling selection buttons
        if query.data.startswith('deal_'):
            await self.handle_bundle_selection(update, context)
            return
        
        if query.data == 'start_input':
            # Start input data process
            await self.start_conversation(update, context)
            
        elif query.data == 'show_status':
            # Show current status
            await self.show_status(update, context)
            
        elif query.data == 'show_help':
            # Show help with back button
            help_text = """
🤖 **Bot Rekap Data RLEGS - Panduan**

📝 **Fitur Utama:**
• Input data step-by-step dengan validasi otomatis
• Penyimpanan otomatis ke Google Docs
• Status tracking progress input
• Cancel anytime dengan /cancel

🔄 **Alur Input (15 Step):**
1️⃣ Kode SA (contoh: SA001)
2️⃣ Nama Lengkap
3️⃣ No. Telepon  
4️⃣ Witel
5️⃣ Telkom Daerah
6️⃣ Tanggal
7️⃣ Kategori Pelanggan
8️⃣ Kegiatan
9️⃣ Tipe Layanan
🔟 Tarif Layanan
1️⃣1️⃣ Nama PIC Pelanggan
1️⃣2️⃣ Jabatan PIC
1️⃣3️⃣ Nomor HP PIC
1️⃣4️⃣ Deal Paket
1️⃣5️⃣ Deal Bundling

⚡ **Tips:**
- Gunakan button untuk navigasi mudah
- Data divalidasi real-time
- Bisa batalkan dengan /cancel
- Lihat progress dengan button Status

💾 **Data tersimpan otomatis ke Google Docs**
            """
            
            keyboard = [
                [InlineKeyboardButton("🏠 Kembali ke Menu", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                help_text, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        elif query.data == 'back_to_menu':
            # Back to main menu
            await self.handle_back_to_menu(update, context)

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
        
        elif session.state == ConversationState.WAITING_NAMA_PIC:
            await self._handle_nama_pic(update, session, user_message)

        elif session.state == ConversationState.WAITING_JABATAN_PIC:
            await self._handle_jabatan_pic(update, session, user_message)
            
        elif session.state == ConversationState.WAITING_TELEPON_PIC:
            await self._handle_telepon_pic(update, session, user_message)

        elif session.state == ConversationState.WAITING_TENANT:
            await self._handle_tenant(update, session, user_message)
        
        elif session.state == ConversationState.IDLE:
            # User belum start conversation - show welcome with buttons
            await self._show_welcome_menu(update)
        else:
            await update.message.reply_text("Mohon untuk mengisi data sesuai format")

        # Note: WAITING_WITEL, WAITING_KATEGORI, dll ditangani via callback, bukan text message

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
**6.** Masukkan **Tanggal Visit**: 
(format: DD/MM/YYYY, DD-MM-YYYY, atau DD MM YYYY)
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_tanggal(self, update, session, tanggal):
        """Handle Tanggal input"""
        is_valid, result = self.validator.validate_tanggal(tanggal)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan tanggal yang benar:"
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
        session.set_state(ConversationState.WAITING_TENANT)
        
        # Confirmation message
        confirmation = f"✅ **Kategori Pelanggan:** {selected_category}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        # Second bubble - next step
        next_step = f"""
**8.** Masukkan **Nama Tenant / Desa / Puskesmas / Kecamatan yang divisit**:
        """
        
        await query.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_tenant(self, update, session, tenant):
        """Handle Nama Tenant input"""
        is_valid, result = self.validator.validate_tenant(tenant)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\n Silakan masukkan Nama Tenant / Desa / Puskesmas / Kecamatan yang benar:"
            )
            return
        
        # Save data and move to next step
        session.add_data('tenant', result)
        session.set_state(ConversationState.WAITING_KEGIATAN)
        
        # First bubble - confirmation
        confirmation = f"✅ **Nama Tenant / Desa / Puskesmas / Kecamatan:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')

        # Continue to next step
        next_step = f"""
**9.** Pilih **Kegiatan**:
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
        
        # Confirmation message
        confirmation = f"✅ **Kegiatan:** {selected_kegiatan}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Save data with correct key
        session.add_data('kegiatan', selected_kegiatan)
        session.set_state(ConversationState.WAITING_LAYANAN)

        # Continue to next step
        next_step = f"""
**10.** Pilih **Layanan yang digunakan saat ini**:
        """
        # Create keyboard with 3 Tipe Layanan options
        keyboard = [
            [InlineKeyboardButton("Indihome", callback_data='layanan_indihome')],
            [InlineKeyboardButton("Indibiz", callback_data='layanan_indibiz')],
            [InlineKeyboardButton("Kompetitor", callback_data='layanan_kompetitor')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_layanan_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Layanan selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract Category name from callback_data
        layanan_map = {
            'layanan_indihome': 'Indihome',
            'layanan_indibiz': 'Indibiz',
            'layanan_kompetitor': 'Kompetitor'
        }
        
        selected_layanan = layanan_map.get(query.data)
        
        if not selected_layanan:
            await query.message.reply_text("❌ Pilihan Layanan tidak valid!")
            return
        
        # Confirmation message
        confirmation = f"✅ **Tipe Layanan:** {selected_layanan}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Save data with correct key
        session.add_data('layanan', selected_layanan)
        session.set_state(ConversationState.WAITING_TARIF)

        # Continue to next step
        next_step = f"""
**11.** Pilih **Tarif Layanan saat ini**:
        """
        # Create keyboard with 3 Tarif Layanan options
        keyboard = [
            [InlineKeyboardButton("< Rp 200.000", callback_data='tarif_rendah')],
            [InlineKeyboardButton("Rp 200.000 - Rp 350.000", callback_data='tarif_menengah')],
            [InlineKeyboardButton("> Rp 500.000", callback_data='tarif_tinggi')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_tarif_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Tarif Layanan selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract Category name from callback_data
        tarif_map = {
            'tarif_rendah': '< Rp 200.000',
            'tarif_menengah': 'Rp 200.000 - Rp 350.000',
            'tarif_tinggi': '> Rp 500.000'
        }
        
        selected_tarif = tarif_map.get(query.data)
        
        if not selected_tarif:
            await query.message.reply_text("❌ Pilihan Tarif Layanan tidak valid!")
            return
        
        # Confirmation message
        confirmation = f"✅ **Tarif Layanan:** {selected_tarif}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Save data with correct key
        session.add_data('tarif', selected_tarif)
        session.set_state(ConversationState.WAITING_NAMA_PIC)

        # Second bubble - next step
        next_step = f"""
**12.** Masukkan **Nama PIC Pelanggan**:
        """
        
        await query.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_nama_pic(self, update, session, nama_pic):
        """Handle Nama PIC Pelanggan input"""
        is_valid, result = self.validator.validate_nama_pic(nama_pic)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Nama PIC Pelanggan yang benar:"
            )
            return
        
        # Save data and move to next step
        session.add_data('nama_pic', result)
        session.set_state(ConversationState.WAITING_JABATAN_PIC)
        
        # First bubble - confirmation
        confirmation = f"✅ **Nama PIC Pelanggan:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')

        # Second bubble - next step
        next_step = f"""
**13.** Masukkan **Jabatan PIC**:
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_jabatan_pic(self, update, session, jabatan_pic):
        """Handle Jabatan PIC input"""
        is_valid, result = self.validator.validate_jabatan_pic(jabatan_pic)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Jabatan PIC yang benar:"
            )
            return
        
        # Save data and move to next step
        session.add_data('jabatan_pic', result)
        session.set_state(ConversationState.WAITING_TELEPON_PIC)
        
        # First bubble - confirmation
        confirmation = f"✅ **Jabatan PIC:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Second bubble - next step
        next_step = f"""
**14.** Masukkan **Nomor HP PIC**:
        """
        
        await update.message.reply_text(next_step, parse_mode='Markdown')
    
    async def _handle_telepon_pic(self, update, session, telepon_pic):
        """Handle Nomor HP PIC input"""
        is_valid, result = self.validator.validate_telepon_pic(telepon_pic)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Nomor HP PIC yang benar:"
            )
            return
        
        # Save data and complete the process
        session.add_data('telepon_pic', result)
        session.set_state(ConversationState.WAITING_PAKET_DEAL)
        
        # First bubble - confirmation
        confirmation = f"✅ **Nomor HP PIC:** {result}"
        await update.message.reply_text(confirmation, parse_mode='Markdown')

        # Continue to next step
        next_step = f"""
**15.** Jika Anda melakukan **Dealing, pilih salah satu deal paket Mbps**:
        """
        # Create keyboard with 4 Dealing Paket options
        keyboard = [
            [InlineKeyboardButton("50 Mbps", callback_data='paket_50')],
            [InlineKeyboardButton("75 Mbps", callback_data='paket_75')],
            [InlineKeyboardButton("100 Mbps", callback_data='paket_100')],
            [InlineKeyboardButton("> 100 Mbps", callback_data='paket_>100')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_paket_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Dealing Paket selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract Category name from callback_data
        paket_map = {
            'paket_50': '50 Mbps',
            'paket_75': '75 Mbps',
            'paket_100': '100 Mbps',
            'paket_>100': '> 100 Mbps',
        }
        
        selected_paket = paket_map.get(query.data)
        
        if not selected_paket:
            await query.message.reply_text("❌ Pilihan Paket Dealing tidak valid!")
            return
        
        # Confirmation message
        confirmation = f"✅ **Deal Paket:** {selected_paket}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Save data with correct key
        session.add_data('paket_deal', selected_paket)
        session.set_state(ConversationState.WAITING_DEAL_BUNDLING)

        # Continue to next step
        next_step = f"""
**16.** Pilih salah satu dealing **layanan bundling**:
        """
        # Create keyboard with 4 Dealing Bundling options
        keyboard = [
            [InlineKeyboardButton("1P Internet Only", callback_data='deal_IO')],
            [InlineKeyboardButton("2P Internet + TV", callback_data='deal_IT')],
            [InlineKeyboardButton("2P Internet + Telepon", callback_data='deal_ITL')],
            [InlineKeyboardButton("3P Internet + TV + Telepon", callback_data='deal_ITT')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_bundle_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Dealing Bundle selection dari inline keyboard"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        session = self.session_manager.get_session(user_id)
        
        # Extract Category name from callback_data
        bundle_map = {
            'deal_IO': '1P Internet Only',
            'deal_IT': '2P Internet + TV',
            'deal_ITL': '2P Internet + Telepon',
            'deal_ITT': '3P Internet + TV + Telepon',
        }
        
        selected_bundle = bundle_map.get(query.data)
        
        if not selected_bundle:
            await query.message.reply_text("❌ Pilihan Bundling tidak valid!")
            return
        
        # Confirmation message
        confirmation = f"✅ **Deal Bundling:** {selected_bundle}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        # Save data with correct key
        session.add_data('deal_bundling', selected_bundle)
        session.set_state(ConversationState.WAITING_FOTO_EVIDENCE)
        
        next_step = f"""
**17. Upload Foto Evidence Visit**:
        """
        
        await query.message.reply_text(next_step, parse_mode='Markdown')

    async def _handle_image(self, update, session, photo):
        photo_file = await photo.get_file()
        
        bio = BytesIO()
        await photo_file.download_to_memory(out=bio)

        bio.seek(0)
        encoded_image = base64.b64encode(bio.read()).decode('utf-8')

        session.add_data('foto_evidence', encoded_image)
        session.set_state(ConversationState.COMPLETED)
        
        # TEMPORARY DELETE THIS, SEND CONFIRMATION AT THE SUMMARY INSTEAD
        # bio.seek(0)
        # await update.message.reply_photo(photo=bio, caption="**Foto Evidence**")
        await self._process_final_data(update, session)

    async def _process_final_data(self, query_or_update, session):
        """Process final data and save to Google Docs"""
        data = session.data
        
        # Handle both callback query and regular update
        if hasattr(query_or_update, 'from_user'):
            # This is a callback query
            send_message = query_or_update.message.reply_text
            edit_message = query_or_update.message.edit_text
            reply_photo = query_or_update.message.reply_photo
            user_id = query_or_update.from_user.id
        else:
            # This is a regular update
            send_message = query_or_update.message.reply_text
            reply_photo = query_or_update.message.reply_photo
            edit_message = None
            user_id = query_or_update.effective_user.id
        
        # First bubble - data completion confirmation
        completion_msg = "✅ **Data Lengkap Berhasil Dikumpulkan!**"
        await send_message(completion_msg, parse_mode='Markdown')
        
        # Second bubble - COMPLETE SUMMARY with all fields
        summary = f"""
📋 **Ringkasan Data Lengkap:**
• **Kode SA:** {data.get('kode_sa', '-')}
• **Nama:** {data.get('nama', '-')}
• **No. Telepon:** {data.get('no_telp', '-')}
• **Witel:** {data.get('witel', '-')}
• **Telkom Daerah:** {data.get('telda', '-')}
• **Tanggal:** {data.get('tanggal', '-')}
• **Kategori Pelanggan:** {data.get('kategori', '-')}
• **Kegiatan:** {data.get('kegiatan', '-')}
• **Nama Tenant:** {data.get('tenant', '-')}
• **Tipe Layanan:** {data.get('layanan', '-')}
• **Tarif Layanan:** {data.get('tarif', '-')}
• **Nama PIC Pelanggan:** {data.get('nama_pic', '-')}
• **Jabatan PIC:** {data.get('jabatan_pic', '-')}
• **Nomor HP PIC:** {data.get('telepon_pic', '-')}
• **Deal Paket:** {data.get('paket_deal', '-')}
• **Deal Bundling:** {data.get('deal_bundling', '-')}
        """
        
        image_bytes = base64.b64decode(data.pop('foto_evidence'))

        image_file = BytesIO(image_bytes)
        image_file.name = "confirm.jpg"
        image_file.seek(0)

        await reply_photo(photo=image_file, caption=summary, parse_mode='Markdown')
        
        # Third bubble - saving status
        saving_msg = "⏳ **Menyimpan ke Google Sheet...**"
        status_msg = await send_message(saving_msg, parse_mode='Markdown')
        
        try:
            # Upload image to google drive
            image_file_name = f'{data.get('kode_sa')}_{data.get('tanggal')}_{data.get('kegiatan')}.jpg'

            image_link = self.googleservices.upload_to_drive(image_file, image_file_name)
            data['foto_evidence'] = image_link

            # Append link to submission data
            data_to_submit = list(data.values())
            logger.info(f"Data to submit: {data_to_submit}")

            success, message = self.googleservices.append_to_sheet([data_to_submit])
                        
            if success:
                # Success with menu buttons
                keyboard = [
                    [InlineKeyboardButton("🚀 Input Data Baru", callback_data='start_input')],
                    [InlineKeyboardButton("📊 Lihat Status", callback_data='show_status')],
                    [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                final_msg = f"""
🎉 **Data Berhasil Disimpan!**

🆔 Kode SA: {data.get('kode_sa', '-')}
✅ Data lengkap (15 field) telah tersimpan ke Google Docs
🕐 Waktu: Otomatis tercatat
---
💡 **Pilih aksi selanjutnya:**
                """
                
                await status_msg.edit_text(final_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
                # Reset session
                session.reset()
                
                logger.info(f"✅ Data saved successfully for user {user_id}")
                
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
            [InlineKeyboardButton("🚀 Lanjutkan Input", callback_data='start_input')],
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
        
        # Calculate progress based on all 15 fields
        total_fields = 15
        completed_fields = len([k for k in session.data.keys() if session.data[k]])
        progress_percentage = (completed_fields / total_fields) * 100
        progress_bar = "🟩" * completed_fields + "⬜" * (total_fields - completed_fields)
        
        # Map states to human readable descriptions
        state_descriptions = {
            ConversationState.WAITING_KODE_SA: "Menunggu Kode SA",
            ConversationState.WAITING_NAMA: "Menunggu Nama Lengkap",
            ConversationState.WAITING_TELEPON: "Menunggu No. Telepon",
            ConversationState.WAITING_WITEL: "Menunggu Pilihan Witel",
            ConversationState.WAITING_TELDA: "Menunggu Telkom Daerah",
            ConversationState.WAITING_TANGGAL: "Menunggu Tanggal",
            ConversationState.WAITING_KATEGORI: "Menunggu Pilihan Kategori",
            ConversationState.WAITING_KEGIATAN: "Menunggu Pilihan Kegiatan",
            ConversationState.WAITING_TENANT: "Menunggu Pilihan Tenant",
            ConversationState.WAITING_LAYANAN: "Menunggu Pilihan Layanan",
            ConversationState.WAITING_TARIF: "Menunggu Pilihan Tarif",
            ConversationState.WAITING_NAMA_PIC: "Menunggu Nama PIC Pelanggan",
            ConversationState.WAITING_JABATAN_PIC: "Menunggu Jabatan PIC",
            ConversationState.WAITING_TELEPON_PIC: "Menunggu Nomor HP PIC",
            ConversationState.WAITING_PAKET_DEAL: "Menunggu Deal Paket",
            ConversationState.WAITING_DEAL_BUNDLING: "Menunggu Deal Bundling",
            ConversationState.WAITING_FOTO_EVIDENCE: "Menunggu Upload Foto Evidence",
            ConversationState.COMPLETED: "Data Lengkap"
        }
        
        current_step = state_descriptions.get(session.state, "Status tidak dikenal")

        status_msg = f"""
📊 **Status Input Data**

🔄 **Progress:** {completed_fields}/{total_fields} ({progress_percentage:.0f}%) 
{progress_bar}

📍 **Step Saat Ini:** {current_step}

✅ **Data yang Sudah Diisi:**
        """
        
        # Show completed data
        data_display = []
        field_labels = {
            'kode_sa': 'Kode SA',
            'nama': 'Nama',
            'no_telp': 'No. Telepon',
            'witel': 'Witel',
            'telda': 'Telkom Daerah',
            'tanggal': 'Tanggal',
            'kategori': 'Kategori Pelanggan',
            'kegiatan': 'Kegiatan',
            'tenant' : 'Nama Tenant',
            'layanan': 'Tipe Layanan',
            'tarif': 'Tarif Layanan',
            'nama_pic': 'Nama PIC Pelanggan',
            'jabatan_pic': 'Jabatan PIC',
            'telepon_pic': 'Nomor HP PIC',
            'paket_deal': 'Deal Paket',
            'deal_bundling': 'Deal Bundling',
            'foto_evidence': 'Foto Evidence Visit'
        }
        
        for key, label in field_labels.items():
            if session.data.get(key):
                data_display.append(f"• {label}: {session.data[key]}")
        
        if data_display:
            status_msg += "\n" + "\n".join(data_display)
        else:
            status_msg += "\n• (Belum ada data yang diisi)"
        
        if session.state != ConversationState.COMPLETED:
            status_msg += "\n\n💡 **Lanjutkan dengan mengirim data yang diminta**"
        else:
            status_msg += "\n\n🎉 **Data sudah lengkap dan siap disimpan!**"
        
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
        
        # Show what data will be lost
        completed_fields = len([k for k in session.data.keys() if session.data[k]])
        
        if completed_fields > 0:
            cancel_msg = f"""
🚫 **Batalkan Proses Input Data?**

⚠️ **Data yang akan hilang:**
• {completed_fields} field yang sudah diisi
• Progress: {completed_fields}/15 langkah

❓ **Yakin ingin membatalkan?**
            """
        else:
            cancel_msg = "🚫 **Proses input data dibatalkan**\n\nPilih aksi selanjutnya:"
        
        session.reset()
        
        await send_message(
            cancel_msg,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"Conversation cancelled for user {user_id}")
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        # Handle both regular message and callback query
        if update.callback_query:
            send_message = update.callback_query.message.reply_text
        else:
            send_message = update.message.reply_text
        
        help_text = f"""
🤖 **Bantuan - Rekapitulasi Data RLEGS III**

📝 **Cara Penggunaan:**
1. Tekan tombol "Start" untuk memulai input data
2. Ikuti instruksi step-by-step (15 langkah)
3. Data akan otomatis tersimpan ke Google Docs

🔢 **Data yang Dikumpulkan:**
• Kode SA
• Nama Lengkap
• No. Telepon
• Witel (8 pilihan)
• Telkom Daerah
• Tanggal Visit
• Kategori Pelanggan (4 pilihan)
• Kegiatan (2 pilihan)
• Nama Tenant
• Tipe Layanan (3 pilihan)
• Tarif Layanan (3 pilihan)
• Nama PIC Pelanggan
• Jabatan PIC
• Nomor HP PIC
• Deal Paket (4 pilihan)
• Deal Bundling (4 pilihan)

📋 **Commands Tersedia:**
/start - Mulai/restart bot
/cancel - Batalkan input data
/help - Tampilkan bantuan ini

💡 **Tips:**
• Data akan tersimpan otomatis setelah lengkap
• Gunakan /status untuk melihat progress
• Gunakan /cancel jika ingin mengulang dari awal

❓ **Butuh bantuan?** Hubungi administrator.
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Mulai Input", callback_data='start_input')],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await send_message(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def handle_back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to menu button"""
        query = update.callback_query
        await query.answer()
        
        user_name = query.from_user.first_name
        
        welcome_text = f"""
**Halo {user_name}!** 👋

🤖**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

Lengkapi setiap pertanyaan yang diberikan dan data akan otomatis tersimpan.
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Mulai Input Data", callback_data='start_input')],
            [InlineKeyboardButton("📊 Lihat Status", callback_data='show_status')],
            [InlineKeyboardButton("❓ Bantuan", callback_data='show_help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
