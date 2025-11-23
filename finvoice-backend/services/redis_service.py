import redis
import json
import os
from datetime import timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class RedisService:
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True  # Automatically decode bytes to strings
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            print(" RedisService initialized")
            print(f"   - Connected to: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
        except redis.ConnectionError:
            print(" Redis connection failed. Make sure Redis is running.")
            raise
    def create_session(
        self,
        user_id: str,
        session_data: Dict[str, Any],
        expiry_minutes: int = 15
    ) -> str:
        """
        Create user session
        
        Args:
            user_id: User identifier
            session_data: Session information (name, email, etc.)
            expiry_minutes: Session expiration in minutes
            
        Returns:
            session_key: Redis key for the session
        """
        try:
            session_key = f"session:{user_id}"
            
            # Store session data as JSON
            self.redis_client.setex(
                session_key,
                timedelta(minutes=expiry_minutes),
                json.dumps(session_data)
            )
            
            print(f" Session created: {session_key} (expires in {expiry_minutes}m)")
            return session_key
            
        except Exception as e:
            print(f" Error creating session: {e}")
            return None
    
    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user session
        
        Args:
            user_id: User identifier
            
        Returns:
            Session data or None if not found/expired
        """
        try:
            session_key = f"session:{user_id}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            return None
            
        except Exception as e:
            print(f" Error getting session: {e}")
            return None
    
    def delete_session(self, user_id: str) -> bool:
        """
        Delete user session (logout)
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            session_key = f"session:{user_id}"
            result = self.redis_client.delete(session_key)
            
            if result:
                print(f" Session deleted: {session_key}")
                return True
            return False
            
        except Exception as e:
            print(f" Error deleting session: {e}")
            return False
    
    def refresh_session(self, user_id: str, expiry_minutes: int = 15) -> bool:
        """
        Refresh session expiry
        
        Args:
            user_id: User identifier
            expiry_minutes: New expiration time
            
        Returns:
            Success status
        """
        try:
            session_key = f"session:{user_id}"
            result = self.redis_client.expire(session_key, timedelta(minutes=expiry_minutes))
            
            if result:
                print(f" Session refreshed: {session_key}")
                return True
            return False
            
        except Exception as e:
            print(f" Error refreshing session: {e}")
            return False
    
    def store_otp(
        self,
        user_id: str,
        otp: str,
        transaction_id: str,
        expiry_minutes: int = 5
    ) -> bool:
        """
        Store OTP for transaction verification
        
        Args:
            user_id: User identifier
            otp: One-time password
            transaction_id: Transaction identifier
            expiry_minutes: OTP expiration (default 5 minutes)
            
        Returns:
            Success status
        """
        try:
            otp_key = f"otp:{user_id}:{transaction_id}"
            
            # Store OTP data
            otp_data = {
                "otp": otp,
                "transaction_id": transaction_id,
                "user_id": user_id,
                "attempts": 0
            }
            
            self.redis_client.setex(
                otp_key,
                timedelta(minutes=expiry_minutes),
                json.dumps(otp_data)
            )
            
            print(f" OTP stored: {otp_key} (expires in {expiry_minutes}m)")
            return True
            
        except Exception as e:
            print(f" Error storing OTP: {e}")
            return False
    
    def verify_otp(
        self,
        user_id: str,
        transaction_id: str,
        otp: str,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Verify OTP for transaction
        
        Args:
            user_id: User identifier
            transaction_id: Transaction identifier
            otp: OTP to verify
            max_attempts: Maximum verification attempts
            
        Returns:
            dict: {
                "valid": bool,
                "message": str,
                "attempts_left": int
            }
        """
        try:
            otp_key = f"otp:{user_id}:{transaction_id}"
            otp_data_str = self.redis_client.get(otp_key)
            
            if not otp_data_str:
                return {
                    "valid": False,
                    "message": "OTP expired or not found",
                    "attempts_left": 0
                }
            
            otp_data = json.loads(otp_data_str)
            
            # Check attempts
            if otp_data["attempts"] >= max_attempts:
                self.redis_client.delete(otp_key)
                return {
                    "valid": False,
                    "message": "Maximum OTP attempts exceeded",
                    "attempts_left": 0
                }
            
            # Verify OTP
            if otp_data["otp"] == otp:
                # OTP correct - delete it
                self.redis_client.delete(otp_key)
                print(f" OTP verified: {otp_key}")
                return {
                    "valid": True,
                    "message": "OTP verified successfully",
                    "attempts_left": max_attempts - otp_data["attempts"]
                }
            else:
                # Wrong OTP - increment attempts
                otp_data["attempts"] += 1
                remaining_ttl = self.redis_client.ttl(otp_key)
                
                self.redis_client.setex(
                    otp_key,
                    remaining_ttl,
                    json.dumps(otp_data)
                )
                
                attempts_left = max_attempts - otp_data["attempts"]
                print(f" Wrong OTP: {otp_key} ({attempts_left} attempts left)")
                
                return {
                    "valid": False,
                    "message": f"Invalid OTP. {attempts_left} attempts left",
                    "attempts_left": attempts_left
                }
            
        except Exception as e:
            print(f" Error verifying OTP: {e}")
            return {
                "valid": False,
                "message": "OTP verification failed",
                "attempts_left": 0
            }
    def check_rate_limit(
        self,
        user_id: str,
        action: str,
        max_requests: int = 10,
        window_minutes: int = 1
    ) -> Dict[str, Any]:
        """
        Check rate limit for user action
        
        Args:
            user_id: User identifier
            action: Action type (e.g., 'login', 'transfer')
            max_requests: Maximum requests allowed
            window_minutes: Time window in minutes
            
        Returns:
            dict: {
                "allowed": bool,
                "remaining": int,
                "reset_in": int (seconds)
            }
        """
        try:
            rate_key = f"rate:{user_id}:{action}"
            
            # Get current count
            count = self.redis_client.get(rate_key)
            
            if count is None:
                # First request
                self.redis_client.setex(
                    rate_key,
                    timedelta(minutes=window_minutes),
                    1
                )
                return {
                    "allowed": True,
                    "remaining": max_requests - 1,
                    "reset_in": window_minutes * 60
                }
            
            count = int(count)
            
            if count >= max_requests:
                # Rate limit exceeded
                ttl = self.redis_client.ttl(rate_key)
                print(f" Rate limit exceeded: {rate_key}")
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_in": ttl
                }
            
            # Increment count
            self.redis_client.incr(rate_key)
            ttl = self.redis_client.ttl(rate_key)
            
            return {
                "allowed": True,
                "remaining": max_requests - count - 1,
                "reset_in": ttl
            }
            
        except Exception as e:
            print(f" Error checking rate limit: {e}")
            # On error, allow request (fail open)
            return {
                "allowed": True,
                "remaining": max_requests,
                "reset_in": window_minutes * 60
            }

    def blacklist_token(self, token: str, expiry_minutes: int = 1440) -> bool:
        """
        Blacklist JWT token (for logout/revoke)
        
        Args:
            token: JWT token to blacklist
            expiry_minutes: How long to keep in blacklist
            
        Returns:
            Success status
        """
        try:
            token_key = f"blacklist:{token}"
            
            self.redis_client.setex(
                token_key,
                timedelta(minutes=expiry_minutes),
                "1"
            )
            
            print(f" Token blacklisted: {token[:20]}...")
            return True
            
        except Exception as e:
            print(f" Error blacklisting token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted
        
        Args:
            token: JWT token to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        try:
            token_key = f"blacklist:{token}"
            return self.redis_client.exists(token_key) > 0
            
        except Exception as e:
            print(f" Error checking token blacklist: {e}")
            return False
    
    def get_all_active_sessions(self) -> int:
        """Get count of active sessions"""
        try:
            keys = self.redis_client.keys("session:*")
            return len(keys)
        except Exception as e:
            print(f" Error getting active sessions: {e}")
            return 0
    
    def clear_user_data(self, user_id: str) -> bool:
        """
        Clear all Redis data for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            # Get all keys for user
            patterns = [
                f"session:{user_id}",
                f"otp:{user_id}:*",
                f"rate:{user_id}:*"
            ]
            
            deleted = 0
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted += self.redis_client.delete(*keys)
            
            print(f" Cleared {deleted} keys for user: {user_id}")
            return True
            
        except Exception as e:
            print(f" Error clearing user data: {e}")

            return False
