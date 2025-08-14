import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from data_parser import DataParser
from google_docs_simple import SimpleGoogleDocs
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

# Initialize
parser = DataParser()
docs_handler = SimpleGoogleDocs()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /start"""
    chat_id = update.message.chat_id
    user = update.effective_user
    user_forms[chat_id] = InputData()
    form = user_forms[chat_id]
    input_field = form._next_empty() or 'nama'
    
    welcome_message = f"""
        🤖 **Halo {user.first_name}!**

        Selamat Datang di Bot Rekap Data RLEGS!
        Data yang kamu kirimkan akan kami rekap menggunakan Google Docs

        **Cara pakai:**
        Kirim data dalam 1 pesan dengan format:
        `Nama, NoTelp, Alamat`

        Contoh:
        `John Doe, 081234567890, Jl. Sudirman No. 1 Jakarta`

        Gunakan /help untuk melihat format lain yang didukung.
    """

    initial_message = f"""
        Masukkan data {input_field}:
    """
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    await update.message.reply_text(initial_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /help"""
    help_text = parser.format_example()
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def start_input_loop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'input_data' not in context.user_data:
        context.user_data['input_data'] = {
            'nama': None,
            'no_telp': None,
            'alamat': None,
            'step': 'nama'
        }

    data = context.user_data['input_data']

    if all(data[field] is not None for field in ['nama', 'no_telp', 'alamat']):
        await process_data(update, context)
        return
    
    if data['nama'] is None:
        await update.message.reply_text("🔍 **Masukkan Nama Anda:**")
        data['step'] = 'nama'
    elif data['no_telp'] is None:
        await update.message.reply_text("📞 **Masukkan Nomor Telepon Anda:**")
        data['step'] = 'no_telp'
    elif data['alamat'] is None:
        await update.message.reply_text("🏠 **Masukkan Alamat Anda:**")
        data['step'] = 'alamat'

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
