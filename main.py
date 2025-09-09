import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from conversation_handlers import ConversationHandler
from miniapp_handler import MiniAppHandler
import config
from io import BytesIO

user_forms = {}

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize handlers
conversation_handler = ConversationHandler()
miniapp_handler = MiniAppHandler()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with Mini App and traditional options"""
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    session = conversation_handler.session_manager.get_session(user_id)
    
    if session.state.value != "idle":
        logger.info(f"User {user_id} used /start during an active conversation. Resetting state.")
        
        conversation_handler.session_manager.reset_session(user_id)
        
        await update.message.reply_text("Sesi input sebelumnya telah dibatalkan.")

    welcome_text = f"""
**Halo *{user_name}*!** 👋

**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

📍 *Pendataan Visit Kawasan Industri, Desa, dan Puskesmas*

Pilih metode input data:
"""
    
    # Mini App button with WebAppInfo
    webapp = WebAppInfo(url=config.WEBAPP_URL)
    
    keyboard = [
        [InlineKeyboardButton("📱 Buka Form (Recommended)", web_app=webapp)],
        [InlineKeyboardButton("💬 Input via Chat (Traditional)", callback_data='start_chat_input')],
        [InlineKeyboardButton("❓ Help", callback_data='show_help')]
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
🤖 *Panduan Bot Rekapitulasi*

📝 *Metode Input Data:*
• **Form (Recommended)** - Interface modern dengan form
• **Chat** - Input step-by-step via chat tradisional

📋 *Perintah:*
/start - Menu utama bot
/cancel - Batalkan input yang sedang berjalan
/help - Tampilkan panduan ini

🔄 *Data yang dikumpulkan:*
• Visit: 15 field data + foto evidence
• Dealing: 15 field data + foto evidence

📊 *Output:*
Otomatis tersimpan ke Google Sheets dengan foto di Google Drive
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

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the ongoing data entry conversation."""
    user_id = update.effective_user.id
    session = conversation_handler.session_manager.get_session(user_id)

    # Check if the user is currently in the middle of a conversation
    if session.state.value != "idle":
        logger.info(f"User {user_id} has cancelled the conversation.")
        
        # Reset the session to clear all stored data and the current state
        conversation_handler.session_manager.reset_session(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ *Proses input data telah dibatalkan.*\n\n"
            "Pilih opsi di bawah untuk melanjutkan:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await start_command(update, context)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()  # Answer the callback query to remove loading state
    
    # Handle different callback data
    if query.data == 'show_help':
        # Show help using the existing help function
        help_text = """
🤖 *Panduan Bot Rekapitulasi*

📝 *Metode Input Data:*
• **Form (Recommended)** - Interface modern dengan form
• **Chat** - Input step-by-step via chat tradisional

📋 *Perintah:*
/start - Menu utama bot
/cancel - Batalkan input yang sedang berjalan
/help - Tampilkan panduan ini

🔄 *Data yang dikumpulkan:*
• Visit: 15 field data + foto evidence
• Dealing: 15 field data + foto evidence

📊 *Output:*
Otomatis tersimpan ke Google Sheets dengan foto di Google Drive
    """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    elif query.data == 'back_to_menu':
        # Go back to main menu
        await start_command_callback(query, context)
        
    elif query.data == 'start_chat_input':
        # Forward to traditional conversation handler
        await conversation_handler.handle_interactions(update, context)

async def start_command_callback(query, context):
    """Start command for callback queries"""
    user_name = query.from_user.first_name
    
    welcome_text = f"""
**Halo *{user_name}*!** 👋

**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

📍 *Pendataan Visit Kawasan Industri, Desa, dan Puskesmas*

Pilih metode input data:
"""
    
    # Mini App button with WebAppInfo
    webapp = WebAppInfo(url=config.WEBAPP_URL)
    
    keyboard = [
        [InlineKeyboardButton("📱 Buka Form (Recommended)", web_app=webapp)],
        [InlineKeyboardButton("💬 Input via Chat (Traditional)", callback_data='start_chat_input')],
        [InlineKeyboardButton("❓ Help", callback_data='show_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data from Web App"""
    if update.message and update.message.web_app_data:
        await miniapp_handler.process_webapp_data(update, context)

async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands with helpful response"""
    keyboard = [
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')],
        [InlineKeyboardButton("❓ Help", callback_data='show_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "*Command tidak dikenal*\n\n"
        "Command yang dikenali sistem: \n"
        "/start \n"
        "/cancel \n"
        "/help \n\n"
        "Atau gunakan button di bawah untuk navigasi:",
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
        await conversation_handler.handle_interactions(update, context)


def main():
    """Main function"""
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # PENTING: Handler untuk Web App data
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Handler untuk callback buttons
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern='^(show_help|back_to_menu|start_chat_input)$'))
    
    # Handler untuk conversation (traditional chat input)
    application.add_handler(CallbackQueryHandler(conversation_handler.handle_interactions))
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Image handler for traditional chat
    application.add_handler(MessageHandler(filters.PHOTO, conversation_handler.handle_interactions))

    # Handle all text messages - welcome new users or continue conversation
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, conversation_handler.handle_interactions))

    # Handle unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    
    # Start bot
    print("🤖 Bot RLEGS dengan Mini App Integration berjalan...")
    print("📱 Mini App URL:", config.WEBAPP_URL)
    print("📝 User flow: Menu → Mini App Form / Chat Input → Save")
    print("🔘 Features: Web App Integration, Inline Keyboards, Status Tracking")
    print("📊 Commands: /start, /cancel, /help")
    
    application.run_polling()

if __name__ == '__main__':
    main()