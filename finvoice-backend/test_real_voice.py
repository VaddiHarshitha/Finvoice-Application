"""
Test Real Voice Processing
Tests: Audio → STT → AI → Banking → TTS → Audio
"""

import os
import sys
sys.path.append('src')

from services.voice_processor import VoiceProcessor
from services.agentic_nlp import AgenticNLP
from services.banking_service import BankingService
import glob


def test_voice_processing():
    """Test complete voice processing pipeline"""
    
    print("\n" + "="*70)
    print("🎤 TESTING REAL VOICE PROCESSING PIPELINE")
    print("="*70 + "\n")
    
    # Initialize services
    print("Initializing services...")
    try:
        voice_processor = VoiceProcessor()
        banking_service = BankingService()
        agentic_nlp = AgenticNLP(banking_service)
        print("✅ All services initialized\n")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Find test audio files
    audio_files = glob.glob('test_audio/*.mp3')
    
    if not audio_files:
        print("⚠️  No test audio files found!")
        print("\n📝 Run this first: python create_test_audio.py")
        return
    
    print(f"📁 Found {len(audio_files)} test audio files\n")
    
    # Test each audio file
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print("="*70)
        print(f"TEST {i}/{len(audio_files)}: {os.path.basename(audio_file)}")
        print("="*70)
        
        # Extract language from filename (e.g., 'hi_balance.mp3' → 'hi-IN')
        filename = os.path.basename(audio_file)
        lang_code = filename.split('_')[0]
        language_map = {
            'en': 'en-IN',
            'hi': 'hi-IN',
            'te': 'te-IN',
            'ta': 'ta-IN',
            'bn': 'bn-IN',
            'mr': 'mr-IN'
        }
        language = language_map.get(lang_code, 'en-IN')
        
        try:
            # STEP 1: Read audio file
            print(f"\n[1/6] 📂 Reading audio file...")
            with open(audio_file, 'rb') as f:
                audio_bytes = f.read()
            print(f"   ✅ Read {len(audio_bytes)} bytes")
            
            # STEP 2: Speech-to-Text
            print(f"\n[2/6] 🎤 Converting speech to text ({language})...")
            stt_result = voice_processor.transcribe_audio(
                audio_content=audio_bytes,
                language_code=language
            )
            
            if not stt_result['success']:
                print(f"   ❌ STT Failed: {stt_result.get('error')}")
                results.append({
                    'file': filename,
                    'status': 'FAILED',
                    'error': 'STT Failed'
                })
                continue
            
            transcribed_text = stt_result['text']
            confidence = stt_result['confidence']
            print(f"   ✅ Transcribed: '{transcribed_text}'")
            print(f"   ✅ Confidence: {confidence * 100:.1f}%")
            
            # STEP 3: AI Processing
            print(f"\n[3/6] 🤖 Processing with AI Agent...")
            lang_short = language.split('-')[0]
            ai_result = agentic_nlp.process(
                text=transcribed_text,
                user_id='user001',
                language=lang_short
            )
            
            if not ai_result['success']:
                print(f"   ❌ AI Failed: {ai_result.get('error')}")
                results.append({
                    'file': filename,
                    'status': 'FAILED',
                    'error': 'AI Failed'
                })
                continue
            
            intent = ai_result['intent']
            response_text = ai_result['response']
            print(f"   ✅ Intent: {intent}")
            print(f"   ✅ Response: '{response_text[:80]}...'")
            
            # STEP 4: Text-to-Speech
            print(f"\n[4/6] 🔊 Converting response to speech...")
            tts_result = voice_processor.synthesize_speech(
                text=response_text,
                language_code=language
            )
            
            if not tts_result['success']:
                print(f"   ❌ TTS Failed: {tts_result.get('error')}")
                results.append({
                    'file': filename,
                    'transcribed': transcribed_text,
                    'intent': intent,
                    'status': 'PARTIAL',
                    'note': 'STT+AI OK, TTS Failed'
                })
                continue
            
            # STEP 5: Save response audio
            print(f"\n[5/6] 💾 Saving response audio...")
            output_file = audio_file.replace('.mp3', '_response.mp3')
            with open(output_file, 'wb') as f:
                f.write(tts_result['audio_content'])
            print(f"   ✅ Saved: {output_file}")
            
            # STEP 6: Summary
            print(f"\n[6/6] ✅ TEST PASSED!")
            results.append({
                'file': filename,
                'language': language,
                'transcribed': transcribed_text,
                'intent': intent,
                'response': response_text[:50] + '...',
                'output': os.path.basename(output_file),
                'status': 'PASSED'
            })
            
        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'file': filename,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r['status'] == 'PASSED')
    failed = len(results) - passed
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/len(results)*100) if results else 0:.1f}%")
    
    print("\n" + "="*70)
    print("DETAILED RESULTS")
    print("="*70)
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result['file']}")
        print(f"    Status: {result['status']}")
        
        if result['status'] == 'PASSED':
            print(f"    Language: {result['language']}")
            print(f"    Transcribed: '{result['transcribed']}'")
            print(f"    Intent: {result['intent']}")
            print(f"    Response: '{result['response']}'")
            print(f"    Output Audio: {result['output']}")
        elif 'error' in result:
            print(f"    Error: {result['error']}")
    
    print("\n" + "="*70)
    print("✅ Voice processing test complete!")
    print("="*70)
    
    if passed > 0:
        print("\n🎵 Play the *_response.mp3 files to hear AI responses!")


if __name__ == "__main__":
    test_voice_processing()