import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from data_parser import DataParser
from google_docs_simple import SimpleGoogleDocs
import config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize
parser = DataParser()
docs_handler = SimpleGoogleDocs()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /start"""
    user = update.effective_user
    welcome_message = f"""
🤖 **Hallo {user.first_name}!**

Selamat Datang di Bot Rekap Data RLEGS!
Data yang kamu kirimkan akan kami rekap menggunakan Google Docs

**Cara pakai:**
Kirim data dalam 1 pesan dengan format:
`Nama, NoTelp, Alamat`

Contoh:
`John Doe, 081234567890, Jl. Sudirman No. 1 Jakarta`

Gunakan /help untuk melihat format lain yang didukung.
    """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /help"""
    help_text = parser.format_example()
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def process_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process data dari user message"""
    try:
        user_text = update.message.text
        user_name = update.effective_user.first_name
        
        # Parse data
        parsed_data = parser.parse_data(user_text)
        
        if not parsed_data:
            await update.message.reply_text(
                "❌ **Format tidak valid!**\n\n"
                "Gunakan /help untuk melihat format yang didukung.\n\n"
                "Contoh: `John Doe, 081234567890, Jl. Sudirman Jakarta`",
                parse_mode='Markdown'
            )
            return
        
        # Validasi data
        is_valid, message = parser.validate_data(parsed_data)
        
        if not is_valid:
            await update.message.reply_text(
                f"❌ **Validasi gagal:** {message}\n\n"
                "Gunakan /help untuk melihat format yang benar.",
                parse_mode='Markdown'
            )
            return
        
        # Konfirmasi data ke user
        nama = parsed_data['nama']
        no_telp = parsed_data['no_telp']
        alamat = parsed_data['alamat']
        
        konfirmasi = f"""
✅ **Data berhasil di-parse:**

- **Nama:** {nama}
- **No. Telepon:** {no_telp}  
- **Alamat:** {alamat}

⏳ Menyimpan ke Google Docs...
        """
        
        # Kirim konfirmasi
        status_msg = await update.message.reply_text(konfirmasi, parse_mode='Markdown')
        
        # Simpan ke Google Docs
        success, result_message = docs_handler.add_data(nama, no_telp, alamat)
        
        if success:
            # Update pesan dengan status sukses
            final_message = f"""
✅ **Data berhasil disimpan ke Google Docs!**

- **Nama:** {nama}
- **No. Telepon:** {no_telp}
- **Alamat:** {alamat}
- **Timestamp:** Otomatis ditambahkan

Kirim data lain untuk melanjutkan.
            """
            
            await status_msg.edit_text(final_message, parse_mode='Markdown')
            
            # Log sukses
            logger.info(f"✅ Data saved - User: {user_name}, Nama: {nama}")
            
        else:
            # Update dengan error message
            error_message = f"""
❌ **Gagal menyimpan data!**

Error: {result_message}

Silakan coba lagi atau hubungi admin.
            """
            
            await status_msg.edit_text(error_message, parse_mode='Markdown')
            logger.error(f"❌ Save failed - User: {user_name}, Error: {result_message}")
    
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        await update.message.reply_text(
            "❌ **Terjadi kesalahan sistem.**\n\nSilakan coba lagi nanti.",
            parse_mode='Markdown'
        )

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle command yang tidak dikenali"""
    await update.message.reply_text(
        "❓ Command tidak dikenal.\n\n"
        "Gunakan /start untuk memulai atau langsung kirim data Anda."
    )

def main():
    """Main function"""
    # Inisialisasi dokumen Google Docs
    docs_handler.init_document()
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Handler untuk semua text message (kecuali command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_data))
    
    # Handler untuk unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
    
    # Run bot
    print("🤖 Bot Simple Google Docs berjalan...")
    print("📝 User bisa langsung kirim: Nama, NoTelp, Alamat")
    application.run_polling()

if __name__ == '__main__':
    main()