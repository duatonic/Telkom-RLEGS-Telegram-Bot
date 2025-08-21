from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
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
    def __init__(self):
        self.session_manager = SessionManager()
        self.validator = DataValidator()
        self.google_service = GoogleService()
        #self.stack_history = []
        
        self.handler_functions_map = {
            ConversationState.IDLE: self.start_conversation,
            ConversationState.WAITING_KODE_SA: self.handle_kode_sa,
            ConversationState.WAITING_NAMA: self.handle_nama,
            ConversationState.WAITING_TELEPON: self.handle_telepon,
            ConversationState.WAITING_WITEL: self.handle_witel,
            ConversationState.WAITING_TELDA: self.handle_telda,
            ConversationState.WAITING_TANGGAL: self.handle_tanggal,
            ConversationState.WAITING_KATEGORI: self.handle_kategori,
            ConversationState.WAITING_KEGIATAN: self.handle_kegiatan,
            ConversationState.WAITING_TENANT: self.handle_tenant,
            ConversationState.WAITING_LAYANAN: self.handle_layanan,
            ConversationState.WAITING_TARIF: self.handle_tarif,
            ConversationState.WAITING_NAMA_PIC: self.handle_nama_pic,
            ConversationState.WAITING_JABATAN_PIC: self.handle_jabatan_pic,
            ConversationState.WAITING_TELEPON_PIC: self.handle_telepon_pic,
            ConversationState.WAITING_PAKET_DEAL: self.handle_paket_deal,
            ConversationState.WAITING_DEAL_BUNDLING: self.handle_deal_bundling,
            ConversationState.WAITING_FOTO_EVIDENCE: self.handle_foto_evidence,
            ConversationState.COMPLETED: self.process_all_data
        }

        self.STATE_TO_DATA_KEY = {
            ConversationState.WAITING_KODE_SA: 'kode_sa',
            ConversationState.WAITING_NAMA: 'nama',
            ConversationState.WAITING_TELEPON: 'no_telp',
            ConversationState.WAITING_WITEL: 'witel',
            ConversationState.WAITING_TELDA: 'telda',
            ConversationState.WAITING_TANGGAL: 'tanggal',
            ConversationState.WAITING_KATEGORI: 'kategori',
            ConversationState.WAITING_TENANT: 'tenant',
            ConversationState.WAITING_KEGIATAN: 'kegiatan',
            ConversationState.WAITING_LAYANAN: 'layanan',
            ConversationState.WAITING_TARIF: 'tarif',
            ConversationState.WAITING_NAMA_PIC: 'nama_pic',
            ConversationState.WAITING_JABATAN_PIC: 'jabatan_pic',
            ConversationState.WAITING_TELEPON_PIC: 'telepon_pic',
            ConversationState.WAITING_PAKET_DEAL: 'paket_deal',
            ConversationState.WAITING_DEAL_BUNDLING: 'deal_bundling',
            ConversationState.WAITING_FOTO_EVIDENCE: 'foto_evidence',
        }

        self.STATE_TO_QUESTION_ASKER = {
            ConversationState.WAITING_KODE_SA: self._ask_kode_sa,
            ConversationState.WAITING_NAMA: self._ask_nama,
            ConversationState.WAITING_TELEPON: self._ask_telepon,
            ConversationState.WAITING_WITEL: self._ask_witel,
            ConversationState.WAITING_TELDA: self._ask_telda,
            ConversationState.WAITING_TANGGAL: self._ask_tanggal,
            ConversationState.WAITING_KATEGORI: self._ask_kategori,
            ConversationState.WAITING_TENANT: self._ask_tenant,
            ConversationState.WAITING_KEGIATAN: self._ask_kegiatan,
            ConversationState.WAITING_LAYANAN: self._ask_layanan,
            ConversationState.WAITING_TARIF: self._ask_tarif,
            ConversationState.WAITING_NAMA_PIC: self._ask_nama_pic,
            ConversationState.WAITING_JABATAN_PIC: self._ask_jabatan_pic,
            ConversationState.WAITING_TELEPON_PIC: self._ask_telepon_pic,
            ConversationState.WAITING_PAKET_DEAL: self._ask_paket_deal,
            ConversationState.WAITING_DEAL_BUNDLING: self._ask_deal_bundling,
            ConversationState.WAITING_FOTO_EVIDENCE: self._ask_foto_evidence,
            ConversationState.COMPLETED: self.handle_summary,
        }

    def _create_back_keyboard(self, custom_keyboard=None):
        keyboard = custom_keyboard if custom_keyboard else []
        
        back_button = [InlineKeyboardButton("⬅️ Kembali", callback_data='go_back')]
        keyboard.append(back_button)
            
        return InlineKeyboardMarkup(keyboard)

    async def _handle_go_back(self, query: CallbackQuery, session):
        if not session.history:
            await query.answer("Tidak bisa kembali lagi.")
            return

        await query.message.delete()

        previous_state = session.history.pop()

        data_key_to_clear = self.STATE_TO_DATA_KEY.get(previous_state)
        if data_key_to_clear and data_key_to_clear in session.data:
            del session.data[data_key_to_clear]
            logger.info(f"Cleared data for key: {data_key_to_clear}")

        session.set_state(previous_state)
        
        question_asker = self.STATE_TO_QUESTION_ASKER.get(previous_state)
        if question_asker:
            await question_asker(query, session, is_going_back=True)
        else:
            logger.error(f"No question asker found for state: {previous_state}")
            await query.message.reply_text("Terjadi kesalahan saat kembali.")

    async def handle_interactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Condition for button
        if update.callback_query:
            logger.info(f'received button input, type: {type(update.callback_query)}')
            query = update.callback_query
            await query.answer()
            user_id = query.from_user.id
        # Condition for non-button
        else:
            logger.info(f'received text input, type: {type(update)}')
            query = update
            user_id = query.effective_user.id
        
        session = self.session_manager.get_session(user_id)

        if isinstance(query, CallbackQuery) and query.data == 'go_back':
            await self._handle_go_back(query, session)
            return

        if session.state in self.handler_functions_map:
            await self.handler_functions_map[session.state](query, session)
        else:
            if update.message:
                await update.message.reply_text('State undefined or incorrect input type.')

    async def start_conversation(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu tombol.")
            return

        user_id = query.from_user.id
        user_name = query.from_user.first_name
        
        # Reset any existing session
        self.session_manager.reset_session(user_id)
        self.history = []

        self.google_service.authenticate()
        self.google_service.build_services()
        
        logger.info(f"Started conversation for user {user_id} ({user_name})")
        await self._ask_kode_sa(query, session)

    async def _ask_kode_sa(self, query, session, is_going_back=False):
        # Set state to waiting for Kode SA
        session.set_state(ConversationState.WAITING_KODE_SA)
        
        welcome_message = f"**Input Data Dimulai!**\n\n**1.** Masukkan **Kode SA**:"
        
        if is_going_back or isinstance(query, CallbackQuery):
            await query.message.reply_text(welcome_message, parse_mode='Markdown')
        else:
            await query.message.reply_text(welcome_message, parse_mode='Markdown')

    async def handle_kode_sa(self, query, session):
        if query.message.photo or query.message.sticker or query.message.document:
            logger.info('Input is not a text.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format")
            return

        kode_sa = query.message.text.strip()

        is_valid, result = self.validator.validate_kode_sa(kode_sa)

        if not is_valid:
            await query.message.reply_text(f"❌ {result}\n\nSilakan masukkan Kode SA yang benar:")
            return
        
        session.add_data('kode_sa', result)
        
        confirmation = f"✅ **Kode SA:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_nama(query, session)

    async def _ask_nama(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_NAMA)
        
        next_step = "**2.** Masukkan **Nama Lengkap** Anda:"
        reply_markup = self._create_back_keyboard() if session.history else None
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_nama(self, query, session):
        if query.message.photo or query.message.sticker or query.message.document:
            logger.info('Input is not a text.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        nama = query.message.text.strip()

        is_valid, result = self.validator.validate_nama(nama)
        
        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan nama yang benar:"
            )
            return
        
        session.add_data('nama', result)

        confirmation = f"✅ **Nama:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        session.history.append(session.state)
        await self._ask_telepon(query, session)
    
    async def _ask_telepon(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_TELEPON)
        
        next_step = "**3.** Masukkan **No. Telepon** Anda:"
        reply_markup = self._create_back_keyboard() if session.history else None
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_telepon(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        no_telp = query.message.text.strip()

        is_valid, result = self.validator.validate_telepon(no_telp)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan nomor telepon yang benar:"
            )
            return
        
        session.add_data('no_telp', result)
        
        confirmation = f"✅ **No. Telepon:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        session.history.append(session.state)
        await self._ask_witel(query, session)

    async def _ask_witel(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_WITEL)
        
        next_step = "**4.** Pilih **Witel** Anda:"
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
        reply_markup = self._create_back_keyboard(keyboard)
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_witel(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu witel.")
            return

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
        
        session.add_data('witel', selected_witel)

        confirmation = f"✅ **Witel:** {selected_witel}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_telda(query, session)
    
    async def _ask_telda(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_TELDA)
        
        next_step = "**5.** Masukkan **Telkom Daerah** Anda:"
        reply_markup = self._create_back_keyboard() if session.history else None
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_telda(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        telda = query.message.text.strip()

        is_valid, result = self.validator.validate_telda(telda)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Telkom Daerah yang benar:"
            )
            return
        
        session.add_data('telda', result)
        
        confirmation = f"✅ **Telkom Daerah:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_tanggal(query, session)

    async def _ask_tanggal(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_TANGGAL)

        next_step = f"**6.** Masukkan **Tanggal Visit**:\n(format: DD/MM/YYYY, DD-MM-YYYY, atau DD MM YYYY)"
        reply_markup = self._create_back_keyboard() if session.history else None

        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_tanggal(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        tanggal = query.message.text.strip()

        is_valid, result = self.validator.validate_tanggal(tanggal)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan tanggal yang benar:"
            )
            return
        
        session.add_data('tanggal', tanggal)
        
        confirmation = f"✅ **Tanggal:** {tanggal}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_kategori(query, session)
        
    async def _ask_kategori(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_KATEGORI)
        next_step = "**7.** Pilih **Kategori Pelanggan** Anda:"
        
        keyboard = [
            [InlineKeyboardButton("Kawasan Industri", callback_data='kategori_kawasan_industri')],
            [InlineKeyboardButton("Desa", callback_data='kategori_desa')],
            [InlineKeyboardButton("Puskesmas", callback_data='kategori_puskesmas')],
            [InlineKeyboardButton("Kecamatan", callback_data='kategori_kecamatan')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)

        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_kategori(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu kategori.")
            return

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
        
        session.add_data('kategori', selected_category)
        
        confirmation = f"✅ **Kategori Pelanggan:** {selected_category}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_tenant(query, session)

    async def _ask_tenant(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_TENANT)
        
        next_step = "**8.** Masukkan **Nama Tenant / Desa / Puskesmas / Kecamatan yang divisit**:"
        reply_markup = self._create_back_keyboard() if session.history else None

        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_tenant(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        tenant = query.message.text.strip()

        is_valid, result = self.validator.validate_tenant(tenant)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\n Silakan masukkan Nama Tenant / Desa / Puskesmas / Kecamatan yang benar:"
            )
            return
        
        session.add_data('tenant', result)
        
        confirmation = f"✅ **Nama Tenant / Desa / Puskesmas / Kecamatan:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_kegiatan(query, session)
        
    async def _ask_kegiatan(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_KEGIATAN)
        
        next_step = "**9.** Pilih **Kegiatan**:"
        keyboard = [
            [InlineKeyboardButton("Visit", callback_data='kegiatan_visit')],
            [InlineKeyboardButton("Dealing", callback_data='kegiatan_dealing')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)

        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_kegiatan(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu kegiatan.")
            return

        kegiatan_map = {
            'kegiatan_visit': 'Visit',
            'kegiatan_dealing': 'Dealing',
        }
        
        selected_kegiatan = kegiatan_map.get(query.data)
        
        if not selected_kegiatan:
            await query.message.reply_text("❌ Pilihan Kegiatan tidak valid!")
            return
        
        session.add_data('kegiatan', selected_kegiatan)

        confirmation = f"✅ **Kegiatan:** {selected_kegiatan}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_layanan(query, session)

    async def _ask_layanan(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_LAYANAN)

        next_step = "**10.** Pilih **Layanan yang digunakan saat ini**:"
        keyboard = [
            [InlineKeyboardButton("Indihome", callback_data='layanan_indihome')],
            [InlineKeyboardButton("Indibiz", callback_data='layanan_indibiz')],
            [InlineKeyboardButton("Kompetitor", callback_data='layanan_kompetitor')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_layanan(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu layanan.")
            return

        layanan_map = {
            'layanan_indihome': 'Indihome',
            'layanan_indibiz': 'Indibiz',
            'layanan_kompetitor': 'Kompetitor'
        }
        
        selected_layanan = layanan_map.get(query.data)
        
        if not selected_layanan:
            await query.message.reply_text("❌ Pilihan Layanan tidak valid!")
            return
        
        session.add_data('layanan', selected_layanan)

        confirmation = f"✅ **Tipe Layanan:** {selected_layanan}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_tarif(query, session)

    async def _ask_tarif(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_TARIF)

        next_step = "**11.** Pilih **Tarif Layanan saat ini**:"
        keyboard = [
            [InlineKeyboardButton("< Rp 200.000", callback_data='tarif_rendah')],
            [InlineKeyboardButton("Rp 200.000 - Rp 350.000", callback_data='tarif_menengah')],
            [InlineKeyboardButton("> Rp 500.000", callback_data='tarif_tinggi')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_tarif(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu tarif.")
            return

        tarif_map = {
            'tarif_rendah': '< Rp 200.000',
            'tarif_menengah': 'Rp 200.000 - Rp 350.000',
            'tarif_tinggi': '> Rp 500.000'
        }
        
        selected_tarif = tarif_map.get(query.data)
        
        if not selected_tarif:
            await query.message.reply_text("❌ Pilihan Tarif Layanan tidak valid!")
            return
        
        session.add_data('tarif', selected_tarif)

        confirmation = f"✅ **Tarif Layanan:** {selected_tarif}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        session.history.append(session.state)
        await self._ask_nama_pic(query, session)

    async def _ask_nama_pic(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_NAMA_PIC)

        next_step = "**12.** Masukkan **Nama PIC Pelanggan**:"
        reply_markup = self._create_back_keyboard() if session.history else None
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_nama_pic(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        nama_pic = query.message.text.strip()

        is_valid, result = self.validator.validate_nama_pic(nama_pic)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Nama PIC Pelanggan yang benar:"
            )
            return
        
        session.add_data('nama_pic', result)
        
        confirmation = f"✅ **Nama PIC Pelanggan:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_jabatan_pic(query, session)

    async def _ask_jabatan_pic(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_JABATAN_PIC)

        next_step = "**13.** Masukkan **Jabatan PIC**:"
        reply_markup = self._create_back_keyboard() if session.history else None
            
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_jabatan_pic(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        jabatan_pic = query.message.text.strip()

        is_valid, result = self.validator.validate_nama_pic(jabatan_pic)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Jabatan PIC yang benar:"
            )
            return
        
        session.add_data('jabatan_pic', result)
        
        confirmation = f"✅ **Jabatan PIC:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        session.history.append(session.state)
        await self._ask_telepon_pic(query, session)

    async def _ask_telepon_pic(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_TELEPON_PIC)

        next_step = "**14.** Masukkan **Nomor HP PIC**:"
        reply_markup = self._create_back_keyboard() if session.history else None
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_telepon_pic(self, query, session):
        if not isinstance(query, Update):
            logger.info('Input is not a text. Expecting text input.')
            await query.message.reply_text("Mohon untuk memasukkan data sesuai format.")
            return

        telepon_pic = query.message.text.strip()

        is_valid, result = self.validator.validate_telepon_pic(telepon_pic)

        if not is_valid:
            await query.message.reply_text(
                f"❌ {result}\n\nSilakan masukkan Nomor HP PIC yang benar:"
            )
            return
        
        session.add_data('telepon_pic', result)
        
        confirmation = f"✅ **Nomor HP PIC:** {result}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')

        session.history.append(session.state)
        await self._ask_paket_deal(query, session)

    async def _ask_paket_deal(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_PAKET_DEAL)

        next_step = "**15.** Jika Anda melakukan **Dealing, pilih salah satu deal paket Mbps**:"
        keyboard = [
            [InlineKeyboardButton("50 Mbps", callback_data='paket_50')],
            [InlineKeyboardButton("75 Mbps", callback_data='paket_75')],
            [InlineKeyboardButton("100 Mbps", callback_data='paket_100')],
            [InlineKeyboardButton("> 100 Mbps", callback_data='paket_>100')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_paket_deal(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu paket.")
            return

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
        
        session.add_data('paket_deal', selected_paket)

        confirmation = f"✅ **Deal Paket:** {selected_paket}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        session.history.append(session.state)
        await self._ask_deal_bundling(query, session)

    async def _ask_deal_bundling(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_DEAL_BUNDLING)

        next_step = "**16.** Pilih salah satu dealing **layanan bundling**:"
        keyboard = [
            [InlineKeyboardButton("1P Internet Only", callback_data='deal_IO')],
            [InlineKeyboardButton("2P Internet + TV", callback_data='deal_IT')],
            [InlineKeyboardButton("2P Internet + Telepon", callback_data='deal_ITL')],
            [InlineKeyboardButton("3P Internet + TV + Telepon", callback_data='deal_ITT')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_deal_bundling(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu paket.")
            return

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
        
        session.add_data('deal_bundling', selected_bundle)

        confirmation = f"✅ **Deal Bundling:** {selected_bundle}"
        await query.message.reply_text(confirmation, parse_mode='Markdown')
        
        session.history.append(session.state)
        await self._ask_foto_evidence(query, session)

    async def _ask_foto_evidence(self, query, session, is_going_back=False):
        session.set_state(ConversationState.WAITING_FOTO_EVIDENCE)

        next_step = "**17. Upload Foto Evidence Visit**:"
        reply_markup = self._create_back_keyboard() if session.history else None
        
        await query.message.reply_text(next_step, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_foto_evidence(self, query, session):
        if not isinstance(query, Update) or not query.message.photo:
            logger.info('Input is not an image. Expecting an image.')
            await query.message.reply_text("Mohon untuk mengunggah foto evidence visit.")
            return
    
        photo = query.message.photo[-1]
        photo_file = await photo.get_file()

        bio = BytesIO()
        await photo_file.download_to_memory(out=bio)

        bio.seek(0)
        encoded_image = base64.b64encode(bio.read()).decode('utf-8')

        session.add_data('foto_evidence', encoded_image)
        await query.message.reply_text("Gambar tersimpan.")

        session.history.append(session.state)
        await self.handle_summary(query, session)

    async def handle_summary(self, query, session):
        session.set_state(ConversationState.COMPLETED)
        
        completion_msg = "✅ **Data Lengkap Berhasil Dikumpulkan!**"
        await query.message.reply_text(completion_msg, parse_mode='Markdown')

        data = session.data

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
        
        image_bytes = base64.b64decode(data.get('foto_evidence'))

        image_file = BytesIO(image_bytes)
        image_file.name = "confirm.jpg"
        image_file.seek(0)
        
        keyboard = [
            [InlineKeyboardButton("✅ Konfirmasi dan Submit", callback_data='confirm_and_submit')],
            [InlineKeyboardButton("❌ Batal", callback_data='batal_submit')],
        ]
        reply_markup = self._create_back_keyboard(keyboard)
        
        await query.message.reply_photo(photo=image_file, caption=summary, parse_mode='Markdown', reply_markup=reply_markup)

    async def process_all_data(self, query, session):
        if not isinstance(query, CallbackQuery):
            logger.info('Input is a text. Expecting button callback.')
            await query.message.reply_text("Mohon untuk memilih salah satu tombol.")
            return

        if query.data == 'batal_submit':
            session.set_state(ConversationState.IDLE)
            await query.message.reply_text("Input data dibatalkan. Kembali ke awal.")
            return
        
        user_id = query.from_user.id
        status_msg = await query.message.reply_text("⏳ **Menyimpan ke Google Sheet...**", parse_mode='Markdown')
        
        data = session.data

        try:
            image_bytes = base64.b64decode(data.pop('foto_evidence'))

            image_file = BytesIO(image_bytes)
            image_file.seek(0)

            image_file_name = f'{data.get('kode_sa')}_{data.get('tanggal')}_{data.get('kegiatan')}.jpg'

            image_link = self.google_service.upload_to_drive(image_file, image_file_name)
            data['foto_evidence'] = image_link

            # Append link to submission data
            data_to_submit = list(data.values())
            logger.info(f"Data to submit: {data_to_submit}")

            success, message = self.google_service.append_to_sheet([data_to_submit])
                        
            if success:
                # Success with menu buttons
                keyboard = [
                    [InlineKeyboardButton("🚀 Input Data Baru", callback_data='start_input')],
                    #[InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                final_msg = f"🎉 **Data Berhasil Disimpan!**\n\n🆔 Kode SA: {data.get('kode_sa', '-')}\n✅ Data lengkap (17 field) telah tersimpan ke Google Docs\n🕐 Waktu: Otomatis tercatat\n---\n💡 **Pilih aksi selanjutnya:**"
                
                await status_msg.edit_text(final_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
                session.reset()
                session.history = []

                logger.info(f"✅ Data saved successfully for user {user_id}")
                
            else:
                # Error with retry button
                keyboard = [
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data='start_input')],
                    #[InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                error_msg = f"❌ **Gagal Menyimpan Data**\n\nError: {message}\n\n🔄 **Opsi:**"
                
                await status_msg.edit_text(error_msg, parse_mode='Markdown', reply_markup=reply_markup)
                
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Coba Lagi", callback_data='start_input')],
                #[InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                "❌ **Terjadi kesalahan sistem**\n\n"
                "Silakan pilih opsi di bawah:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
