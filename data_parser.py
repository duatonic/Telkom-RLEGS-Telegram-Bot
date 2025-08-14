import re
import logging

logger = logging.getLogger(__name__)

class DataParser:
    @staticmethod
    def parse_data(text):
        """
        Parse text input menjadi nama, no_telp, alamat
        Mendukung berbagai format input
        """
        text = text.strip()
        
        # Format 1: Comma separated
        if ',' in text:
            parts = [part.strip() for part in text.split(',')]
            if len(parts) >= 3:
                return {
                    'nama': parts[0],
                    'no_telp': parts[1],
                    'alamat': ', '.join(parts[2:])  # Gabungkan sisa sebagai alamat
                }
        
        # Format 2: Pipe separated  
        elif '|' in text:
            parts = [part.strip() for part in text.split('|')]
            if len(parts) >= 3:
                return {
                    'nama': parts[0],
                    'no_telp': parts[1],
                    'alamat': ' | '.join(parts[2:]).strip()  # Fix: tambah spasi
                }
        
        # Format 3: New line separated
        elif '\n' in text:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) >= 3:
                return {
                    'nama': lines[0],
                    'no_telp': lines[1],
                    'alamat': ' '.join(lines[2:])  # Gabungkan sisa sebagai alamat
                }
        
        # Format 4: Space separated (minimal parsing)
        else:
            # Coba detect nomor telepon dengan regex - Pattern lebih ketat
            phone_pattern = r'(\+?62[\d\s\-\(\)]{9,}|0[\d\s\-\(\)]{9,})'
            phone_match = re.search(phone_pattern, text)
            
            if phone_match:
                phone = phone_match.group(1).strip()
                # Ambil text sebelum nomor sebagai nama
                name_part = text[:phone_match.start()].strip()
                # Ambil text setelah nomor sebagai alamat  
                address_part = text[phone_match.end():].strip()
                
                if name_part and address_part:
                    return {
                        'nama': name_part,
                        'no_telp': phone,
                        'alamat': address_part
                    }
        
        # Jika gagal parsing
        return None
    
    @staticmethod
    def validate_data(data):
        """Validasi data yang sudah di-parse"""
        if not data:
            return False, "Format data tidak valid"
        
        nama = data.get('nama', '').strip()
        no_telp = data.get('no_telp', '').strip()
        alamat = data.get('alamat', '').strip()
        
        if len(nama) < 2:
            return False, "Nama terlalu pendek (minimal 2 karakter)"
        
        if len(no_telp) < 10:
            return False, "Nomor telepon terlalu pendek (minimal 10 karakter)"
        
        if not any(char.isdigit() for char in no_telp):
            return False, "Nomor telepon harus mengandung angka"
        
        if len(alamat) < 10:
            return False, "Alamat terlalu pendek (minimal 10 karakter)"
        
        return True, "Valid"
    
    @staticmethod
    def format_example():
        """Contoh format yang didukung"""
        return """
            📝 **Format yang didukung:**

            **1. Dengan koma (,):**
            `Nama, NoTelp, Alamat`
            Contoh: `John Doe, 081234567890, Jl. Sudirman No. 1 Jakarta Pusat`

            **2. Dengan garis (|):**
            `Nama | NoTelp | Alamat` 
            Contoh: `John Doe | 081234567890 | Jl. Sudirman No. 1 Jakarta`

            **3. Baris baru:**
            ```
            Nama
            NoTelp  
            Alamat
            ```
            Contoh:
            ```
            John Doe
            081234567890
            Jl. Sudirman No. 1 Jakarta Pusat
            ```

            **4. Spasi (auto-detect):**
            `Nama NoTelp Alamat`
            Contoh: `John Doe 081234567890 Jl. Sudirman Jakarta`

            **Tips:**
            • Nama minimal 2 karakter
            • Nomor telepon minimal 10 karakter
            • Alamat minimal 10 karakter
            • Gunakan format yang paling nyaman untuk Anda!
        """
    
    @staticmethod
    def clean_phone_number(phone):
        """Bersihkan dan standardisasi nomor telepon"""
        if not phone:
            return phone
            
        # Hapus spasi, tanda kurung, dan dash
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Konversi format Indonesia
        if cleaned.startswith('62'):
            cleaned = '+' + cleaned
        elif cleaned.startswith('0'):
            cleaned = '+62' + cleaned[1:]
        elif not cleaned.startswith('+'):
            # Jika tidak ada kode negara, assume Indonesia
            cleaned = '+62' + cleaned
            
        return cleaned
    
    @staticmethod
    def test_parser():
        """Test function untuk debug parsing"""
        test_cases = [
            "John Doe, 081234567890, Jl. Sudirman No. 1 Jakarta",
            "Jane Smith | 081987654321 | Jl. Thamrin Jakarta",
            "Ahmad Budi\n081555123456\nJl. Gatot Subroto Jakarta",
            "Siti Nurhaliza 081333444555 Jl. Kemang Raya Jakarta Selatan",
            "Budi, +62 813-5555-1234, Komplex Permata Hijau, Jakarta Barat",
        ]
        
        print("🧪 Testing DataParser...")
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test}")
            result = DataParser.parse_data(test)
            if result:
                is_valid, msg = DataParser.validate_data(result)
                print(f"✅ Parsed: {result}")
                print(f"Valid: {is_valid} - {msg}")
            else:
                print("❌ Failed to parse")

# Test jika file dijalankan langsung
if __name__ == "__main__":
    DataParser.test_parser()