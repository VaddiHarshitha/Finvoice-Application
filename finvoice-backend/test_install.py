print("Testing imports...")

try:
    import fastapi
    print("✅ FastAPI installed")
except:
    print("❌ FastAPI missing")

try:
    from google.cloud import speech_v1
    print("✅ Google Speech installed")
except:
    print("❌ Google Speech missing")

try:
    from google.cloud import texttospeech_v1
    print("✅ Google TTS installed")
except:
    print("❌ Google TTS missing")

print("\n✅ All packages installed successfully!")