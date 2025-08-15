import re
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Validator untuk setiap step input"""
    
    @staticmethod
    def validate_kode_sa(kode):
        """Validasi Kode SA"""
        if not kode:
            return False, "Kode SA tidak boleh kosong"
            
        kode = kode.strip().upper()
        
        # Pattern: SA + 3-6 digit angka
        pattern = r'^SA\d{3,6}$'
        
        if not re.match(pattern, kode):
            return False, "Format Kode SA tidak valid. Gunakan format: SA001, SA1234, dll."
        
        return True, kode  # Return cleaned version
    
    @staticmethod
    def validate_nama(nama):
        """Validasi Nama Lengkap"""
        if not nama:
            return False, "Nama tidak boleh kosong"
            
        nama = nama.strip().title()  # Capitalize each word
        
        if len(nama) < 3:
            return False, "Nama terlalu pendek (minimal 3 karakter)"
        
        if len(nama) > 50:
            return False, "Nama terlalu panjang (maksimal 50 karakter)"
        
        # Only letters, spaces, dots, and apostrophes
        if not re.match(r"^[a-zA-Z\s\.']+$", nama):
            return False, "Nama hanya boleh mengandung huruf, spasi, titik, dan tanda petik"
        
        return True, nama
    
    @staticmethod
    def validate_telepon(telepon):
        """Validasi No. Telepon"""
        if not telepon:
            return False, "Nomor telepon tidak boleh kosong"
            
        # Remove all non-digits first untuk checking
        clean_phone = re.sub(r'\D', '', telepon)
        original = telepon.strip()
        
        # Indonesian phone patterns
        patterns = [
            r'^08\d{8,11}$',           # 08xx format
            r'^628\d{8,11}$',          # 628xx format  
            r'^\+628\d{8,11}$'         # +628xx format
        ]
        
        # Check original format first
        clean_original = original.replace(' ', '').replace('-', '')
        for pattern in patterns:
            if re.match(pattern, clean_original):
                return True, original
        
        # Auto-format if looks like Indonesian number
        if len(clean_phone) >= 10:
            if clean_phone.startswith('8'):
                formatted = '0' + clean_phone
                return True, formatted
            elif len(clean_phone) >= 10:
                return True, clean_phone
        
        return False, "Format nomor telepon tidak valid. Contoh: 081234567890, +6281234567890"
    
    @staticmethod
    def validate_witel(witel):
        """Validasi Witel - tidak diperlukan lagi karena menggunakan button selection"""
        if not witel:
            return False, "Witel tidak boleh kosong"
            
        witel = witel.strip()
        
        valid_witels = [
            'Bali', 'Jatim Barat', 'Jatim Timur', 'Nusa Tenggara',
            'Semarang Jateng', 'Solo Jateng Timur', 'Suramadu', 'Yogya Jateng Selatan'
        ]
        
        if witel in valid_witels:
            return True, witel
        
        return False, f"Witel tidak valid. Pilihan: {', '.join(valid_witels)}"
    
    @staticmethod
    def validate_kategori(category):
        """Validasi Kategori Pelanggan"""
        if not category or not category.strip():
            return False, "Kategori tidak boleh kosong"
        
        category = category.strip()
        
        valid_categories = {
            'kawasan industri': 'Kawasan Industri',
            'desa': 'Desa',
            'puskesmas': 'Puskesmas',
            'kecamatan': 'Kecamatan'
        }
        
        category_key = category.lower()
        
        if category in valid_categories:
            return True, category
        
        return False, f"Witel tidak valid. Pilihan: {', '.join(valid_categories)}"
    
    @staticmethod
    def validate_telda(telda):
        """Validasi Telkom Daerah"""
        if not telda:
            return False, "Telkom Daerah tidak boleh kosong"
            
        telda = telda.strip().title()  # Clean and format
        
        if len(telda) < 3:
            return False, "Nama Telkom Daerah terlalu pendek (minimal 3 karakter)"
        
        if len(telda) > 50:
            return False, "Nama Telkom Daerah terlalu panjang (maksimal 50 karakter)"
        
        # Allow letters, spaces, and some common characters
        if not re.match(r"^[a-zA-Z\s\.\-]+$", telda):
            return False, "Telkom Daerah hanya boleh mengandung huruf, spasi, titik, dan tanda hubung"
        
        return True, telda