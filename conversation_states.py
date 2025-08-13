from enum import Enum

class ConversationState(Enum):
    """States untuk conversation flow"""
    IDLE = "idle"
    WAITING_KODE_SA = "waiting_kode_sa"
    WAITING_NAMA = "waiting_nama"
    WAITING_TELEPON = "waiting_telepon"
    WAITING_ALAMAT = "waiting_alamat"
    COMPLETED = "completed"

class UserSession:
    """Class untuk menyimpan session data per user"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = ConversationState.IDLE
        self.data = {}
        self.reset()
    
    def reset(self):
        """Reset session data"""
        self.state = ConversationState.IDLE
        self.data = {
            'kode_sa': None,
            'nama': None,
            'no_telp': None,
            'alamat': None
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
        steps = ['kode_sa', 'nama', 'no_telp', 'alamat']
        completed = sum(1 for step in steps if self.data[step])
        return completed, len(steps)