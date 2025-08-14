import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from conversation_handler import ConversationHandler
import config

user_forms = {}

class InputData:
    def __init__(self):
        self.nama = None
        self.telepon = None
        self.alamat = None

    def __str__(self):
        return f"{self.nama}, {self.telepon}, {self.alamat}"
    
    def _next_empty(self):
        for field in ['nama', 'telepon', 'alamat']:
            if getattr(self, field) is None:
                return field
        return None

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize conversation handler
conversation_handler = ConversationHandler()

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Command /start"""
#     chat_id = update.message.chat_id
#     user = update.effective_user
#     user_forms[chat_id] = InputData()
#     form = user_forms[chat_id]
#     input_field = form._next_empty() or 'nama'

#     welcome_message = f"""
#         🤖 **Halo {user.first_name}!**

#         Selamat Datang di Bot Rekap Data RLEGS!
#         Data yang kamu kirimkan akan kami rekap menggunakan Google Docs

#         **Cara pakai:**
#         Kirim data dalam 1 pesan dengan format:
#         `Nama, NoTelp, Alamat`

#         Contoh:
#         `John Doe, 081234567890, Jl. Sudirman No. 1 Jakarta`

#         Gunakan /help untuk melihat format lain yang didukung.
#     """

#     initial_message = f"""
#         Masukkan data {input_field}:
#     """
    
#     await update.message.reply_text(welcome_message, parse_mode='Markdown')
#     await update.message.reply_text(initial_message, parse_mode='Markdown')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with inline keyboard"""
    user_name = update.effective_user.first_name
    
    welcome_text = f"""
        👋 **Halo {user_name}!**
        🤖 **Selamat Datang di ChatBot Rekapitulasi Data 8 Fishong Spot RLEGS III**
        📝 Lengkapi data dalam setiap pertanyaan yang diberikan dan data otomatis akan disimpan ke Google Docs.

        🔄 ** Pilih aksi di bawah ini:**
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with inline keyboard"""
    help_text = """
        🤖 **Bot Rekap Data RLEGS - Panduan**

        📝 **Commands:**
        - `/start` - Menu utama bot
        - `/status` - Lihat progress saat ini
        - `/cancel` - Batalkan input yang sedang berjalan
        - `/help` - Tampilkan panduan ini

        🔄 **Alur Input:**
        1️⃣ Kode SA (contoh: SA001)
        2️⃣ Nama Lengkap
        3️⃣ No. Telepon
        4️⃣ Telkom Daerah

        ⚡ **Tips:**
        - Bot akan memandu step by step
        - Data otomatis divalidasi
        - Bisa batalkan kapan saja dengan /cancel
        - Gunakan button untuk navigasi yang mudah

        💾 **Data otomatis tersimpan ke Google Docs setelah lengkap**
    """
    
    # Create back button
    keyboard = [
        [InlineKeyboardButton("Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# async def start_input_loop(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if 'input_data' not in context.user_data:
#         context.user_data['input_data'] = {
#             'nama': None,
#             'no_telp': None,
#             'alamat': None,
#             'step': 'nama'
#         }

#     data = context.user_data['input_data']

#     if all(data[field] is not None for field in ['nama', 'no_telp', 'alamat']):
#         await process_data(update, context)
#         return
    
#     if data['nama'] is None:
#         await update.message.reply_text("🔍 **Masukkan Nama Anda:**")
#         data['step'] = 'nama'
#     elif data['no_telp'] is None:
#         await update.message.reply_text("📞 **Masukkan Nomor Telepon Anda:**")
#         data['step'] = 'no_telp'
#     elif data['alamat'] is None:
#         await update.message.reply_text("🏠 **Masukkan Alamat Anda:**")
#         data['step'] = 'alamat'

async def process_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process data dari user message"""
    try:
        chat_id = update.message.chat_id
        user_text = update.message.text
        user_name = update.effective_user.first_name
        
        if chat_id not in user_forms:
            await update.message.reply_text("please use /start to begin.")
            return
        
        form = user_forms[chat_id]
        current_field = form._next_empty()


        setattr(form, current_field, user_text.strip())
        logger.info(f"User {user_name} input: {current_field} = {user_text.strip()}")

        # TODO: Handle case where all fields are filled
        if form._next_empty() is None:
            await update.message.reply_text("❗ Semua data sudah lengkap. Gunakan /start untuk mengulang.")
            return
        
        # Parse data
        # parsed_data = parser.parse_data(user_text)
                
        # if not parsed_data:
        #     await update.message.reply_text(
        #         "❌ **Format tidak valid!**\n\n"
        #         "Gunakan /help untuk melihat format yang didukung.\n\n"
        #         "Contoh: `John Doe, 081234567890, Jl. Sudirman Jakarta`",
        #         parse_mode='Markdown'
        #     )
        #     return
        
        # Validasi data
        # is_valid, message = parser.validate_data(parsed_data)
        
        # if not is_valid:
        #     await update.message.reply_text(
        #         f"❌ **Validasi gagal:** {message}\n\n"
        #         "Gunakan /help untuk melihat format yang benar.",
        #         parse_mode='Markdown'
        #     )
        #     return
        
        # Konfirmasi data ke user
        # nama = parsed_data['nama']
        # no_telp = parsed_data['no_telp']
        # alamat = parsed_data['alamat']
        

        # konfirmasi = f"""
        #     ✅ **Data berhasil di-parse:**

        #     - **Nama:** {user_text}
        #     - **No. Telepon:** {user_text}  
        #     - **Alamat:** {user_text}

        #     ⏳ Menyimpan ke Google Docs...
        # """
        
        # # Kirim konfirmasi
        # status_msg = await update.message.reply_text(konfirmasi, parse_mode='Markdown')
        # await update.message.reply_text("DONE!!!", parse_mode='Markdown')
        await update.message.reply_text(f"Masukkan data {form._next_empty()}", parse_mode='Markdown')

        # Simpan ke Google Docs
        # success, result_message = docs_handler.add_data(nama, no_telp, alamat)
        
        # if success:
            # Update pesan dengan status sukses
            # final_message = f"""
            #     ✅ **Data berhasil disimpan ke Google Docs!**

            #     - **Nama:** {nama}
            #     - **No. Telepon:** {no_telp}
            #     - **Alamat:** {alamat}
            #     - **Timestamp:** Otomatis ditambahkan

            #     Kirim data lain untuk melanjutkan.
            # """
            
            # await status_msg.edit_text(final_message, parse_mode='Markdown')
            
            # Log sukses
            # logger.info(f"✅ Data saved - User: {user_name}, Nama: {nama}")
            
        # else:
            # Update dengan error message
            # error_message = f"""
            #     ❌ **Gagal menyimpan data!**

            #     Error: {result_message}

            #     Silakan coba lagi atau hubungi admin.
            # """
            
            # await status_msg.edit_text(error_message, parse_mode='Markdown')
            # logger.error(f"❌ Save failed - User: {user_name}, Error: {result_message}")
    
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        await update.message.reply_text(
            "❌ **Terjadi kesalahan sistem.**\n\nSilakan coba lagi nanti.",
            parse_mode='Markdown'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses"""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    user_name = update.effective_user.first_name
    
    if query.data == 'start_input':
        # Start input data process
        await conversation_handler.start_conversation(update, context)
        
    elif query.data == 'show_status':
        # Show current status
        await conversation_handler.show_status(update, context)
        
    elif query.data == 'show_help':
        # Show help with back button
        help_text = """
            🤖 **Bot Rekap Data RLEGS - Panduan**

            📝 **Fitur Utama:**
            • Input data step-by-step dengan validasi otomatis
            • Penyimpanan otomatis ke Google Docs
            • Status tracking progress input
            • Cancel anytime dengan /cancel

            🔄 **Alur Input:**
            1️⃣ Kode SA (contoh: SA001)
            2️⃣ Nama Lengkap
            3️⃣ No. Telepon  
            4️⃣ Telkom Daerah

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
        welcome_text = f"""
            👋 **Halo {user_name}!**

            🤖 **ChatBot Rekapitulasi Data RLEGS III**

            📝 Pilih aksi yang ingin Anda lakukan:
        """
        
        keyboard = [
            [InlineKeyboardButton("Start", callback_data='start_input')],
            [InlineKeyboardButton("Help", callback_data='show_help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands with helpful response"""
    keyboard = [
        [InlineKeyboardButton("Menu", callback_data='back_to_menu')],
        [InlineKeyboardButton("Help", callback_data='show_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "❓ **Command tidak dikenal**\n\n"
        "Gunakan button di bawah untuk navigasi:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def welcome_new_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message for users who just start chatting (any text message when idle)"""
    user_id = update.effective_user.id
    session = conversation_handler.session_manager.get_session(user_id)
    
    # Only show welcome if user is idle (not in middle of conversation)
    if session.state.value == "idle":
        await start_command(update, context)
    else:
        # User is in conversation, handle normally
        await conversation_handler.handle_message(update, context)

def main():
    """Main function"""
    # Initialize Google Docs
    conversation_handler.docs_handler.init_document()
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Add callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", conversation_handler.show_status))
    application.add_handler(CommandHandler("cancel", conversation_handler.cancel_conversation))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handle all text messages - welcome new users or continue conversation
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_new_users)
    )
    
    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    
    # Start bot
    print("🤖 Bot Step-by-Step RLEGS dengan Inline Buttons berjalan...")
    print("📝 User flow: Menu Buttons → Input Data → Save")
    print("🔘 Features: Inline Keyboards, Auto Welcome, Status Tracking")
    print("📊 Commands: /start, /status, /cancel, /help")
    
    application.run_polling()

if __name__ == '__main__':
    main()
