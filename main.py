import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from conversation_handlers import ConversationHandler
import config
from io import BytesIO

user_forms = {}

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

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Add callback query handler for inline keyboards - INI PENTING!
    # application.add_handler(CallbackQueryHandler(conversation_handler.button_callbacks))

    # TEMP
    application.add_handler(CallbackQueryHandler(conversation_handler.handle_interactions))
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    #application.add_handler(CommandHandler("status", conversation_handler.show_status))
    #application.add_handler(CommandHandler("cancel", conversation_handler.cancel_conversation))
    application.add_handler(CommandHandler("help", help_command))
    
    # Image handler
    #application.add_handler(MessageHandler(filters.PHOTO, conversation_handler.handle_image))

    #TEMP
    application.add_handler(MessageHandler(filters.PHOTO, conversation_handler.handle_interactions))

    # Handle all text messages - welcome new users or continue conversation
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # TEMP
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, conversation_handler.handle_interactions))

    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    
    # Start bot
    print("🤖 Bot Step-by-Step RLEGS dengan Inline Buttons berjalan...")
    print("📝 User flow: Menu Buttons → Input Data (15 steps) → Save")
    print("🔘 Features: Inline Keyboards, Auto Welcome, Status Tracking")
    print("📊 Commands: /start, /status, /cancel, /help")
    
    application.run_polling()

if __name__ == '__main__':
    main()
