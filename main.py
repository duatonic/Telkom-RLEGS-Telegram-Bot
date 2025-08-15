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
        self.witel = None
        self.telda = None

    def __str__(self):
        return f"{self.nama}, {self.telepon}, {self.witel}, {self.telda}"
    
    def _next_empty(self):
        for field in ['nama', 'telepon', 'witel', 'telda']:
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with inline keyboard"""
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with inline keyboard"""
    help_text = """
🤖 **Bot Rekap Data RLEGS - Panduan**

📝 **Commands:**
- `/start` - Menu utama bot
- `/status` - Lihat progress saat ini
- `/cancel` - Batalkan input yang sedang berjalan
- `/help` - Tampilkan panduan ini

🔄 **Alur Input (8 Step):**
1️⃣ Kode SA (contoh: SA001)
2️⃣ Nama Lengkap
3️⃣ No. Telepon
4️⃣ Witel
5️⃣ Telkom Daerah
6️⃣ Tanggal
7️⃣ Kategori Pelanggan
8️⃣ Kegiatan

⚡ **Tips:**
- Bot akan memandu step by step
- Data otomatis divalidasi
- Bisa batalkan kapan saja dengan /cancel
- Gunakan button untuk navigasi yang mudah

💾 **Data otomatis tersimpan ke Google Docs setelah lengkap**
    """
    
    # Create back button
    keyboard = [
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

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
        
        await update.message.reply_text(f"Masukkan data {form._next_empty()}", parse_mode='Markdown')

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
    
    # Handle Witel selection buttons 
    if query.data.startswith('witel_'):
        await conversation_handler.handle_witel_selection(update, context)
        return
    
    # Handle Kategori selection buttons 
    if query.data.startswith('kategori_'):
        await conversation_handler.handle_kategori_selection(update, context)
        return
    
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

🔄 **Alur Input (8 Step):**
1️⃣ Kode SA (contoh: SA001)
2️⃣ Nama Lengkap
3️⃣ No. Telepon  
4️⃣ Witel
5️⃣ Telkom Daerah
6️⃣ Tanggal
7️⃣ Kategori Pelanggan
8️⃣ Kegiatan

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
**Halo {user_name}!** 👋

🤖**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

Lengkapi setiap pertanyaan yang diberikan dan data akan otomatis tersimpan.
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
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')],
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
    
    # Add callback query handler for inline keyboards - INI PENTING!
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
    print("📝 User flow: Menu Buttons → Input Data (8 steps) → Save")
    print("🔘 Features: Inline Keyboards, Auto Welcome, Status Tracking")
    print("📊 Commands: /start, /status, /cancel, /help")
    
    application.run_polling()

if __name__ == '__main__':
    main()