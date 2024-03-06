from authentication.models import ActiveSessions


class TokenValidationMixin:
    
    def validate_token(self, request):
        session_id = request.headers.get('session_id')
        if not session_id:
            return False, 'Session id not found in header'
        
        session_id = session_id[:7]
        
        # Take user_id from request body
        user_id_hash = request.data.get('user_id_hash')
        if not user_id_hash:
            return False, 'User id not found in request body'
        
        # Check if session id is valid
        active_session = ActiveSessions.objects.filter(user_id_hash=user_id_hash, session_id=session_id)
        if len(active_session) == 0:
            return False, 'Invalid session id'
        
        return True, 'Token is valid'