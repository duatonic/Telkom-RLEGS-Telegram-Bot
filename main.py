import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from miniapp_handler import MiniAppHandler
import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize mini app handler
miniapp_handler = MiniAppHandler()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - delegate to mini app handler"""
    await miniapp_handler.start_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command - delegate to mini app handler"""
    await miniapp_handler.help_command(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel command - redirect to start"""
    await start_command(update, context)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    
    if query.data == "back_to_menu":
        await miniapp_handler.handle_back_to_menu(update, context)
    else:
        # Handle any other callbacks or unknown ones
        await query.answer("Aksi tidak dikenali.")
        await miniapp_handler.handle_back_to_menu(update, context)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data from Web App"""
    await miniapp_handler.process_webapp_data(update, context)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message - redirect to start for mini app"""
    await miniapp_handler.handle_unknown_command(update, context)

async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await miniapp_handler.handle_unknown_command(update, context)

async def handle_photo_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages - not needed for mini app, redirect to start"""
    await update.message.reply_text(
        "📷 Foto harus diupload melalui form.\n\n"
        "Silakan gunakan tombol di bawah untuk membuka form:"
    )
    await miniapp_handler.start_command(update, context)

def main():
    """Main function"""
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Handler untuk Web App data (prioritas tertinggi)
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Handler untuk callback buttons
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    
    # Handle photo messages (redirect to form)
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))
    
    # Handle all other text messages (redirect to start)
    application.add_handler(MessageHandler(filters.TEXT, handle_text_messages))
    
    print("🤖 Bot RLEGS Mini App berjalan...")
    print("📱 Mini App URL:", config.WEBAPP_URL)
    print("📝 User flow: /start → Mini App Form → Submit → Success")
    print("🔘 Features: Web App Integration, Data Validation, Google Services")
    print("📊 Commands: /start, /help, /cancel")
    print("📋 Mode: Mini App Only (Manual input dihapus)")
    
    application.run_polling()

if __name__ == '__main__':
    main()