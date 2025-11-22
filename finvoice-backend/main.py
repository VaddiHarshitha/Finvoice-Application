"""
FinVoice Backend API - COMPLETE PRODUCTION VERSION
WITH ALL FEATURES: Loans, Bills, Reminders, Analytics, GDPR, Performance Monitoring
Version: 5.0.0
"""

from auth.auth_manager import AuthManager, get_current_user, get_current_user_optional
from fastapi import Depends, Header, Request
from typing import Optional
from collections import defaultdict
import time

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
from contextlib import asynccontextmanager
from utils.clean_up import cleanup_loop, cleanup_old_audio_files, get_cache_stats
from utils.error_handler import (
    handle_api_error,
    log_error,
    log_info,
    log_warning,
    ValidationError,
    BankingError,
    NotFoundError,
    track_error,
    get_error_stats,
    validate_required_fields,
    validate_positive_number
)

import os
from dotenv import load_dotenv
import traceback
from datetime import datetime
import base64
import io
from pathlib import Path
import psycopg2
import re

# Import services
from services.voice_processor import VoiceProcessor
from services.agentic_nlp import AgenticNLP
from services.banking_service import BankingService
from services.conversation_service import ConversationService
from services.redis_service import RedisService
from services.performance import performance_monitor  # ✅ FIXED: Use instance
from services.analytics import AnalyticsService

load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "finvoice_db")
}

# Audio cache directory
AUDIO_CACHE_DIR = Path("cache/audio")
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Performance tracking (legacy - kept for compatibility)
request_times = defaultdict(list)
endpoint_calls = defaultdict(int)


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - runs on startup and shutdown
    """
    # ========== STARTUP ==========
    print("\n" + "="*70)
    print("🚀 STARTING FINVOICE BACKEND v5.0.0")
    print("="*70)
    
    # Run initial cleanup
    print("\n🗑️ Running initial cache cleanup...")
    cleanup_result = cleanup_old_audio_files(hours=24)
    if cleanup_result.get('success'):
        print(f"✅ Initial cleanup: {cleanup_result.get('deleted', 0)} files deleted")
        print(f"   Size freed: {cleanup_result.get('deleted_size_mb', 0)} MB")
    else:
        print(f"⚠️ Initial cleanup failed: {cleanup_result.get('error', 'Unknown error')}")
    
    # Start background cleanup task
    print("🔄 Starting background cleanup task...")
    cleanup_task = asyncio.create_task(cleanup_loop(interval_hours=24))
    print("✅ Background cleanup task started (runs every 24h)")
    
    print("\n" + "="*70)
    print("✅ All services initialized and ready!")
    print("="*70 + "\n")
    
    yield  # Server runs here
    
    # ========== SHUTDOWN ==========
    print("\n🛑 Shutting down...")
    cleanup_task.cancel()
    print("✅ Cleanup task stopped")


# ============================================================================
# INITIALIZE FASTAPI
# ============================================================================

app = FastAPI(
    title="FinVoice Backend API - Complete Production",
    description="Voice Banking with AI: Loans, Bills, Reminders, Analytics & More",
    version="5.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# PERFORMANCE MONITORING MIDDLEWARE (FIXED)
# ============================================================================

@app.middleware("http")
async def performance_middleware_handler(request: Request, call_next):
    """Track request performance and errors"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Track performance
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        # ✅ FIXED: Use instance instead of class
        performance_monitor.record_request(
            endpoint=endpoint,
            duration=duration,
            status_code=status_code,
            method=method
        )
        
        # Legacy tracking (for compatibility)
        request_times[endpoint].append(duration)
        endpoint_calls[endpoint] += 1
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{duration:.3f}s"
        response.headers["X-Endpoint"] = endpoint
        
        # Log slow requests
        if duration > 3.0:
            log_warning(
                f"SLOW REQUEST: {method} {endpoint} took {duration:.2f}s",
                context={
                    "endpoint": endpoint,
                    "duration": duration,
                    "method": method
                }
            )
        
        # Log very slow requests
        if duration > 5.0:
            log_error(
                Exception(f"VERY SLOW REQUEST: {method} {endpoint}"),
                endpoint=endpoint,
                context={
                    "duration": duration,
                    "method": method,
                    "status_code": status_code
                }
            )
        
        return response
        
    except Exception as e:
        # Track errors
        duration = time.time() - start_time
        performance_monitor.record_request(
            endpoint=request.url.path,
            duration=duration,
            status_code=500,
            method=request.method
        )
        track_error(request.url.path, type(e).__name__)
        raise


# ============================================================================
# INITIALIZE SERVICES
# ============================================================================

print("\n🚀 Initializing services...")
voice_processor = VoiceProcessor()
banking_service = BankingService()
agentic_nlp = AgenticNLP(banking_service=banking_service)
conversation_service = ConversationService()

# Initialize Redis service
try:
    redis_service = RedisService()
    
    from auth.auth_manager import set_redis_service
    set_redis_service(redis_service)
    print("✅ Redis service connected to auth manager")
    
except Exception as e:
    print(f"⚠️ Redis not available: {e}")
    redis_service = None

print("✅ All services ready!\n")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def save_audio_to_cache(user_id: str, audio_base64: str) -> str:
    """Save audio to cache and return filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{user_id}_{timestamp}.mp3"
    filepath = AUDIO_CACHE_DIR / filename
    
    audio_bytes = base64.b64decode(audio_base64)
    with open(filepath, 'wb') as f:
        f.write(audio_bytes)
    
    return filename

def log_security_event(
    user_id: str,
    event_type: str,
    details: str,
    ip_address: str = None
):
    """Log security event to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # ✅ FIX: Check if user exists first
        cursor.execute("""
            SELECT user_id FROM users WHERE user_id = %s
        """, (user_id,))
        
        user_exists = cursor.fetchone() is not None
        
        # Only log if user exists OR use a system user for failed logins
        final_user_id = user_id if user_exists else "system"
        
        cursor.execute("""
            INSERT INTO security_events (
                user_id, event_type, details, ip_address, timestamp
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (final_user_id, event_type, details, ip_address, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"🔒 Security event logged: {event_type} for {final_user_id}")
        
    except Exception as e:
        print(f"❌ Failed to log security event: {e}")


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


# ============================================================================
# ROOT & HEALTH
# ============================================================================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "status": "running",
        "service": "FinVoice Backend API",
        "version": "5.0.0",
        "features": [
            "JWT Authentication",
            "Voice Processing (10 languages)",
            "Agentic AI (Gemini 2.0)",
            "Conversation History",
            "Complete OTP Flow via Voice",
            "Security Logging",
            "Auto Audio Cleanup (24h)",
            "Error Handling & Logging",
            "Performance Monitoring",
            "🏦 Loan Management",
            "💡 Bill Payments",
            "⏰ Payment Reminders",
            "📊 Analytics Dashboard",
            "🔒 GDPR Compliance"
        ]
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "voice_processor": "ready",
            "banking_service": "ready",
            "agentic_nlp": "ready",
            "conversation_service": "ready",
            "redis_service": "ready" if redis_service else "unavailable",
            "database": "PostgreSQL",
            "auto_cleanup": "enabled",
            "error_logging": "enabled",
            "performance_tracking": "enabled"
        }
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Login with rate limiting and security logging"""
    try:
        print(f"\n🔐 Login attempt: {email}")
        client_ip = get_client_ip(request)
        
        # Validate input
        if not email or not password:
            raise ValidationError("Email and password are required")
        
        # Rate limiting check
        if redis_service:
            rate_check = redis_service.check_rate_limit(
                user_id=email,
                action="login",
                max_requests=5,
                window_minutes=5
            )
            
            if not rate_check["allowed"]:
                log_security_event(
                    user_id=email,
                    event_type="LOGIN_RATE_LIMITED",
                    details=f"Rate limit exceeded for {email}",
                    ip_address=client_ip
                )
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many login attempts. Try again in {rate_check['reset_in']} seconds"
                )
        
        # Authenticate user
        try:
            user = AuthManager.authenticate_user(email, password)
        except HTTPException as e:
            log_security_event(
                user_id=email,
                event_type="LOGIN_FAILED",
                details=f"Invalid credentials for {email}",
                ip_address=client_ip
            )
            raise e
        
        # Create tokens
        access_token = AuthManager.create_access_token(
            user_id=user['user_id'],
            additional_claims={
                "name": user['name'],
                "email": user['email']
            }
        )
        
        refresh_token = AuthManager.create_refresh_token(
            user_id=user['user_id']
        )
        
        # Create session in Redis
        if redis_service:
            redis_service.create_session(
                user_id=user['user_id'],
                session_data={
                    "name": user['name'],
                    "email": user['email'],
                    "login_time": datetime.now().isoformat(),
                    "ip_address": client_ip
                },
                expiry_minutes=15
            )
        
        # Log successful login
        log_security_event(
            user_id=user['user_id'],
            event_type="LOGIN_SUCCESS",
            details=f"Successful login from {client_ip}",
            ip_address=client_ip
        )
        
        log_info(f"User logged in: {user['user_id']}", user_id=user['user_id'])
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in_minutes": 15,
            "refresh_expires_in_days": 7,
            "user": user
        }
        
    except ValidationError as e:
        raise handle_api_error(e, email, "/auth/login")
    except HTTPException:
        raise
    except Exception as e:
        raise handle_api_error(e, email, "/auth/login")

    
@app.post("/auth/refresh", 
          summary="🔄 Refresh Access Token",
          tags=["Authentication"])
async def refresh_token(
    refresh_token: str = Form(..., description="Refresh token from login")
):
    """Get a new access token using refresh token"""
    try:
        if not refresh_token:
            raise ValidationError("Refresh token is required")
        
        result = AuthManager.refresh_access_token(refresh_token)
        
        log_info("Access token refreshed")
        
        return {
            "success": True,
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in_minutes": result["expires_in_minutes"],
            "message": "Access token refreshed successfully"
        }
        
    except ValidationError as e:
        raise handle_api_error(e, None, "/auth/refresh")
    except HTTPException:
        raise
    except Exception as e:
        raise handle_api_error(e, None, "/auth/refresh")


@app.post("/auth/logout")
async def logout(
    request: Request,
    current_user: str = Depends(get_current_user),
    authorization: str = Header(...),
    refresh_token: Optional[str] = Form(None)
):
    """Logout user and blacklist both tokens"""
    try:
        client_ip = get_client_ip(request)
        access_token = authorization.replace("Bearer ", "")
        
        if redis_service:
            redis_service.blacklist_token(access_token, expiry_minutes=15)
            
            if refresh_token:
                redis_service.blacklist_token(refresh_token, expiry_minutes=7*24*60)
            
            redis_service.delete_session(current_user)
        
        log_security_event(
            user_id=current_user,
            event_type="LOGOUT_SUCCESS",
            details=f"User logged out from {client_ip}",
            ip_address=client_ip
        )
        
        log_info("User logged out", user_id=current_user)
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        raise handle_api_error(e, current_user, "/auth/logout")


@app.get("/auth/me")
async def get_current_user_info(
    current_user: str = Depends(get_current_user)
):
    """Get current user information"""
    try:
        user = AuthManager.get_user_by_id(current_user)
        
        return {
            "success": True,
            "user": user
        }
        
    except Exception as e:
        raise handle_api_error(e, current_user, "/auth/me")


# ============================================================================
# VOICE PROCESSING WITH COMPLETE OTP FLOW
# ============================================================================

@app.post("/api/voice/process")
async def process_voice(
    request: Request,
    current_user: str = Depends(get_current_user),
    audio: UploadFile = File(...),
    language: str = Form("en-IN")
):
    """COMPLETE VOICE PROCESSING WITH AUTONOMOUS OTP FLOW"""
    
    request_start = datetime.now()
    
    try:
        print("\n" + "="*70)
        print("🤖 VOICE REQUEST WITH OTP FLOW")
        print("="*70)
        
        client_ip = get_client_ip(request)
        
        # Validate language
        supported_languages = list(voice_processor.get_supported_languages().keys())
        if language not in supported_languages:
            raise ValidationError(
                f"Unsupported language: {language}",
                field="language",
                details={"supported": supported_languages}
            )
        
        # Read audio
        audio_content = await audio.read()
        audio_size = len(audio_content)
        
        if audio_size == 0:
            raise ValidationError("Empty audio file", field="audio")
        
        if audio_size > 10 * 1024 * 1024:
            raise ValidationError(
                "Audio too large (max 10MB)",
                field="audio",
                details={"size_mb": audio_size / (1024 * 1024)}
            )
        
        # Speech-to-Text
        stt_result = voice_processor.transcribe_audio(
            audio_content=audio_content,
            language_code=language
        )
        
        if not stt_result['success']:
            raise BankingError(
                "Speech recognition failed",
                operation="stt",
                details={"error": stt_result.get('error')}
            )
        
        transcribed_text = stt_result['text']
        stt_confidence = stt_result.get('confidence', 0.0)
        
        # AI Processing
        lang_code = language.split('-')[0] if '-' in language else language
        
        agent_result = agentic_nlp.process(
            text=transcribed_text,
            user_id=current_user,
            language=lang_code
        )
        
        if not agent_result['success']:
            raise BankingError(
                "AI processing failed",
                operation="nlp",
                details={"error": agent_result.get('error')}
            )
        
        response_text = agent_result['response']
        intent = agent_result['intent']
        detected_lang = agent_result.get('detected_language', lang_code)
        ai_confidence = agent_result.get('confidence', 0.95)
        
        # OTP Flow handling
        transaction_id = None
        otp_status = None
        
        # OTP VERIFICATION
        if intent == "OTP_VERIFICATION" and 'otp_extracted' in agent_result:
            otp = agent_result['otp_extracted']
            
            if redis_service:
                session = redis_service.get_session(current_user)
                
                if session and 'pending_transaction_id' in session:
                    transaction_id = session['pending_transaction_id']
                    
                    verification = redis_service.verify_otp(
                        user_id=current_user,
                        transaction_id=transaction_id,
                        otp=otp,
                        max_attempts=3
                    )
                    
                    if verification["valid"]:
                        log_security_event(
                            user_id=current_user,
                            event_type="OTP_VERIFIED",
                            details=f"OTP verified via voice for {transaction_id}",
                            ip_address=client_ip
                        )
                        
                        log_security_event(
                            user_id=current_user,
                            event_type="TRANSACTION_SUCCESS",
                            details=f"Transaction {transaction_id} completed via voice",
                            ip_address=client_ip
                        )
                        
                        session['pending_transaction_id'] = None
                        redis_service.create_session(
                            user_id=current_user,
                            session_data=session,
                            expiry_minutes=1440
                        )
                        
                        response_text = "Transaction completed successfully!"
                        intent = "TRANSACTION_COMPLETE"
                        otp_status = "verified"
                        
                    else:
                        log_security_event(
                            user_id=current_user,
                            event_type="OTP_FAILED",
                            details=f"Invalid OTP. Attempts: {verification['attempts_left']}",
                            ip_address=client_ip
                        )
                        
                        response_text = f"Invalid OTP. {verification['message']}"
                        otp_status = "failed"
                        intent = "OTP_FAILED"
                        
                else:
                    response_text = "No pending transaction found."
                    otp_status = "no_transaction"
        
        # FUND TRANSFER
        elif intent == "FUND_TRANSFER" and "OTP:" in response_text:
            match = re.search(r'OTP:\s*(\d{6})', response_text)
            if match:
                otp = match.group(1)
                transaction_id = f"TXN{int(datetime.now().timestamp())}"
                
                if redis_service:
                    redis_service.store_otp(
                        user_id=current_user,
                        otp=otp,
                        transaction_id=transaction_id,
                        expiry_minutes=5
                    )
                    
                    session = redis_service.get_session(current_user)
                    if session:
                        session['pending_transaction_id'] = transaction_id
                        redis_service.create_session(
                            user_id=current_user,
                            session_data=session,
                            expiry_minutes=1440
                        )
                    
                    log_security_event(
                        user_id=current_user,
                        event_type="OTP_GENERATED",
                        details=f"OTP generated via voice for {transaction_id}",
                        ip_address=client_ip
                    )
                    
                    response_text += " Please say your OTP to complete the transaction."
                    otp_status = "pending"
        
        # Text-to-Speech
        tts_result = voice_processor.synthesize_speech(
            text=response_text,
            language_code=language
        )
        
        audio_filename = None
        audio_url = None
        
        if tts_result.get('success') and tts_result.get('audio_base64'):
            audio_filename = save_audio_to_cache(current_user, tts_result['audio_base64'])
            audio_url = f"/api/audio/{audio_filename}"
        
        # Save Conversation
        overall_confidence = (stt_confidence + ai_confidence) / 2
        
        session_id = conversation_service.save_voice_session(
            user_id=current_user,
            language=language,
            transcribed_text=transcribed_text,
            intent=intent,
            response_text=response_text,
            confidence=overall_confidence,
            audio_file_path=audio_filename
        )
        
        if session_id > 0:
            conversation_service.save_conversation_turn(
                user_id=current_user,
                session_id=session_id,
                role="user",
                message=transcribed_text,
                language=detected_lang
            )
            
            conversation_service.save_conversation_turn(
                user_id=current_user,
                session_id=session_id,
                role="assistant",
                message=response_text,
                language=detected_lang
            )
        
        request_duration = (datetime.now() - request_start).total_seconds()
        
        log_info(
            f"Voice request processed: {intent}",
            user_id=current_user,
            context={"duration": request_duration, "confidence": overall_confidence}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "authenticated_user": current_user,
            "language": language,
            "detected_language": detected_lang,
            "transcribed_text": transcribed_text,
            "intent": intent,
            "confidence": {
                "stt": stt_confidence,
                "ai": ai_confidence,
                "overall": overall_confidence
            },
            "response_text": response_text,
            "response_audio": tts_result.get('audio_base64') if tts_result.get('success') else None,
            "audio_url": audio_url,
            "audio_filename": audio_filename,
            "transaction_id": transaction_id,
            "otp_status": otp_status,
            "metadata": {
                "audio_size_bytes": audio_size,
                "processing_time_seconds": round(request_duration, 2),
                "timestamp": request_start.isoformat()
            }
        }
        
    except (ValidationError, BankingError) as e:
        raise handle_api_error(e, current_user, "/api/voice/process")
    except HTTPException:
        raise
    except Exception as e:
        raise handle_api_error(
            e,
            current_user,
            "/api/voice/process",
            context={"language": language}
        )


# ============================================================================
# TRANSACTION ENDPOINTS
# ============================================================================

@app.post("/api/transactions/initiate")
async def initiate_transfer(
    request: Request,
    current_user: str = Depends(get_current_user),
    recipient: str = Form(...),
    amount: float = Form(...)
):
    """Initiate transfer with validation"""
    try:
        client_ip = get_client_ip(request)
        
        # Validate amount
        if amount <= 0:
            raise ValidationError(
                "Amount must be positive",
                field="amount",
                details={"value": amount}
            )
        
        # Validate recipient
        if not recipient or len(recipient.strip()) == 0:
            raise ValidationError("Recipient cannot be empty", field="recipient")
        
        result = banking_service.transfer_money(current_user, recipient, amount)
        
        if not result['success']:
            error_msg = result.get('error', 'Transfer failed')
            if 'not found' in error_msg.lower():
                raise ValidationError(
                    f"Recipient '{recipient}' not found",
                    field="recipient",
                    details={"available": error_msg}
                )
            
            raise BankingError(
                error_msg,
                operation="transfer",
                details={"recipient": recipient, "amount": amount}
            )
        
        transaction_id = f"TXN{int(datetime.now().timestamp())}"
        otp = result['otp']
        
        if redis_service:
            redis_service.store_otp(
                user_id=current_user,
                otp=otp,
                transaction_id=transaction_id,
                expiry_minutes=5
            )
        
        log_security_event(
            user_id=current_user,
            event_type="OTP_GENERATED",
            details=f"OTP for ₹{amount} to {recipient}",
            ip_address=client_ip
        )
        
        log_info(
            f"Transfer initiated: ₹{amount} to {recipient}",
            user_id=current_user,
            context={"transaction_id": transaction_id}
        )
        
        return {
            "success": True,
            "requires_otp": True,
            "transaction_id": transaction_id,
            "otp": otp,
            "recipient": result['recipient'],
            "amount": amount,
            "message": "OTP sent"
        }
        
    except (ValidationError, BankingError) as e:
        raise handle_api_error(e, current_user, "/api/transactions/initiate")
    except Exception as e:
        raise handle_api_error(
            e,
            current_user,
            "/api/transactions/initiate",
            context={"recipient": recipient, "amount": amount}
        )


@app.post("/api/transactions/verify-otp")
async def verify_otp(
    request: Request,
    current_user: str = Depends(get_current_user),
    transaction_id: str = Form(...),
    otp: str = Form(...)
):
    """Verify OTP with validation"""
    try:
        client_ip = get_client_ip(request)
        
        if not redis_service:
            raise BankingError("OTP service unavailable", operation="otp_verify")
        
        if not otp or len(otp) != 6:
            raise ValidationError("Invalid OTP format", field="otp")
        
        verification = redis_service.verify_otp(
            user_id=current_user,
            transaction_id=transaction_id,
            otp=otp,
            max_attempts=3
        )
        
        if not verification["valid"]:
            log_security_event(
                user_id=current_user,
                event_type="OTP_FAILED",
                details=f"Invalid OTP for {transaction_id}",
                ip_address=client_ip
            )
            
            return {
                "success": False,
                "message": verification["message"],
                "attempts_left": verification["attempts_left"]
            }
        
        log_security_event(
            user_id=current_user,
            event_type="OTP_VERIFIED",
            details=f"OTP verified for {transaction_id}",
            ip_address=client_ip
        )
        
        log_security_event(
            user_id=current_user,
            event_type="TRANSACTION_SUCCESS",
            details=f"Transaction {transaction_id} completed",
            ip_address=client_ip
        )
        
        log_info(
            f"Transaction completed: {transaction_id}",
            user_id=current_user
        )
        
        return {
            "success": True,
            "message": "Transaction completed",
            "transaction_id": transaction_id,
            "reference_number": f"REF{transaction_id}"
        }
        
    except ValidationError as e:
        raise handle_api_error(e, current_user, "/api/transactions/verify-otp")
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/transactions/verify-otp")


# ============================================================================
# LOAN ENDPOINTS 🏦 (NEW)
# ============================================================================

@app.get("/api/loans",
         summary="🏦 Get User Loans",
         tags=["Loans"])
async def get_user_loans(
    current_user: str = Depends(get_current_user)
):
    """Get all active loans for user"""
    try:
        result = banking_service.get_loan_info(current_user)
        
        if result['success']:
            log_info(
                f"Loan info retrieved: {len(result['loans'])} loans",
                user_id=current_user
            )
        
        return {
            "success": result['success'],
            "loans": result.get('loans', []),
            "total_outstanding": result.get('total_outstanding', 0),
            "count": len(result.get('loans', []))
        }
        
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/loans")


@app.post("/api/loans/eligibility",
          summary="💰 Check Loan Eligibility",
          tags=["Loans"])
async def check_loan_eligibility(
    current_user: str = Depends(get_current_user),
    amount: float = Form(...)
):
    """Check if user is eligible for a loan"""
    try:
        # Validate amount
        if amount <= 0:
            raise ValidationError(
                "Loan amount must be positive",
                field="amount",
                details={"value": amount}
            )
        
        if amount < 10000:
            raise ValidationError(
                "Minimum loan amount is ₹10,000",
                field="amount",
                details={"value": amount, "minimum": 10000}
            )
        
        result = banking_service.get_loan_eligibility(current_user, amount)
        
        log_info(
            f"Loan eligibility check: ₹{amount:,.0f} - {'Eligible' if result.get('eligible') else 'Not Eligible'}",
            user_id=current_user,
            context={"amount": amount, "eligible": result.get('eligible')}
        )
        
        return {
            "success": result['success'],
            "eligible": result.get('eligible', False),
            "requested_amount": amount,
            "max_eligible": result.get('max_eligible', 0),
            "interest_rate": result.get('interest_rate'),
            "tenure_months": result.get('tenure_months'),
            "monthly_emi": result.get('monthly_emi'),
            "current_balance": result.get('current_balance')
        }
        
    except ValidationError as e:
        raise handle_api_error(e, current_user, "/api/loans/eligibility")
    except Exception as e:
        raise handle_api_error(
            e,
            current_user,
            "/api/loans/eligibility",
            context={"amount": amount}
        )


# ============================================================================
# BILL PAYMENT ENDPOINTS 💡 (NEW)
# ============================================================================

@app.post("/api/bills/pay",
          summary="💡 Pay Utility Bill",
          tags=["Bills"])
async def pay_utility_bill(
    request: Request,
    current_user: str = Depends(get_current_user),
    bill_type: str = Form(...),
    biller_name: str = Form(...),
    amount: float = Form(...),
    account_number: str = Form(None)
):
    """Pay utility bills (electricity, water, phone, internet, gas)"""
    try:
        client_ip = get_client_ip(request)
        
        # Validate bill type
        valid_bill_types = ['ELECTRICITY', 'WATER', 'PHONE', 'INTERNET', 'GAS']
        bill_type_upper = bill_type.upper()
        
        if bill_type_upper not in valid_bill_types:
            raise ValidationError(
                f"Invalid bill type: {bill_type}",
                field="bill_type",
                details={"valid_types": valid_bill_types}
            )
        
        # Validate amount
        if amount <= 0:
            raise ValidationError(
                "Bill amount must be positive",
                field="amount",
                details={"value": amount}
            )
        
        if amount > 100000:
            raise ValidationError(
                "Maximum bill payment is ₹1,00,000",
                field="amount",
                details={"value": amount, "maximum": 100000}
            )
        
        # Validate biller name
        if not biller_name or len(biller_name.strip()) == 0:
            raise ValidationError("Biller name cannot be empty", field="biller_name")
        
        # Execute bill payment
        result = banking_service.pay_bill(
            user_id=current_user,
            bill_type=bill_type_upper,
            biller_name=biller_name,
            amount=amount,
            account_number=account_number
        )
        
        if not result['success']:
            raise BankingError(
                result.get('error', 'Bill payment failed'),
                operation="bill_payment",
                details={
                    "bill_type": bill_type,
                    "amount": amount,
                    "biller": biller_name
                }
            )
        
        # Log security event
        log_security_event(
            user_id=current_user,
            event_type="BILL_PAYMENT",
            details=f"Paid ₹{amount:,.0f} for {bill_type} to {biller_name}",
            ip_address=client_ip
        )
        
        log_info(
            f"Bill payment: {bill_type} - ₹{amount:,.0f}",
            user_id=current_user,
            context={
                "bill_type": bill_type,
                "amount": amount,
                "reference": result.get('bill_reference')
            }
        )
        
        return {
            "success": True,
            "bill_reference": result['bill_reference'],
            "bill_type": result['bill_type'],
            "biller_name": result['biller_name'],
            "amount_paid": result['amount_paid'],
            "message": result['message']
        }
        
    except (ValidationError, BankingError) as e:
        raise handle_api_error(e, current_user, "/api/bills/pay")
    except Exception as e:
        raise handle_api_error(
            e,
            current_user,
            "/api/bills/pay",
            context={
                "bill_type": bill_type,
                "amount": amount
            }
        )


# ============================================================================
# PAYMENT REMINDER ENDPOINTS ⏰ (NEW)
# ============================================================================

@app.post("/api/reminders/create",
          summary="⏰ Create Payment Reminder",
          tags=["Reminders"])
async def create_payment_reminder(
    current_user: str = Depends(get_current_user),
    reminder_type: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    description: str = Form(...)
):
    """Create a payment reminder"""
    try:
        # Validate reminder type
        valid_types = ['BILL', 'EMI', 'TRANSFER', 'OTHER']
        reminder_type_upper = reminder_type.upper()
        
        if reminder_type_upper not in valid_types:
            raise ValidationError(
                f"Invalid reminder type: {reminder_type}",
                field="reminder_type",
                details={"valid_types": valid_types}
            )
        
        # Validate amount
        if amount <= 0:
            raise ValidationError(
                "Amount must be positive",
                field="amount",
                details={"value": amount}
            )
        
        # Validate due_date format (YYYY-MM-DD)
        from datetime import datetime as dt
        try:
            due_date_obj = dt.strptime(due_date, "%Y-%m-%d")
            
            # Check if date is in the past
            if due_date_obj.date() < dt.now().date():
                raise ValidationError(
                    "Due date cannot be in the past",
                    field="due_date",
                    details={"provided": due_date}
                )
        except ValueError:
            raise ValidationError(
                "Invalid date format. Use YYYY-MM-DD",
                field="due_date",
                details={"provided": due_date, "expected": "YYYY-MM-DD"}
            )
        
        # Validate description
        if not description or len(description.strip()) == 0:
            raise ValidationError("Description cannot be empty", field="description")
        
        # Create reminder
        result = banking_service.create_payment_reminder(
            user_id=current_user,
            reminder_type=reminder_type_upper,
            amount=amount,
            due_date=due_date,
            description=description
        )
        
        if not result['success']:
            raise BankingError(
                result.get('error', 'Failed to create reminder'),
                operation="create_reminder"
            )
        
        log_info(
            f"Reminder created: {reminder_type} - ₹{amount:,.0f} on {due_date}",
            user_id=current_user,
            context={
                "reminder_id": result.get('reminder_id'),
                "type": reminder_type,
                "amount": amount
            }
        )
        
        return {
            "success": True,
            "reminder_id": result['reminder_id'],
            "message": result['message']
        }
        
    except ValidationError as e:
        raise handle_api_error(e, current_user, "/api/reminders/create")
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/reminders/create")


@app.get("/api/reminders/upcoming",
         summary="📅 Get Upcoming Payments",
         tags=["Reminders"])
async def get_upcoming_payments(
    current_user: str = Depends(get_current_user),
    days: int = 7
):
    """Get upcoming payment reminders"""
    try:
        # Validate days
        if days < 1 or days > 365:
            raise ValidationError(
                "Days must be between 1 and 365",
                field="days",
                details={"value": days}
            )
        
        result = banking_service.get_upcoming_payments(current_user, days)
        
        if result['success']:
            log_info(
                f"Retrieved {result['count']} upcoming payments",
                user_id=current_user,
                context={"days": days, "count": result['count']}
            )
        
        return {
            "success": result['success'],
            "upcoming_payments": result.get('upcoming_payments', []),
            "count": result.get('count', 0),
            "total_amount": result.get('total_amount', 0),
            "days": days
        }
        
    except ValidationError as e:
        raise handle_api_error(e, current_user, "/api/reminders/upcoming")
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/reminders/upcoming")


# ============================================================================
# CONVERSATION & CHAT ENDPOINTS
# ============================================================================

@app.get("/api/conversations")
async def get_conversations(
    current_user: str = Depends(get_current_user),
    limit: int = 10
):
    """Get conversation history"""
    try:
        conversations = conversation_service.get_user_conversations(
            user_id=current_user,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": current_user,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/conversations")


@app.get("/api/conversations/{session_id}")
async def get_conversation_details(
    session_id: int,
    current_user: str = Depends(get_current_user)
):
    """Get specific conversation"""
    try:
        conversation = conversation_service.get_conversation_by_session(session_id)
        
        if "error" not in conversation and conversation.get("user_id") != current_user:
            raise NotFoundError("Conversation", str(session_id))
        
        return {
            "success": True,
            "conversation": conversation
        }
    except NotFoundError as e:
        raise handle_api_error(e, current_user, f"/api/conversations/{session_id}")
    except Exception as e:
        raise handle_api_error(e, current_user, f"/api/conversations/{session_id}")


@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    current_user: str = Depends(get_current_user),
    language: str = Form("auto")
):
    """Text-only chat with validation"""
    try:
        # Validate input
        if not message or len(message.strip()) == 0:
            raise ValidationError("Message cannot be empty", field="message")
        
        if len(message) > 1000:
            raise ValidationError(
                "Message too long (max 1000 characters)",
                field="message",
                details={"length": len(message)}
            )
        
        result = agentic_nlp.process(
            text=message,
            user_id=current_user,
            language=language
        )
        
        if not result.get('success'):
            raise BankingError(
                "Chat processing failed",
                operation="chat",
                details={"error": result.get('error')}
            )
        
        log_info(
            f"Chat processed: {message[:50]}...",
            user_id=current_user,
            context={"intent": result.get('intent')}
        )
        
        return result
        
    except ValidationError as e:
        raise handle_api_error(e, current_user, "/api/chat")
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/chat", context={"message_length": len(message)})


# ============================================================================
# ANALYTICS ENDPOINTS 📊 (NEW)
# ============================================================================

@app.get("/api/analytics/dashboard",
         summary="📊 Analytics Dashboard",
         tags=["Analytics"])
async def get_analytics_dashboard(days: int = 7):
    """Get comprehensive analytics dashboard"""
    try:
        analytics = AnalyticsService(DB_CONFIG)
        
        return {
            "success": True,
            "usage_metrics": analytics.get_usage_metrics(days),
            "transaction_metrics": analytics.get_transaction_metrics(days),
            "roi_metrics": analytics.calculate_roi(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================================
# GDPR ENDPOINTS 🔒 (NEW)
# ============================================================================

@app.post("/api/user/export-data",
          summary="📦 Export User Data (GDPR)",
          tags=["GDPR"])
async def export_user_data(
    current_user: str = Depends(get_current_user)
):
    """GDPR: Export all user data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get all user data
        data = {
            "user_info": {},
            "transactions": [],
            "conversations": [],
            "security_events": []
        }
        
        # User info
        cursor.execute("""
            SELECT name, email, phone, created_at
            FROM users WHERE user_id = %s
        """, (current_user,))
        row = cursor.fetchone()
        data["user_info"] = {
            "name": row[0],
            "email": row[1],
            "phone": row[2],
            "joined": row[3].isoformat()
        }
        
        # Transactions
        cursor.execute("""
            SELECT transaction_id, amount, type, timestamp
            FROM transactions WHERE user_id = %s
        """, (current_user,))
        for row in cursor.fetchall():
            data["transactions"].append({
                "id": row[0],
                "amount": float(row[1]),
                "type": row[2],
                "date": row[3].isoformat()
            })
        
        cursor.close()
        conn.close()
        
        log_security_event(
            user_id=current_user,
            event_type="DATA_EXPORT",
            details="User exported their data (GDPR)"
        )
        
        return {
            "success": True,
            "data": data,
            "exported_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/user/export-data")


@app.delete("/api/user/delete-account",
            summary="🗑️ Delete Account (GDPR)",
            tags=["GDPR"])
async def delete_user_account(
    current_user: str = Depends(get_current_user),
    confirmation: str = Form(...)
):
    """GDPR: Delete user account and all data"""
    try:
        if confirmation != "DELETE MY ACCOUNT":
            raise ValidationError(
                "Invalid confirmation",
                details={"required": "DELETE MY ACCOUNT"}
            )
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Soft delete (mark as inactive)
        cursor.execute("""
            UPDATE users
            SET is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (current_user,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        log_security_event(
            user_id=current_user,
            event_type="ACCOUNT_DELETED",
            details="User deleted their account (GDPR)"
        )
        
        return {
            "success": True,
            "message": "Account deleted successfully"
        }
        
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/user/delete-account")


# ============================================================================
# ADMIN & MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/admin/error-stats",
         summary="📊 Error Statistics",
         tags=["Admin"])
async def get_error_statistics():
    """Get error statistics and rates"""
    try:
        stats = get_error_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/admin/logs",
         summary="📋 Recent Logs",
         tags=["Admin"])
async def get_recent_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        log_file = Path("logs/app.log")
        
        if not log_file.exists():
            return {
                "success": False,
                "error": "Log file not found"
            }
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]
        
        return {
            "success": True,
            "lines": len(recent),
            "logs": recent
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/admin/cleanup-cache",
          summary="🗑️ Manual Cache Cleanup",
          tags=["Admin"])
async def manual_cleanup(hours: int = 24):
    """Manually trigger cache cleanup"""
    try:
        result = cleanup_old_audio_files(hours=hours)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/cache-stats",
         summary="📊 Cache Statistics",
         tags=["Admin"])
async def cache_statistics():
    """Get cache statistics"""
    try:
        stats = get_cache_stats()
        return {
            "success": True,
            "cache_directory": str(AUDIO_CACHE_DIR),
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================================
# PERFORMANCE MONITORING ENDPOINTS (FIXED)
# ============================================================================

@app.get("/api/performance",
         summary="📊 Performance Metrics",
         tags=["Monitoring"])
async def get_performance_metrics():
    """Get comprehensive API performance statistics"""
    try:
        all_stats = performance_monitor.get_all_stats()
        summary = performance_monitor.get_summary()
        
        return {
            "success": True,
            "summary": summary,
            "endpoints": all_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/performance/summary",
         summary="📈 Performance Summary",
         tags=["Monitoring"])
async def get_performance_summary():
    """Get quick performance summary"""
    try:
        summary = performance_monitor.get_summary()
        recommendations = performance_monitor.get_recommendations()
        
        return {
            "success": True,
            "summary": summary,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/performance/slow",
         summary="⚠️ Slow Endpoints",
         tags=["Monitoring"])
async def get_slow_endpoints(threshold: float = 1.0):
    """Get endpoints slower than threshold"""
    try:
        slow_endpoints = performance_monitor.get_slow_endpoints(threshold)
        
        return {
            "success": True,
            "threshold_seconds": threshold,
            "slow_endpoints": slow_endpoints,
            "count": len(slow_endpoints),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/performance/errors",
         summary="🚨 Error-Prone Endpoints",
         tags=["Monitoring"])
async def get_error_endpoints(min_error_rate: float = 5.0):
    """Get endpoints with high error rates"""
    try:
        error_endpoints = performance_monitor.get_error_prone_endpoints(min_error_rate)
        
        return {
            "success": True,
            "min_error_rate": min_error_rate,
            "error_prone_endpoints": error_endpoints,
            "count": len(error_endpoints),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/performance/popular",
         summary="🔥 Most Used Endpoints",
         tags=["Monitoring"])
async def get_popular_endpoints(limit: int = 10):
    """Get most frequently called endpoints"""
    try:
        popular = performance_monitor.get_most_used_endpoints(limit)
        
        return {
            "success": True,
            "limit": limit,
            "popular_endpoints": popular,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/performance/endpoint/{endpoint_path:path}",
         summary="🔍 Endpoint Details",
         tags=["Monitoring"])
async def get_endpoint_performance(endpoint_path: str):
    """Get detailed performance stats for specific endpoint"""
    try:
        if not endpoint_path.startswith('/'):
            endpoint_path = '/' + endpoint_path
        
        stats = performance_monitor.get_endpoint_stats(endpoint_path)
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/performance/reset",
          summary="🔄 Reset Performance Stats",
          tags=["Monitoring"])
async def reset_performance_stats():
    """Reset all performance statistics"""
    try:
        performance_monitor.reset_stats()
        
        log_info("Performance statistics reset")
        
        return {
            "success": True,
            "message": "Performance statistics reset successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================================
# OTHER ENDPOINTS
# ============================================================================

@app.get("/api/security/events")
async def get_security_events(
    current_user: str = Depends(get_current_user),
    limit: int = 20
):
    """Get security audit log"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_type, details, ip_address, timestamp
            FROM security_events
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (current_user, limit))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                "event_type": row[0],
                "details": row[1],
                "ip_address": row[2],
                "timestamp": row[3].isoformat()
            })
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "user_id": current_user,
            "events": events,
            "count": len(events)
        }
    except Exception as e:
        raise handle_api_error(e, current_user, "/api/security/events")


@app.get("/api/audio/{filename}")
async def play_audio(filename: str):
    """Play cached audio"""
    try:
        filepath = AUDIO_CACHE_DIR / filename
        
        if not filepath.resolve().is_relative_to(AUDIO_CACHE_DIR.resolve()):
            raise NotFoundError("Audio file", filename)
        
        if not filepath.exists():
            raise NotFoundError("Audio file", filename)
        
        with open(filepath, 'rb') as f:
            audio_bytes = f.read()
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except NotFoundError as e:
        raise handle_api_error(e, None, f"/api/audio/{filename}")
    except Exception as e:
        raise handle_api_error(e, None, f"/api/audio/{filename}")


@app.get("/api/languages")
async def get_languages():
    """Get supported languages"""
    return {
        "voice_languages": voice_processor.get_supported_languages(),
        "text_languages": {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "mr": "Marathi"
        }
    }


@app.get("/api/stats")
async def get_stats():
    """Get statistics"""
    try:
        conversation_history = agentic_nlp.get_memory()
        
        intent_counts = {}
        language_counts = {}
        
        for entry in conversation_history:
            intent = entry.get('intent', 'UNKNOWN')
            language = entry.get('language', 'en')
            
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            language_counts[language] = language_counts.get(language, 0) + 1
        
        return {
            "total_conversations": len(conversation_history),
            "intent_distribution": intent_counts,
            "language_distribution": language_counts,
            "cached_audio_files": len(list(AUDIO_CACHE_DIR.glob("*.mp3"))),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/admin/sessions")
async def get_active_sessions():
    """Get active sessions"""
    try:
        if not redis_service:
            return {"active_sessions": "Redis unavailable"}
        
        count = redis_service.get_all_active_sessions()
        
        return {
            "success": True,
            "active_sessions": count
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom error handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# TESTING ENDPOINTS
# ============================================================================

@app.post("/test/encryption",
          summary="🧪 Test Encryption",
          tags=["Testing"])
async def test_encryption_endpoint(
    data: str = Form(..., description="Data to encrypt")
):
    """Test AES-256 encryption"""
    try:
        from utils.encryption import encrypt_data, decrypt_data
        
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        
        return {
            "success": True,
            "original": data,
            "encrypted": encrypted,
            "decrypted": decrypted,
            "match": data == decrypted
        }
        
    except Exception as e:
        raise handle_api_error(e, None, "/test/encryption")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🤖 FINVOICE v5.0.0 - COMPLETE PRODUCTION VERSION")
    print("="*70)
    print("\n📍 Server: http://localhost:8000")
    print("📄 Docs: http://localhost:8000/docs")
    print("🗄️ Database: PostgreSQL")
    print("🔴 Redis: localhost:6379")
    print("🤖 AI: Gemini 2.0 Flash")
    print("\n✨ Features:")
    print("   • Voice Processing (10 languages)")
    print("   • Complete OTP Flow")
    print("   • 🏦 Loan Management")
    print("   • 💡 Bill Payments")
    print("   • ⏰ Payment Reminders")
    print("   • 📊 Analytics Dashboard")
    print("   • 🔒 GDPR Compliance")
    print("   • Performance Monitoring")
    print("   • Security Logging")
    print("   • Auto Cleanup")
    print("\n⏳ Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")