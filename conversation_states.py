from enum import Enum

class ConversationState(Enum):
    """States untuk conversation flow"""
    IDLE = "idle"
    WAITING_KODE_SA = "waiting_kode_sa"
    WAITING_NAMA = "waiting_nama"
    WAITING_TELEPON = "waiting_telepon"
    WAITING_WITEL = "waiting_witel"
    WAITING_TELDA = "waiting_telda"
    WAITING_TANGGAL = "waiting_tanggal"
    WAITING_KATEGORI = "waiting_kategori"
    WAITING_KEGIATAN = "waiting_kegiatan"
    WAITING_TENANT =    "waiting_tenant"
    WAITING_LAYANAN = "waiting_layanan"
    WAITING_TARIF = "waiting_tarif"
    WAITING_NAMA_PIC = "waiting_nama_pic"
    WAITING_JABATAN_PIC = "waiting_jabatan_pic"
    WAITING_TELEPON_PIC = "waiting_telepon_pic"
    WAITING_PAKET_DEAL = "waiting_paket_deal"
    WAITING_DEAL_BUNDLING = "waiting_deal_bundling"
    WAITING_FOTO_EVIDENCE = "waiting_foto_evidence"
    CANCELED = "canceled"
    COMPLETED = "completed"

class UserSession:
    """Class untuk menyimpan session data per user"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = ConversationState.IDLE
        self.data = {}
        self.history = []
        self.reset()

    def reset(self):
        """Reset session data"""
        self.state = ConversationState.IDLE
        self.data = {
            'kode_sa': None,
            'nama': None,
            'no_telp': None,
            'witel': None,
            'telda': None,
            'tanggal': None,
            'kategori': None,
            'kegiatan': None,
            'tenant': None,
            'layanan': None,
            'tarif': None,
            'nama_pic': None,
            'jabatan_pic': None,
            'telepon_pic': None,
            'paket_deal': None,
            'deal_bundling': None,
            'foto_evidence': None,
        }
    
    def set_state(self, new_state):
        """Update conversation state"""
        self.state = new_state
    
    def add_data(self, key, value):
        """Add data to session"""
        self.data[key] = value
    
    def is_complete(self):
        """Check if all required data collected"""
        return all(self.data.values())
    
    def get_progress(self):
        """Get current progress"""
        steps = [
            'kode_sa',
            'nama',
            'no_telp',
            'witel',
            'telda',
            'tanggal',
            'kategori',
            'kegiatan',
            'tenant',
            'layanan',
            'tarif',
            'nama_pic',
            'jabatan_pic',
            'telepon_pic',
            'paket_deal',
            'deal_bundling',
            'foto_evidence',
        ]
        completed = sum(1 for step in steps if self.data[step])
        return completed, len(steps)
