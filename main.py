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
👋 Halo *{user_name}*!

Selamat datang di *Rekapitulasi Data 8 Fishing Spot RLEGS III*

📍 _Pendataan Visit Kawasan Industri, Desa, dan Puskesmas_
"""

    webapp = WebAppInfo(url=config.WEBAPP_URL)
    
    keyboard = [
        [InlineKeyboardButton("Mulai Input Data", web_app=webapp)],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ========================
# CANCEL COMMAND
# ========================
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the ongoing data entry conversation."""
    user_id = update.effective_user.id
    session = conversation_handler.session_manager.get_session(user_id)

    if session.state.value != "idle":
        logger.info(f"User {user_id} has cancelled the conversation.")
        conversation_handler.session_manager.reset_session(user_id)
        
        keyboard = [[InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ *Proses input data telah dibatalkan.*\n\nPilih opsi di bawah untuk melanjutkan:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await start_command(update, context)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()  # hilangkan loading circle di Telegram

    if query.data == "start_chat_input":
        # langsung mulai alur input manual
        await conversation_handler.handle_interactions(update, context)

    elif query.data == "back_to_menu":
        # kembali ke menu utama
        await start_command_callback(query, context)

    # kalau mau tambahin callback lain (misal show_help) bisa di sini

# ========================
# START COMMAND CALLBACK
# ========================
async def start_command_callback(query, context):
    """Start command for callback queries"""
    user_name = query.from_user.first_name
    
    welcome_text = f"""
👋 Halo *{user_name}*!

Selamat datang di *Rekapitulasi Data 8 Fishing Spot RLEGS III*

📍 _Pendataan Visit Kawasan Industri, Desa, dan Puskesmas_

"""
    webapp = WebAppInfo(url=config.WEBAPP_URL)
    
    keyboard = [
        [InlineKeyboardButton("Mulai Input Data", web_app=webapp)],
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

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message for users who just start chatting (any text message when idle)"""
    user_id = update.effective_user.id
    session = conversation_handler.session_manager.get_session(user_id)
    
    if session.state.value == "idle":
        await start_command(update, context)
    else:
        await conversation_handler.handle_interactions(update, context)

def main():
    """Main function"""
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Handler untuk Web App data
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Handler untuk callback buttons
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern='^(start_chat_input|back_to_menu|show_help)$'))
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Image handler
    application.add_handler(MessageHandler(filters.PHOTO, conversation_handler.handle_interactions))

    # Handle all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, conversation_handler.handle_interactions))

    print("🤖 Bot RLEGS dengan Mini App Integration berjalan...")
    print("📱 Mini App URL:", config.WEBAPP_URL)
    print("📝 User flow: Menu → Mini App Form / Chat Input → Save")
    print("🔘 Features: Web App Integration, Inline Keyboards, Status Tracking")
    print("📊 Commands: /start, /cancel")
    
    application.run_polling()

if __name__ == '__main__':
    main()
