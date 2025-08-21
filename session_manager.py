from conversation_states import UserSession, ConversationState

class SessionManager:
    """Manager untuk handle multiple user sessions"""
    def __init__(self):
        self.sessions = {}  # user_id -> UserSession
    
    def get_session(self, user_id):
        """Get or create session for user"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id)
        return self.sessions[user_id]
    
    def reset_session(self, user_id):
        """Reset specific user session"""
        if user_id in self.sessions:
            self.sessions[user_id].reset()
    
    def delete_session(self, user_id):
        """Delete user session"""
        if user_id in self.sessions:
            del self.sessions[user_id]
    
    def get_active_sessions_count(self):
        """Get number of active sessions"""
        return len([s for s in self.sessions.values() if s.state != ConversationState.IDLE])
