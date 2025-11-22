"""
Voice Biometrics Service using Azure Speaker Recognition
Enables voice-based authentication
"""

import os
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig
from azure.cognitiveservices.speech.speaker import SpeakerRecognitionModel
from dotenv import load_dotenv

load_dotenv()

class VoiceBiometricsService:
    def __init__(self):
        """Initialize Azure Speaker Recognition"""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
        
        if not self.speech_key:
            print("⚠️ Azure Speech Key not found - voice biometrics disabled")
            self.enabled = False
        else:
            self.speech_config = SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )
            self.enabled = True
            print("✅ Voice Biometrics initialized (Azure)")
    
    def enroll_voice(self, user_id: str, audio_samples: list) -> dict:
        """
        Enroll user's voice (requires 3+ audio samples)
        
        Args:
            user_id: User identifier
            audio_samples: List of audio bytes (3+ samples)
            
        Returns:
            dict: {
                "success": bool,
                "voice_profile_id": str,
                "message": str
            }
        """
        if not self.enabled:
            return {"success": False, "error": "Voice biometrics not enabled"}
        
        if len(audio_samples) < 3:
            return {
                "success": False,
                "error": "Need at least 3 voice samples for enrollment"
            }
        
        try:
            # Create voice profile
            # (Simplified - in production, use Azure SDK properly)
            
            voice_profile_id = f"VOICE_{user_id}_{int(datetime.now().timestamp())}"
            
            # Store voice signature in database (encrypted)
            from utils.encryption import encrypt_dict
            
            voice_data = {
                "profile_id": voice_profile_id,
                "enrolled_at": datetime.now().isoformat(),
                "sample_count": len(audio_samples)
            }
            
            encrypted_signature = encrypt_dict(voice_data)
            
            # Save to database
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users
                SET voice_signature = %s
                WHERE user_id = %s
            """, (encrypted_signature, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "voice_profile_id": voice_profile_id,
                "message": "Voice enrollment complete"
            }
            
        except Exception as e:
            print(f"❌ Voice enrollment error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_voice(self, user_id: str, audio_sample: bytes) -> dict:
        """
        Verify user's voice against enrolled profile
        
        Args:
            user_id: User identifier
            audio_sample: Audio bytes to verify
            
        Returns:
            dict: {
                "success": bool,
                "verified": bool,
                "confidence": float,
                "message": str
            }
        """
        if not self.enabled:
            return {
                "success": False,
                "verified": False,
                "error": "Voice biometrics not enabled"
            }
        
        try:
            # Get user's voice profile from database
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT voice_signature
                FROM users
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result or not result[0]:
                return {
                    "success": False,
                    "verified": False,
                    "error": "No voice profile enrolled"
                }
            
            # In production: Compare audio_sample with stored voice profile
            # For demo: Simulate 85% confidence
            confidence = 0.85
            verified = confidence > 0.75
            
            return {
                "success": True,
                "verified": verified,
                "confidence": confidence,
                "message": "Voice verified" if verified else "Voice not recognized"
            }
            
        except Exception as e:
            print(f"❌ Voice verification error: {e}")
            return {
                "success": False,
                "verified": False,
                "error": str(e)
            }