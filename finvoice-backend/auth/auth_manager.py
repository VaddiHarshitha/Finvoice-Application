from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import bcrypt
import psycopg2

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "15")) 
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))  

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "finvoice_db")
}

# Security scheme
security = HTTPBearer()

# Global Redis service instance 
_redis_service = None

def set_redis_service(redis_service):
    """Set the global Redis service instance"""
    global _redis_service
    _redis_service = redis_service
    print(" Redis service registered in auth manager")

print(f" Auth Manager initialized (PostgreSQL)")
print(f"   - Access Token Expiration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
print(f"   - Refresh Token Expiration: {REFRESH_TOKEN_EXPIRE_DAYS} days")
print(f"   - Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")


class AuthManager:
    """
    Central authentication manager with PostgreSQL backend
    NOW WITH REFRESH TOKEN SUPPORT
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Previously hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    
    @staticmethod
    def create_access_token(
        user_id: str,
        additional_claims: Optional[dict] = None
    ) -> str:
        """
        Create a JWT access token (short-lived)
        
        Args:
            user_id: User identifier (will be stored in 'sub' claim)
            additional_claims: Optional dict of extra data to include in token
            
        Returns:
            JWT token string
        """
        # expiration time
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Base payload
        to_encode = {
            "sub": user_id,           # Subject (user ID)
            "exp": expire,             # Expiration time
            "iat": datetime.utcnow(), # Issued at time
            "type": "access"           # Token type (NEW)
        }
        
        if additional_claims:
            to_encode.update(additional_claims)
        
        # Encode and return token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        print(f" Access token created for user: {user_id} (expires in {ACCESS_TOKEN_EXPIRE_MINUTES}m)")
        return encoded_jwt
    
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """
        Create a JWT refresh token (long-lived)
        
        Args:
            user_id: User identifier
            
        Returns:
            JWT refresh token string
        """
        # Calculate expiration time (7 days)
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Payload
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"  # Distinguish from access token
        }
        
        # Encode and return token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        print(f" Refresh token created for user: {user_id} (expires in {REFRESH_TOKEN_EXPIRE_DAYS} days)")
        return encoded_jwt
    
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            dict: Token payload containing user_id and other claims
            
        Raises:
            HTTPException: If token is invalid, expired, or wrong type
        """
        try:
            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid token type. Expected {token_type}, got {payload.get('type')}"
                )
            
            # Extract user_id
            user_id: str = payload.get("sub")
            
            if user_id is None:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: no user ID found"
                )
            
            print(f"✅ {token_type.capitalize()} token verified for user: {user_id}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print(f"❌ {token_type.capitalize()} token expired")
            raise HTTPException(
                status_code=401,
                detail=f"{token_type.capitalize()} token has expired. Please login again."
            )
            
        except JWTError as e:
            print(f" Token verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"Could not validate credentials: {str(e)}"
            )
    
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """
        Generate new access token from refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            dict: {
                "access_token": str,
                "token_type": str
            }
        """
        try:
            # Verify refresh token
            payload = AuthManager.verify_token(refresh_token, token_type="refresh")
            
            # Check if blacklisted (user logged out)
            global _redis_service
            if _redis_service:
                if _redis_service.is_token_blacklisted(refresh_token):
                    print(f" Blacklisted refresh token rejected")
                    raise HTTPException(
                        status_code=401,
                        detail="Refresh token has been revoked. Please login again."
                    )
            
            user_id = payload.get("sub")
            
            # Generate new access token
            new_access_token = AuthManager.create_access_token(user_id)
            
            print(f" New access token generated for user: {user_id}")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f" Refresh token error: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"Failed to refresh token: {str(e)}"
            )
    
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> dict:
        """
        """
        conn = None
        cursor = None
        
        try:
            # Connect to database
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Find user by email
            cursor.execute("""
                SELECT user_id, name, email, phone, password_hash 
                FROM users 
                WHERE email = %s AND is_active = TRUE
            """, (email,))
            
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            user_id, name, email, phone, password_hash = result
            
            # Verify password using bcrypt
            if not AuthManager.verify_password(password, password_hash):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            print(f" User authenticated from DB: {user_id}")
            
            return {
                "user_id": user_id,
                "name": name,
                "email": email,
                "phone": phone
            }
            
        except psycopg2.Error as e:
            print(f" Database error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Database connection failed"
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f" Authentication error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Authentication failed: {str(e)}"
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    
    @staticmethod
    def get_user_by_id(user_id: str) -> dict:
        """
        Get user details by ID from PostgreSQL database
        Args:
            user_id: User identifier
            
        Returns:
            dict: User data with account info
            
        Raises:
            HTTPException: If user not found
        """
        conn = None
        cursor = None
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Get user info
            cursor.execute("""
                SELECT user_id, name, email, phone 
                FROM users 
                WHERE user_id = %s AND is_active = TRUE
            """, (user_id,))
            
            user_result = cursor.fetchone()
            
            if not user_result:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found: {user_id}"
                )
            
            user_id, name, email, phone = user_result
            
            # Get account info
            cursor.execute("""
                SELECT account_number, account_type, balance, currency
                FROM accounts
                WHERE user_id = %s AND is_primary = TRUE
            """, (user_id,))
            
            account_result = cursor.fetchone()
            
            user_data = {
                "user_id": user_id,
                "name": name,
                "email": email,
                "phone": phone
            }
            
            if account_result:
                user_data["account"] = {
                    "account_number": account_result[0],
                    "account_type": account_result[1],
                    "balance": float(account_result[2]),
                    "currency": account_result[3]
                }
            
            return user_data
            
        except psycopg2.Error as e:
            print(f" Database error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Database connection failed"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get user: {str(e)}"
            )
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    This works perfectly with Swagger UI's 🔒 Authorize button
    
    Args:
        credentials: JWT credentials from Authorization header
        
    Returns:
        str: User ID extracted from token
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Check if token is blacklisted in Redis BEFORE verifying
        global _redis_service
        if _redis_service:
            try:
                is_blacklisted = _redis_service.is_token_blacklisted(token)
                if is_blacklisted:
                    print(f" Blacklisted token rejected: {token[:20]}...")
                    raise HTTPException(
                        status_code=401,
                        detail="Token has been revoked. Please login again."
                    )
            except HTTPException:
                raise
            except Exception as redis_error:
                print(f"Redis blacklist check failed: {redis_error}")
                # Continue without blacklist check if Redis fails
        else:
            print(" Redis service not available - skipping blacklist check")
        
        # Verify token and get payload 
        payload = AuthManager.verify_token(token, token_type="access")
        
       # user_id
        return payload["sub"]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f" Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    """
    Optional authentication dependency
    Returns user_id if authenticated, None otherwise
    
    Usage:
        @app.get("/public-or-private")
        async def mixed_route(user_id: Optional[str] = Depends(get_current_user_optional)):
            if user_id:
                return {"message": f"Hello {user_id}!"}
            else:
                return {"message": "Hello guest!"}
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        # Check blacklist
        global _redis_service
        if _redis_service:
            try:
                if _redis_service.is_token_blacklisted(token):
                    return None
            except:
                pass
        
        payload = AuthManager.verify_token(token, token_type="access")
        return payload["sub"]
    except:

        return None
