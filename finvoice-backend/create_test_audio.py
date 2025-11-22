"""
Create Test Audio Files - Compatible with VoiceProcessor
Works with audio_base64 response format
"""

import os
import sys
sys.path.append('src')

from services.voice_processor import VoiceProcessor
import base64


def create_test_audio_files():
    """Generate test audio files in multiple languages"""
    
    print("\n" + "="*70)
    print("🎙️ CREATING TEST AUDIO FILES")
    print("="*70 + "\n")
    
    # Initialize voice processor
    try:
        voice_processor = VoiceProcessor()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Create test_audio directory
    os.makedirs('test_audio', exist_ok=True)
    
    # Test cases
    test_cases = [
        # ========================================
        # ENGLISH TESTS (4 tests)
        # ========================================
        {
            'id': 'EN-01',
            'text': "What is my account balance?",
            'language': 'en-IN',
            'filename': 'test_audio/01_en_balance.mp3',
            'description': 'English - Balance Query',
            'expected_intent': 'CHECK_BALANCE'
        },
        {
            'id': 'EN-02',
            'text': "Send five thousand rupees to Mom",
            'language': 'en-IN',
            'filename': 'test_audio/02_en_transfer.mp3',
            'description': 'English - Transfer Request',
            'expected_intent': 'FUND_TRANSFER'
        },
        {
            'id': 'EN-03',
            'text': "Show my last three transactions",
            'language': 'en-IN',
            'filename': 'test_audio/03_en_history.mp3',
            'description': 'English - Transaction History',
            'expected_intent': 'TRANSACTION_HISTORY'
        },
        {
            'id': 'EN-04',
            'text': "Who can I send money to?",
            'language': 'en-IN',
            'filename': 'test_audio/04_en_beneficiaries.mp3',
            'description': 'English - List Beneficiaries',
            'expected_intent': 'LIST_BENEFICIARIES'
        },
        
        # ========================================
        # HINDI TESTS (4 tests)
        # ========================================
        {
            'id': 'HI-01',
            'text': "मेरा बैलेंस क्या है?",
            'language': 'hi-IN',
            'filename': 'test_audio/05_hi_balance.mp3',
            'description': 'Hindi - Balance Query',
            'expected_intent': 'CHECK_BALANCE'
        },
        {
            'id': 'HI-02',
            'text': "माँ को पांच हजार रुपये भेजें",
            'language': 'hi-IN',
            'filename': 'test_audio/06_hi_transfer.mp3',
            'description': 'Hindi - Transfer Request',
            'expected_intent': 'FUND_TRANSFER'
        },
        {
            'id': 'HI-03',
            'text': "मेरे आखिरी तीन लेनदेन दिखाएं",
            'language': 'hi-IN',
            'filename': 'test_audio/07_hi_history.mp3',
            'description': 'Hindi - Transaction History',
            'expected_intent': 'TRANSACTION_HISTORY'
        },
        {
            'id': 'HI-04',
            'text': "मैं किसे पैसे भेज सकता हूं?",
            'language': 'hi-IN',
            'filename': 'test_audio/08_hi_beneficiaries.mp3',
            'description': 'Hindi - List Beneficiaries',
            'expected_intent': 'LIST_BENEFICIARIES'
        },
        
        # ========================================
        # TAMIL TESTS (2 tests) - Using Standard voice
        # ========================================
        {
            'id': 'TA-01',
            'text': "என் இருப்பு என்ன?",
            'language': 'ta-IN',
            'filename': 'test_audio/09_ta_balance.mp3',
            'description': 'Tamil - Balance Query',
            'expected_intent': 'CHECK_BALANCE',
            'use_standard': True  # Tamil might not have Wavenet
        },
        {
            'id': 'TA-02',
            'text': "அம்மாவுக்கு ஐயாயிரம் ரூபாய் அனுப்பு",
            'language': 'ta-IN',
            'filename': 'test_audio/10_ta_transfer.mp3',
            'description': 'Tamil - Transfer Request',
            'expected_intent': 'FUND_TRANSFER',
            'use_standard': True
        },
        
        # ========================================
        # BENGALI TESTS (2 tests)
        # ========================================
        {
            'id': 'BN-01',
            'text': "আমার ব্যালেন্স কত?",
            'language': 'bn-IN',
            'filename': 'test_audio/11_bn_balance.mp3',
            'description': 'Bengali - Balance Query',
            'expected_intent': 'CHECK_BALANCE'
        },
        {
            'id': 'BN-02',
            'text': "মা কে পাঁচ হাজার টাকা পাঠান",
            'language': 'bn-IN',
            'filename': 'test_audio/12_bn_transfer.mp3',
            'description': 'Bengali - Transfer Request',
            'expected_intent': 'FUND_TRANSFER'
        },
        
        # ========================================
        # MARATHI TESTS (2 tests)
        # ========================================
        {
            'id': 'MR-01',
            'text': "माझं बॅलन्स किती आहे?",
            'language': 'mr-IN',
            'filename': 'test_audio/13_mr_balance.mp3',
            'description': 'Marathi - Balance Query',
            'expected_intent': 'CHECK_BALANCE'
        },
        {
            'id': 'MR-02',
            'text': "आईला पाच हजार रुपये पाठवा",
            'language': 'mr-IN',
            'filename': 'test_audio/14_mr_transfer.mp3',
            'description': 'Marathi - Transfer Request',
            'expected_intent': 'FUND_TRANSFER'
        },
        
        # ========================================
        # EDGE CASES (2 tests)
        # ========================================
        {
            'id': 'EDGE-01',
            'text': "Transfer three thousand to Brother",
            'language': 'en-IN',
            'filename': 'test_audio/15_edge_brother_transfer.mp3',
            'description': 'Edge - Different Recipient',
            'expected_intent': 'FUND_TRANSFER'
        },
        {
            'id': 'EDGE-02',
            'text': "Send ten thousand rupees to Dad",
            'language': 'en-IN',
            'filename': 'test_audio/16_edge_large_amount.mp3',
            'description': 'Edge - Large Amount',
            'expected_intent': 'FUND_TRANSFER'
        }
    ]
    
    print(f"Total test cases: {len(test_cases)}\n")
    
    success_count = 0
    failed_tests = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test['id']}: {test['description']}")
        print(f"   Text: '{test['text']}'")
        print(f"   Language: {test['language']}")
        
        try:
            # Generate speech
            result = voice_processor.synthesize_speech(
                text=test['text'],
                language_code=test['language']
            )
            
            if result['success']:
                # Decode base64 audio
                audio_bytes = base64.b64decode(result['audio_base64'])
                
                # Save as MP3
                with open(test['filename'], 'wb') as f:
                    f.write(audio_bytes)
                
                file_size = len(audio_bytes)
                print(f"   ✅ Created: {test['filename']}")
                print(f"   💾 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)\n")
                success_count += 1
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"   ❌ Failed: {error_msg}\n")
                failed_tests.append({
                    'id': test['id'],
                    'error': error_msg
                })
        
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            failed_tests.append({
                'id': test['id'],
                'error': str(e)
            })
    
    # Summary
    print("="*70)
    print(f"📊 SUMMARY")
    print("="*70)
    print(f"Total: {len(test_cases)}")
    print(f"Success: {success_count} ✅")
    print(f"Failed: {len(failed_tests)} ❌")
    print(f"Success Rate: {(success_count/len(test_cases)*100):.1f}%")
    print("="*70)
    
    if failed_tests:
        print("\n⚠️  Failed Tests:")
        for fail in failed_tests:
            print(f"   - {fail['id']}: {fail['error']}")
    
    if success_count > 0:
        print("\n✅ SUCCESS! Audio files created in: test_audio/")
        print("\n🎵 Test a file:")
        print("   start test_audio\\01_en_balance.mp3")
        
        print("\n🌐 Now test via API:")
        print("   1. Start server: python main.py")
        print("   2. Open: http://localhost:8000/docs")
        print("   3. Find: POST /api/voice/process")
        print("   4. Upload files from test_audio/ folder")
        
        # Create test checklist
        create_test_checklist(test_cases, success_count)


def create_test_checklist(test_cases, success_count):
    """Create a simple test checklist"""
    
    checklist = f"""# 🧪 Voice API Testing Checklist

## Progress: 0/{success_count} Completed

**Generated:** {success_count} test audio files
**Server:** http://localhost:8000/docs
**Endpoint:** POST /api/voice/process

---

## 📋 Test Instructions

1. Start server: `python main.py`
2. Open: http://localhost:8000/docs
3. Find: `POST /api/voice/process`
4. Click: "Try it out"
5. For each test:
   - Upload audio file
   - Set `user_id`: `user001`
   - Set `language` (as shown below)
   - Click "Execute"
   - Verify response
   - Check box when done

---

## Test Cases

"""
    
    for test in test_cases:
        if os.path.exists(test['filename']):
            checklist += f"""
### [{test['id']}] {test['description']}
- [ ] **File:** `{test['filename']}`
- **Language:** `{test['language']}`
- **Expected Intent:** `{test['expected_intent']}`
- **Test Input:** "{test['text']}"

"""
    
    checklist += """
---

## ✅ Expected Response Format
```json
{
  "success": true,
  "language": "en-IN",
  "transcribed_text": "What is my account balance?",
  "intent": "CHECK_BALANCE",
  "confidence": 0.95,
  "response_text": "Balance: ₹75,230.50 in SAVINGS account",
  "response_audio": "base64_encoded_audio..."
}
```

---

## 📊 Test Results

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| English | 4 | ___ | ___ |
| Hindi | 4 | ___ | ___ |
| Tamil | 2 | ___ | ___ |
| Bengali | 2 | ___ | ___ |
| Marathi | 2 | ___ | ___ |
| Edge Cases | 2 | ___ | ___ |
| **TOTAL** | **16** | **___** | **___** |

---

## 🎯 Success Criteria

- ✅ All tests return `"success": true`
- ✅ Intent matches expected
- ✅ Confidence > 0.85
- ✅ Response in correct language
- ✅ Response time < 5 seconds

---

**Notes:**
(Add any observations or issues here)

"""
    
    with open('TEST_CHECKLIST.md', 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print("\n📋 Created: TEST_CHECKLIST.md")


if __name__ == "__main__":
    create_test_audio_files()