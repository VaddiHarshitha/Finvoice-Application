import requests
import json

BASE_URL = "http://localhost:8000"

# Language mapping: text language → voice language
LANGUAGE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN"
}

# Comprehensive multilingual test cases
TEST_CASES = {
    "English": {
        "code": "en",
        "tests": [
            {"message": "What's my balance?", "intent": "CHECK_BALANCE"},
            {"message": "Send 5000 to Mom", "intent": "FUND_TRANSFER"},
            {"message": "Who can I send money to?", "intent": "LIST_BENEFICIARIES"},
            {"message": "Show my last 3 transactions", "intent": "TRANSACTION_HISTORY"},
        ]
    },
    "Hindi (हिंदी)": {
        "code": "hi",
        "tests": [
            {"message": "मेरा बैलेंस क्या है?", "intent": "CHECK_BALANCE", "translation": "What is my balance?"},
            {"message": "माँ को 5000 भेजें", "intent": "FUND_TRANSFER", "translation": "Send 5000 to Mom"},
            {"message": "मैं किसे पैसे भेज सकता हूं?", "intent": "LIST_BENEFICIARIES", "translation": "Who can I send money to?"},
            {"message": "मेरे आखिरी 3 लेनदेन दिखाएं", "intent": "TRANSACTION_HISTORY", "translation": "Show my last 3 transactions"},
        ]
    },
    "Telugu (తెలుగు)": {
        "code": "te",
        "tests": [
            {"message": "నా బ్యాలెన్స్ ఎంత?", "intent": "CHECK_BALANCE", "translation": "What is my balance?"},
            {"message": "అమ్మకు 5000 పంపండి", "intent": "FUND_TRANSFER", "translation": "Send 5000 to Mom"},
            {"message": "నేను ఎవరికి డబ్బు పంపగలను?", "intent": "LIST_BENEFICIARIES", "translation": "Who can I send money to?"},
        ]
    },
    "Tamil (தமிழ்)": {
        "code": "ta",
        "tests": [
            {"message": "என் இருப்பு என்ன?", "intent": "CHECK_BALANCE", "translation": "What is my balance?"},
            {"message": "அம்மாவுக்கு 5000 அனுப்பு", "intent": "FUND_TRANSFER", "translation": "Send 5000 to Mom"},
            {"message": "நான் யாருக்கு பணம் அனுப்பலாம்?", "intent": "LIST_BENEFICIARIES", "translation": "Who can I send money to?"},
        ]
    },
    "Bengali (বাংলা)": {
        "code": "bn",
        "tests": [
            {"message": "আমার ব্যালেন্স কত?", "intent": "CHECK_BALANCE", "translation": "What is my balance?"},
            {"message": "মা কে 5000 পাঠান", "intent": "FUND_TRANSFER", "translation": "Send 5000 to Mom"},
        ]
    },
    "Marathi (मराठी)": {
        "code": "mr",
        "tests": [
            {"message": "माझं बॅलन्स किती आहे?", "intent": "CHECK_BALANCE", "translation": "What is my balance?"},
            {"message": "आईला 5000 पाठवा", "intent": "FUND_TRANSFER", "translation": "Send 5000 to Mom"},
        ]
    }
}

def test_text_endpoint():
    """Test text chat endpoint with multiple languages"""
    print("\n" + "="*80)
    print("🧪 TESTING TEXT CHAT ENDPOINT (/api/chat)")
    print("="*80)
    
    total_tests = 0
    passed_tests = 0
    
    for language_name, language_data in TEST_CASES.items():
        lang_code = language_data["code"]
        tests = language_data["tests"]
        
        print(f"\n{'='*80}")
        print(f"🌍 Testing: {language_name} (Code: {lang_code})")
        print('='*80)
        
        for i, test in enumerate(tests, 1):
            total_tests += 1
            message = test["message"]
            expected_intent = test["intent"]
            translation = test.get("translation", "")
            
            print(f"\n[Test {i}/{len(tests)}]")
            print(f"📝 Message: {message}")
            if translation:
                print(f"🔤 Translation: {translation}")
            
            try:
                # Make API call
                response = requests.post(
                    f"{BASE_URL}/api/chat",
                    data={
                        "message": message,
                        "user_id": "user001",
                        "language": lang_code
                    }
                )
                
                result = response.json()
                
                # Check results
                success = result.get("success")
                intent = result.get("intent")
                response_text = result.get("response", "")
                detected_lang = result.get("detected_language", "unknown")
                translated_text = result.get("translated_text")
                
                intent_match = intent == expected_intent
                passed = success and intent_match
                
                if passed:
                    passed_tests += 1
                
                # Display results
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"\nStatus: {status}")
                print(f"Success: {success}")
                print(f"Expected Intent: {expected_intent}")
                print(f"Actual Intent: {intent}")
                print(f"Detected Language: {detected_lang}")
                if translated_text:
                    print(f"Translated to English: {translated_text}")
                print(f"Response: {response_text[:150]}...")
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {total_tests - passed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("="*80)


def test_language_endpoint():
    """Test the /api/languages endpoint"""
    print("\n" + "="*80)
    print("🧪 TESTING LANGUAGES ENDPOINT")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/languages")
        result = response.json()
        
        print("\n✅ Voice Languages:")
        for code, name in result["voice_languages"].items():
            print(f"  • {code}: {name}")
        
        print("\n✅ Text Languages:")
        for code, name in result["text_languages"].items():
            print(f"  • {code}: {name}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🌍 FINVOICE MULTILINGUAL API TESTING SUITE")
    print("="*80)
    
    # Test language endpoint
    test_language_endpoint()
    
    # Test text chat with multiple languages
    test_text_endpoint()
    
    print("\n✅ All tests completed!\n")