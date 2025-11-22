from services.voice_processor import VoiceProcessor

# Initialize
vp = VoiceProcessor()

# Test 1: Check supported languages
print("\n📋 Supported Languages:")
for code, name in vp.get_supported_languages().items():
    print(f"  {code}: {name}")

# Test 2: Text-to-Speech
print("\n🔊 Testing Text-to-Speech...")
result = vp.synthesize_speech(
    text="Hello! Your account balance is rupees forty five thousand two hundred thirty.",
    language_code="en-IN"
)

if result['success']:
    print("✅ TTS Success!")
    print(f"✅ Audio length: {len(result['audio_base64'])} characters")
    
    # Save audio for testing
    import base64
    audio_bytes = base64.b64decode(result['audio_base64'])
    with open('test_output.mp3', 'wb') as f:
        f.write(audio_bytes)
    print("✅ Saved as: test_output.mp3")
else:
    print(f"❌ TTS Failed: {result['error']}")

print("\n✅ Voice Processor tests complete!")