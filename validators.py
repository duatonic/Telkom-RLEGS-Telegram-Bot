import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataValidator:
    """Complete validator untuk setiap step input dengan semua method yang diperlukan"""
    
    @staticmethod
    def validate_kode_sa(kode):
        """Validasi Kode SA"""
        if not kode:
            return False, "Kode SA tidak boleh kosong"
            
        kode = kode.strip().upper()
        
        logger.info(f"Kode SA validated: {kode}")
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
        
        logger.info(f"Nama validated: {nama}")
        return True, nama
    
    @staticmethod
    def validate_telepon(telepon):
        """Validasi No. Telepon """
        if not telepon:
            return False, "Nomor telepon tidak boleh kosong"
        
        # Remove all non-digits first untuk checking
        clean_phone = re.sub(r'\D', '', telepon)
        original = telepon.strip()
        
        # Indonesian phone patterns dengan prefix yang valid
        patterns = [
            r'^08[1-9]\d{7,10}$',      # 08xx format (081x, 082x, dst - bukan 080x)
            r'^628[1-9]\d{7,10}$',     # 628xx format  
            r'^\+628[1-9]\d{7,10}$'    # +628xx format
        ]
        
        # Check original format first (dengan spasi dan dash dihilangkan)
        clean_original = original.replace(' ', '').replace('-', '')
        for pattern in patterns:
            if re.match(pattern, clean_original):
                logger.info(f"Phone validated (original format): {original}")
                return True, original
        
        # Auto-format hanya jika nomor dimulai dengan digit yang valid untuk Indonesia
        if len(clean_phone) >= 10:
            # Jika dimulai dengan 8, tambahkan 0 di depan (misal: 81234567890 -> 081234567890)
            if clean_phone.startswith('8') and clean_phone[1] in '123456789':
                formatted = '0' + clean_phone
                # Validasi ulang dengan pattern
                for pattern in patterns:
                    if re.match(pattern, formatted):
                        logger.info(f"Phone validated (auto-formatted): {formatted}")
                        return True, formatted
            
            # Jika sudah dimulai dengan 08, 628, cek apakah valid
            elif clean_phone.startswith('08') or clean_phone.startswith('628'):
                for pattern in patterns:
                    if re.match(pattern, clean_phone):
                        logger.info(f"Phone validated (clean): {clean_phone}")
                        return True, clean_phone
        
        return False, "Format nomor telepon tidak valid. Contoh: 081234567890, +6281234567890"
    
    @staticmethod
    def validate_witel(witel):
        """Validasi Witel - untuk fallback jika diperlukan"""
        if not witel:
            return False, "Witel tidak boleh kosong"
            
        witel = witel.strip()
        
        valid_witels = [
            'Bali', 'Jatim Barat', 'Jatim Timur', 'Nusa Tenggara',
            'Semarang Jateng', 'Solo Jateng Timur', 'Suramadu', 'Yogya Jateng Selatan'
        ]
        
        if witel in valid_witels:
            logger.info(f"Witel validated: {witel}")
            return True, witel
        
        return False, f"Witel tidak valid. Pilihan: {', '.join(valid_witels)}"
    
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
        
        logger.info(f"Telda validated: {telda}")
        return True, telda
    
    @staticmethod
    def validate_tanggal(tanggal):
        """Validasi Tanggal dengan format DD/MM/YYYY, DD-MM-YYYY, atau DD MM YYYY"""
        if not tanggal:
            return False, "Tanggal tidak boleh kosong"
            
        tanggal = tanggal.strip()
        
        # Multiple date patterns
        date_patterns = [
            r'^(\d{1,2})/(\d{1,2})/(\d{4})$',    # DD/MM/YYYY
            r'^(\d{1,2})-(\d{1,2})-(\d{4})$',    # DD-MM-YYYY  
            r'^(\d{1,2})\s+(\d{1,2})\s+(\d{4})$' # DD MM YYYY (satu atau lebih spasi)
        ]
        
        day = month = year = None
        matched_format = None
        
        # Try each pattern
        for i, pattern in enumerate(date_patterns):
            match = re.match(pattern, tanggal)
            if match:
                day, month, year = map(int, match.groups())
                matched_format = ['DD/MM/YYYY', 'DD-MM-YYYY', 'DD MM YYYY'][i]
                break
        
        if not matched_format:
            return False, "Format tanggal tidak valid. Gunakan format DD/MM/YYYY, DD-MM-YYYY, atau DD MM YYYY (contoh: 15/08/2025, 15-08-2025, 15 08 2025)"
        
        # Additional date validation
        try:
            # Check basic ranges
            if not (1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2030):
                return False, "Tanggal tidak valid. Pastikan tanggal, bulan, dan tahun dalam rentang yang benar"
            
            # Try to create datetime object for more thorough validation
            datetime(year, month, day)
            
            # Normalize to DD/MM/YYYY format untuk konsistensi output
            normalized_date = f"{day:02d}/{month:02d}/{year}"
            
            logger.info(f"Tanggal validated: {tanggal} -> normalized: {normalized_date}")
            return True, normalized_date
            
        except ValueError as e:
            return False, f"Tanggal tidak valid: {str(e)}"
    
    @staticmethod
    def validate_kategori(kategori):
        """Validasi Kategori Pelanggan"""
        if not kategori or not kategori.strip():
            return False, "Kategori tidak boleh kosong"
        
        kategori = kategori.strip()
        
        valid_categories = [
            'Kawasan Industri',
            'Desa', 
            'Puskesmas',
            'Kecamatan'
        ]
        
        if kategori in valid_categories:
            logger.info(f"Kategori validated: {kategori}")
            return True, kategori
        
        # Case insensitive fallback
        kategori_lower = kategori.lower()
        for cat in valid_categories:
            if cat.lower() == kategori_lower:
                logger.info(f"Kategori validated (case corrected): {cat}")
                return True, cat
        
        return False, f"Kategori tidak valid. Pilihan: {', '.join(valid_categories)}"
    
    @staticmethod
    def validate_kegiatan(kegiatan):
        """Validasi Kegiatan"""
        if not kegiatan or not kegiatan.strip():
            return False, "Kegiatan tidak boleh kosong"
        
        kegiatan = kegiatan.strip()
        
        valid_kegiatan = ['Visit', 'Dealing']
        
        if kegiatan in valid_kegiatan:
            logger.info(f"Kegiatan validated: {kegiatan}")
            return True, kegiatan
        
        # Case insensitive fallback
        kegiatan_lower = kegiatan.lower()
        for keg in valid_kegiatan:
            if keg.lower() == kegiatan_lower:
                logger.info(f"Kegiatan validated (case corrected): {keg}")
                return True, keg
        
        return False, f"Kegiatan tidak valid. Pilihan: {', '.join(valid_kegiatan)}"
    
    @staticmethod
    def validate_tenant(tenant):
        """Validasi Tenant"""
        if not tenant:
            return False, "Tenant tidak boleh kosong"
            
        tenant = tenant.strip().title()  # Clean and format
        
        if len(tenant) < 3:
            return False, "Nama Tenant terlalu pendek (minimal 3 karakter)"
        
        if len(tenant) > 50:
            return False, "Nama Tenant terlalu panjang (maksimal 50 karakter)"
        
        # Allow letters, spaces, and some common characters
        if not re.match(r"^[a-zA-Z\s\.\-]+$", tenant):
            return False, "Tenant hanya boleh mengandung huruf, spasi, titik, dan tanda hubung"
        
        logger.info(f"Tenant validated: {tenant}")
        return True, tenant
    
    @staticmethod
    def validate_layanan(layanan):
        """Validasi Tipe Layanan"""
        if not layanan or not layanan.strip():
            return False, "Tipe Layanan tidak boleh kosong"
        
        layanan = layanan.strip()
        
        valid_layanan = ['Indihome', 'Indibiz', 'Kompetitor']
        
        if layanan in valid_layanan:
            logger.info(f"Layanan validated: {layanan}")
            return True, layanan
        
        # Case insensitive fallback
        layanan_lower = layanan.lower()
        for lay in valid_layanan:
            if lay.lower() == layanan_lower:
                logger.info(f"Layanan validated (case corrected): {lay}")
                return True, lay
        
        return False, f"Tipe Layanan tidak valid. Pilihan: {', '.join(valid_layanan)}"
    
    @staticmethod
    def validate_paket(paket):
        """Validasi Paket Dealing"""
        if not paket or not paket.strip():
            return False, "Paket Dealing tidak boleh kosong"
        
        paket = paket.strip()
        
        valid_paket = ['50 Mbps', '75 Mbps', '100 Mbps', '> 100 Mbps']
        
        if paket in valid_paket:
            logger.info(f"Paket validated: {paket}")
            return True, paket
        
        # Case insensitive fallback
        paket_lower = paket.lower()
        for pak in valid_paket:
            if pak.lower() == paket_lower:
                logger.info(f"Paket validated (case corrected): {pak}")
                return True, pak
        
        return False, f"Paket Dealing tidak valid. Pilihan: {', '.join(valid_paket)}"
    
    @staticmethod
    def validate_tarif(tarif):
        """Validasi Tarif Layanan"""
        if not tarif or not tarif.strip():
            return False, "Tarif Layanan tidak boleh kosong"
        
        tarif = tarif.strip()
        
        valid_tarif = [
            '< Rp 200.000',
            'Rp 200.000 - Rp 350.000',
            '> Rp 500.000'
        ]
        
        if tarif in valid_tarif:
            logger.info(f"Tarif validated: {tarif}")
            return True, tarif
        
        return False, f"Tarif Layanan tidak valid. Pilihan: {', '.join(valid_tarif)}"
    
    @staticmethod
    def validate_nama_pic(nama_pic):
        """Validasi Nama PIC (Person In Charge) Pelanggan"""
        if not nama_pic:
            return False, "Nama PIC Pelanggan tidak boleh kosong"
            
        nama_pic = nama_pic.strip().title()  # Capitalize each word
        
        if len(nama_pic) < 2:
            return False, "Nama PIC terlalu pendek (minimal 2 karakter)"
        
        if len(nama_pic) > 50:
            return False, "Nama PIC terlalu panjang (maksimal 50 karakter)"
        
        # Only letters, spaces, dots, and apostrophes
        if not re.match(r"^[a-zA-Z\s\.']+$", nama_pic):
            return False, "Nama PIC hanya boleh mengandung huruf, spasi, titik, dan tanda petik"
        
        logger.info(f"Nama PIC validated: {nama_pic}")
        return True, nama_pic
    
    @staticmethod
    def validate_jabatan_pic(jabatan_pic):
        """Validasi Jabatan PIC (Person In Charge)"""
        if not jabatan_pic:
            return False, "Jabatan PIC tidak boleh kosong"
            
        jabatan_pic = jabatan_pic.strip().title()  # Capitalize each word
        
        if len(jabatan_pic) < 2:
            return False, "Jabatan PIC terlalu pendek (minimal 2 karakter)"
        
        if len(jabatan_pic) > 50:
            return False, "Jabatan PIC terlalu panjang (maksimal 50 karakter)"
        
        # Allow letters, spaces, dots, hyphens, and parentheses for job titles
        if not re.match(r"^[a-zA-Z\s\.\-\(\)]+$", jabatan_pic):
            return False, "Jabatan PIC hanya boleh mengandung huruf, spasi, titik, tanda hubung, dan kurung"
        
        logger.info(f"Jabatan PIC validated: {jabatan_pic}")
        return True, jabatan_pic
    
    @staticmethod
    def validate_telepon_pic(telepon_pic):
        """Validasi Nomor HP PIC """
        if not telepon_pic:
            return False, "Nomor HP PIC tidak boleh kosong"
            
        # Remove all non-digits first untuk checking
        clean_phone = re.sub(r'\D', '', telepon_pic)
        original = telepon_pic.strip()
        
        # Indonesian phone patterns dengan prefix yang valid
        patterns = [
            r'^08[1-9]\d{7,10}$',      # 08xx format (081x, 082x, dst - bukan 080x)
            r'^628[1-9]\d{7,10}$',     # 628xx format  
            r'^\+628[1-9]\d{7,10}$'    # +628xx format
        ]
        
        # Check original format first (dengan spasi dan dash dihilangkan)
        clean_original = original.replace(' ', '').replace('-', '')
        for pattern in patterns:
            if re.match(pattern, clean_original):
                logger.info(f"Phone PIC validated (original format): {original}")
                return True, original
        
        # Auto-format hanya jika nomor dimulai dengan digit yang valid untuk Indonesia
        if len(clean_phone) >= 10:
            # Jika dimulai dengan 8, tambahkan 0 di depan (misal: 81234567890 -> 081234567890)
            if clean_phone.startswith('8') and clean_phone[1] in '123456789':
                formatted = '0' + clean_phone
                # Validasi ulang dengan pattern
                for pattern in patterns:
                    if re.match(pattern, formatted):
                        logger.info(f"Phone PIC validated (auto-formatted): {formatted}")
                        return True, formatted
            
            # Jika sudah dimulai dengan 08, 628, cek apakah valid
            elif clean_phone.startswith('08') or clean_phone.startswith('628'):
                for pattern in patterns:
                    if re.match(pattern, clean_phone):
                        logger.info(f"Phone PIC validated (clean): {clean_phone}")
                        return True, clean_phone
        
        return False, "Format nomor HP PIC tidak valid. Contoh: 081234567890, +6281234567890"
    
    @staticmethod
    def validate_bundling(bundling):
        """Validasi Deal Bundling"""
        if not bundling or not bundling.strip():
            return False, "Deal Bundling tidak boleh kosong"
        
        bundling = bundling.strip()
        
        valid_bundling = [
            '1P Internet Only',
            '2P Internet + TV',
            '2P Internet + Telepon',
            '3P Internet + TV + Telepon'
        ]
        
        if bundling in valid_bundling:
            logger.info(f"Bundling validated: {bundling}")
            return True, bundling
        
        return False, f"Deal Bundling tidak valid. Pilihan: {', '.join(valid_bundling)}"
    
    @staticmethod
    def validate_all_data(data):
        """Validasi semua data sekaligus untuk final check"""
        errors = []
        validated_data = {}
        
        # Required fields dan validator mapping
        field_validators = {
            'kode_sa': DataValidator.validate_kode_sa,
            'nama': DataValidator.validate_nama,
            'no_telp': DataValidator.validate_telepon,
            'witel': DataValidator.validate_witel,
            'telda': DataValidator.validate_telda,
            'tanggal': DataValidator.validate_tanggal,
            'kategori': DataValidator.validate_kategori,
            'kegiatan': DataValidator.validate_kegiatan,
            'layanan': DataValidator.validate_layanan,
            'tarif': DataValidator.validate_tarif,
            'nama_pic': DataValidator.validate_nama_pic,
            'jabatan_pic': DataValidator.validate_jabatan_pic,
            'telepon_pic': DataValidator.validate_telepon_pic
        }
        
        # Validate each field
        for field, validator in field_validators.items():
            value = data.get(field)
            
            if not value:
                errors.append(f"{field} tidak boleh kosong")
                continue
            
            is_valid, result = validator(value)
            
            if is_valid:
                validated_data[field] = result
            else:
                errors.append(f"{field}: {result}")
        
        if errors:
            logger.warning(f"Validation errors: {errors}")
            return False, errors
        
        logger.info("All data validated successfully")
        return True, validated_data
    
    @staticmethod
    def get_field_label(field_name):
        """Get human-readable label for field names"""
        field_labels = {
            'kode_sa': 'Kode SA',
            'nama': 'Nama Lengkap',
            'no_telp': 'No. Telepon',
            'witel': 'Witel',
            'telda': 'Telkom Daerah',
            'tanggal': 'Tanggal Visit',
            'kategori': 'Kategori Pelanggan',
            'kegiatan': 'Kegiatan',
            'layanan': 'Tipe Layanan',
            'tarif': 'Tarif Layanan',
            'nama_pic': 'Nama PIC Pelanggan',
            'jabatan_pic': 'Jabatan PIC',
            'telepon_pic': 'Nomor HP PIC'
        }
        
        return field_labels.get(field_name, field_name.replace('_', ' ').title())
    
    @staticmethod
    def clean_phone_display(phone):
        """Clean phone number for better display"""
        if not phone:
            return phone
            
        # Remove extra spaces and format nicely
        clean = phone.strip()
        
        # Format Indonesian numbers nicely
        if clean.startswith('08'):
            # Format: 0812-3456-7890
            if len(clean) >= 11:
                return f"{clean[:4]}-{clean[4:8]}-{clean[8:]}"
        elif clean.startswith('+628'):
            # Format: +62 812-3456-7890
            if len(clean) >= 14:
                return f"+62 {clean[3:6]}-{clean[6:10]}-{clean[10:]}"
        elif clean.startswith('628'):
            # Format: 628 12-3456-7890
            if len(clean) >= 13:
                return f"628 {clean[3:5]}-{clean[5:9]}-{clean[9:]}"
                
        return clean
    
    @staticmethod
    def get_validation_summary():
        """Get summary of all validation rules"""
        return {
            "kode_sa": "Format: SA + 3-6 digit (SA001, SA1234)",
            "nama": "3-50 karakter, hanya huruf dan spasi",
            "no_telp": "Format Indonesia (08xx, 628xx, +628xx)",
            "witel": "Pilihan: 8 witel tersedia",
            "telda": "3-50 karakter, huruf dan tanda baca dasar",
            "tanggal": "Format DD/MM/YYYY (15/08/2025)",
            "kategori": "Pilihan: Kawasan Industri, Desa, Puskesmas, Kecamatan",
            "kegiatan": "Pilihan: Visit, Dealing",
            "layanan": "Pilihan: Indihome, Indibiz, Kompetitor",
            "tarif": "Pilihan: < Rp 200.000, Rp 200.000 - Rp 350.000, > Rp 500.000",
            "nama_pic": "2-50 karakter, hanya huruf dan spasi",
            "jabatan_pic": "2-50 karakter, huruf dan tanda baca dasar",
            "telepon_pic": "Format Indonesia (sama dengan no_telp)"
        }