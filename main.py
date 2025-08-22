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
**Halo *{user_name}*! ** 👋

**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

📍 *Pendataan Visit Kawasan Industri, Desa, dan Puskesmas*    
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
🤖 *Panduan Bot Rekapitulasi*

📝 *Perintah:*
/start - Menu utama bot
/cancel - Batalkan input yang sedang berjalan
/help - Tampilkan panduan ini
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

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()  # Answer the callback query to remove loading state
    
    # Handle different callback data
    if query.data == 'show_help':
        # Show help using the existing help function
        help_text = """
🤖 *Panduan Bot Rekapitulasi*

📝 *Perintah:*
/start - Menu utama bot
/cancel - Batalkan input yang sedang berjalan
/help - Tampilkan panduan ini
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
        user_name = update.effective_user.first_name
        welcome_text = f"""
**Halo *{user_name}*! ** 👋

**Selamat Datang di Rekapitulasi Data 8 Fishong Spot RLEGS III** 

📍 *Pendataan Visit Kawasan Industri, Desa, dan Puskesmas*    
"""
        
        keyboard = [
            [InlineKeyboardButton("Start", callback_data='start_input')],
            [InlineKeyboardButton("Help", callback_data='show_help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    elif query.data == 'start_input':
        # Forward to conversation handler untuk memulai input data
        await conversation_handler.handle_interactions(update, context)

async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands with helpful response"""
    keyboard = [
        [InlineKeyboardButton("🏠 Menu Utama", callback_data='back_to_menu')],
        [InlineKeyboardButton("Help", callback_data='show_help')]
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
        await conversation_handler.handle_message(update, context)


def main():
    """Main function"""
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # PENTING: Tambahkan callback handler untuk button interactions
    # Handler ini akan menangani semua button presses
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern='^(show_help|back_to_menu)$'))
    
    # Handler untuk conversation (start_input dan lainnya)
    application.add_handler(CallbackQueryHandler(conversation_handler.handle_interactions))
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Image handler
    application.add_handler(MessageHandler(filters.PHOTO, conversation_handler.handle_interactions))

    # Handle all text messages - welcome new users or continue conversation
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