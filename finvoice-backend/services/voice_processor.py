"""
Voice Processing Service
Handles Speech-to-Text and Text-to-Speech using Google Cloud
WITH MP3 to WAV CONVERSION
"""

import os
from google.cloud import speech_v1
from google.cloud import texttospeech_v1
from google.oauth2 import service_account
import base64
import wave
import io


class VoiceProcessor:
    def __init__(self, credentials_path: str = "google-credentials.json"):
        """
        Initialize Voice Processor with Google Cloud credentials
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
        """
        # Load credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        
        # Initialize clients
        self.speech_client = speech_v1.SpeechClient(credentials=self.credentials)
        self.tts_client = texttospeech_v1.TextToSpeechClient(credentials=self.credentials)
        
        print("✅ VoiceProcessor initialized")
        print(f"✅ Connected to project: {self.credentials.project_id}")
    
    
    # =========================================
    # SPEECH-TO-TEXT METHODS
    # =========================================
    
    def transcribe_audio(
        self, 
        audio_content: bytes,
        language_code: str = "en-IN",
        sample_rate: int = 16000
    ) -> dict:
        """
        Convert audio to text using Google Speech-to-Text
        Automatically converts MP3 to WAV if needed
        
        Args:
            audio_content: Audio file as bytes (MP3, WAV, etc.)
            language_code: Language (en-IN, hi-IN, ta-IN, etc.)
            sample_rate: Audio sample rate in Hz
            
        Returns:
            dict: {
                "success": bool,
                "text": str,
                "confidence": float,
                "language": str
            }
        """
        try:
            print(f"🎤 Transcribing audio (language: {language_code})...")
            
            # CONVERT MP3 TO WAV IF NEEDED
            audio_content, actual_sample_rate = self._convert_to_wav(audio_content)
            
            if audio_content is None:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "error": "Failed to convert audio format"
                }
            
            # Use detected sample rate if available
            if actual_sample_rate:
                sample_rate = actual_sample_rate
            
            # Configure audio
            audio = speech_v1.RecognitionAudio(content=audio_content)
            
            # Configure recognition
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model="default",
                use_enhanced=True,
                # Banking-specific keywords
                speech_contexts=[
                    speech_v1.SpeechContext(
                        phrases=[
                            "balance", "transfer", "account", "rupees",
                            "deposit", "withdraw", "beneficiary", "transaction",
                            "mom", "mother", "dad", "father", "brother", "sister"
                        ]
                    )
                ]
            )
            
            # Call Google API
            response = self.speech_client.recognize(config=config, audio=audio)
            
            # Process results
            if not response.results:
                print("⚠️ No speech detected")
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "error": "No speech detected in audio"
                }
            
            # Get best result
            result = response.results[0]
            alternative = result.alternatives[0]
            
            text = alternative.transcript
            confidence = alternative.confidence
            
            print(f"✅ Transcribed: '{text}'")
            print(f"✅ Confidence: {confidence * 100:.1f}%")
            
            return {
                "success": True,
                "text": text,
                "confidence": confidence,
                "language": language_code
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Transcription error: {error_msg}")
            
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "error": error_msg
            }
    
    
    def _convert_to_wav(self, audio_content: bytes) -> tuple:
        """
        Convert MP3/other formats to WAV (LINEAR16) for Google STT
        
        Args:
            audio_content: Audio bytes (any format)
            
        Returns:
            tuple: (wav_bytes, sample_rate) or (None, None) if failed
        """
        try:
            # Check if already WAV format
            if audio_content[:4] == b'RIFF' and audio_content[8:12] == b'WAVE':
                print("   ✅ Audio is already in WAV format")
                
                # Extract sample rate from WAV header
                try:
                    sample_rate = int.from_bytes(audio_content[24:28], 'little')
                    print(f"   ✅ Detected sample rate: {sample_rate} Hz")
                    return audio_content, sample_rate
                except:
                    return audio_content, 16000  # Default to 16kHz
            
            # Need to convert - use pydub
            print("   🔄 Converting audio to WAV format...")
            
            try:
                from pydub import AudioSegment
            except ImportError:
                print("   ❌ pydub not installed. Installing now...")
                import subprocess
                subprocess.check_call(['pip', 'install', 'pydub'])
                from pydub import AudioSegment
            
            # Detect format and load
            if audio_content[:3] == b'ID3' or audio_content[:2] == b'\xff\xfb' or audio_content[:2] == b'\xff\xf3':
                # MP3 format
                print("   📦 Detected MP3 format")
                audio = AudioSegment.from_mp3(io.BytesIO(audio_content))
            else:
                # Try automatic detection
                print("   📦 Auto-detecting format...")
                audio = AudioSegment.from_file(io.BytesIO(audio_content))
            
            # Convert to LINEAR16 WAV (16kHz, mono, 16-bit)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Export to WAV bytes
            wav_io = io.BytesIO()
            audio.export(wav_io, format='wav')
            wav_bytes = wav_io.getvalue()
            
            print(f"   ✅ Converted to WAV: {len(wav_bytes):,} bytes (16kHz, mono, 16-bit)")
            return wav_bytes, 16000
            
        except ImportError as e:
            print(f"   ❌ Missing dependency: {e}")
            print("   💡 Install: pip install pydub")
            print("   💡 And FFmpeg: https://ffmpeg.org/download.html")
            return None, None
            
        except Exception as e:
            print(f"   ❌ Audio conversion failed: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    
    # =========================================
    # TEXT-TO-SPEECH METHODS
    # =========================================
    
    def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-IN",
        voice_gender: str = "FEMALE",
        output_format: str = "mp3"
    ) -> dict:
        """
        Convert text to speech using Google Text-to-Speech
        
        Args:
            text: Text to convert to speech
            language_code: Language (en-IN, hi-IN, etc.)
            voice_gender: MALE or FEMALE
            output_format: 'mp3' or 'wav'
            
        Returns:
            dict: {
                "success": bool,
                "audio_base64": str,
                "audio_content": bytes,
                "audio_format": str
            }
        """
        try:
            print(f"🔊 Synthesizing speech: '{text[:50]}...'")
            
            # Configure input
            synthesis_input = texttospeech_v1.SynthesisInput(text=text)
            
            # Configure voice
            if voice_gender.upper() == "FEMALE":
                gender = texttospeech_v1.SsmlVoiceGender.FEMALE
            else:
                gender = texttospeech_v1.SsmlVoiceGender.MALE
            
            # Try different voice names (Wavenet, Standard)
            voice_names = [
                f"{language_code}-Wavenet-A",
                f"{language_code}-Standard-A",
                f"{language_code}-Wavenet-B",
                f"{language_code}-Standard-B"
            ]
            
            last_error = None
            
            for voice_name in voice_names:
                try:
                    voice = texttospeech_v1.VoiceSelectionParams(
                        language_code=language_code,
                        name=voice_name,
                        ssml_gender=gender
                    )
                    
                    # Configure audio format
                    if output_format.lower() == "wav":
                        audio_encoding = texttospeech_v1.AudioEncoding.LINEAR16
                        sample_rate = 16000
                    else:
                        audio_encoding = texttospeech_v1.AudioEncoding.MP3
                        sample_rate = 24000
                    
                    audio_config = texttospeech_v1.AudioConfig(
                        audio_encoding=audio_encoding,
                        speaking_rate=1.0,
                        pitch=0.0,
                        volume_gain_db=0.0,
                        sample_rate_hertz=sample_rate
                    )
                    
                    # Call Google API
                    response = self.tts_client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                    
                    # Encode audio to base64
                    audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
                    
                    print(f"✅ Speech synthesized (voice: {voice_name}, format: {output_format})")
                    
                    return {
                        "success": True,
                        "audio_base64": audio_base64,
                        "audio_content": response.audio_content,
                        "audio_format": output_format
                    }
                    
                except Exception as e:
                    last_error = str(e)
                    continue
            
            # If all voices failed
            raise Exception(f"All voice options failed. Last error: {last_error}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Speech synthesis error: {error_msg}")
            
            return {
                "success": False,
                "audio_base64": "",
                "error": error_msg
            }
    
    
    # =========================================
    # HELPER METHODS
    # =========================================
    
    def get_supported_languages(self) -> dict:
        """Get list of supported languages"""
        return {
            "en-IN": "English (India)",
            "hi-IN": "Hindi (India)",
            "ta-IN": "Tamil (India)",
            "te-IN": "Telugu (India)",
            "bn-IN": "Bengali (India)",
            "mr-IN": "Marathi (India)",
            "gu-IN": "Gujarati (India)",
            "kn-IN": "Kannada (India)",
            "ml-IN": "Malayalam (India)",
            "pa-IN": "Punjabi (India)"
        }
    
    def validate_audio(self, audio_content: bytes) -> bool:
        """Check if audio is valid"""
        return len(audio_content) > 0