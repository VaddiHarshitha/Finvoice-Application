"""
Test voice API with multiple users from credentials file
"""

import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_AUDIO_DIR = Path("test_audio")

def load_test_users():
    """Load users from user_credentials.txt"""
    users = []
    
    try:
        with open('database/user_credentials.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            current_user = {}
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and separator lines
                if not line or line.startswith('=') or line.startswith('-') or line.startswith('⚠️'):
                    continue
                
                # Parse "User N: Name" format (but not "User ID:")
                if line.startswith("User ") and ":" in line and not line.startswith("User ID:"):
                    # Save previous user if exists
                    if current_user and 'user_id' in current_user:
                        users.append(current_user)
                    # Extract name from "User 1: Sarita Sen"
                    name = line.split(":", 1)[1].strip()
                    current_user = {"name": name}
                elif line.startswith("User ID:"):
                    current_user["user_id"] = line.split(":", 1)[1].strip()
                elif line.startswith("Email:"):
                    current_user["email"] = line.split(":", 1)[1].strip()
                elif line.startswith("Password:"):
                    current_user["password"] = line.split(":", 1)[1].strip()
                elif line.startswith("PIN:"):
                    current_user["pin"] = line.split(":", 1)[1].strip()
                elif line.startswith("Phone:"):
                    current_user["phone"] = line.split(":", 1)[1].strip()
            
            # Add the last user
            if current_user and 'user_id' in current_user:
                users.append(current_user)
        
        # Validate users have required fields
        valid_users = []
        for user in users:
            if all(key in user for key in ['user_id', 'name', 'email', 'password']):
                valid_users.append(user)
        
        return valid_users[:3]  # Return first 3 users for testing
    
    except FileNotFoundError:
        print("❌ user_credentials.txt not found")
        return []
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        return []


def login(email, password):
    """Login and get token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            raise Exception(f"Login failed ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")


def test_voice_for_user(user, audio_file, token, language="en-IN"):
    """Test voice processing for a specific user with pre-authenticated token"""
    email = user['email']
    name = user.get('name', 'Unknown')
    
    # Determine language from filename
    filename = audio_file.name.lower()
    if '_hi_' in filename or 'hindi' in filename:
        language = "hi-IN"
    elif '_ta_' in filename or 'tamil' in filename:
        language = "ta-IN"
    elif '_te_' in filename or 'telugu' in filename:
        language = "te-IN"
    elif '_bn_' in filename or 'bengali' in filename:
        language = "bn-IN"
    elif '_mr_' in filename or 'marathi' in filename:
        language = "mr-IN"
    elif '_en_' in filename or 'english' in filename:
        language = "en-IN"
    
    print(f"   📧 Email: {email}")
    print(f"   🗣️  Language: {language}")
    
    try:
        # Process voice (no login needed - using existing token)
        print(f"   🎤 Processing audio...", end=" ")
        
        with open(audio_file, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/api/voice/process",
                headers={"Authorization": f"Bearer {token}"},
                files={"audio": f},
                data={"language": language},
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅")
            print(f"   📝 Transcribed: {data.get('transcribed_text', 'N/A')}")
            print(f"   🎯 Intent: {data.get('intent', 'N/A')}")
            
            response_text = data.get('response_text', '')
            if len(response_text) > 80:
                print(f"   💬 Response: {response_text[:80]}...")
            else:
                print(f"   💬 Response: {response_text}")
            
            confidence = data.get('confidence', {})
            overall = confidence.get('overall', 0)
            print(f"   📊 Confidence: {overall*100:.1f}%")
            
            return True
        else:
            print("❌")
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f"   ⚠️  Error ({response.status_code}): {error_data.get('error', response.text[:100])}")
            return False
            
    except Exception as e:
        print(f"❌")
        print(f"   ⚠️  Exception: {str(e)[:100]}")
        return False


def get_audio_files():
    """Get all audio files from test directory"""
    if not TEST_AUDIO_DIR.exists():
        print(f"❌ Audio directory not found: {TEST_AUDIO_DIR}")
        return []
    
    # Get all mp3 and wav files
    audio_files = list(TEST_AUDIO_DIR.glob("*.mp3")) + list(TEST_AUDIO_DIR.glob("*.wav"))
    
    # Sort by filename
    audio_files.sort()
    
    return audio_files


if __name__ == "__main__":
    print("\n🎤 MULTI-USER & MULTI-AUDIO VOICE TESTING")
    print("="*70)
    
    # Load test users
    print("\n📋 Loading test users...")
    test_users = load_test_users()
    
    if not test_users:
        print("❌ No users loaded. Exiting.")
        exit(1)
    
    print(f"✅ Loaded {len(test_users)} users for testing")
    
    # Get all audio files
    print("\n🎵 Loading audio files...")
    audio_files = get_audio_files()
    
    if not audio_files:
        print(f"❌ No audio files found in {TEST_AUDIO_DIR}")
        print(f"   Please add .mp3 or .wav files to the directory")
        exit(1)
    
    print(f"✅ Found {len(audio_files)} audio file(s):")
    for audio_file in audio_files:
        print(f"   • {audio_file.name}")
    
    # Run tests
    print("\n" + "="*70)
    print("RUNNING TESTS")
    print("="*70)
    
    results = []
    test_count = 0
    
    # Login once per user and cache tokens
    user_tokens = {}
    
    print("\n🔐 Authenticating users...")
    for user in test_users:
        try:
            print(f"   • {user['name']}...", end=" ")
            token = login(user['email'], user['password'])
            user_tokens[user['email']] = token
            print("✅")
        except Exception as e:
            print(f"❌ {str(e)[:50]}")
            user_tokens[user['email']] = None
    
    # Test each user with each audio file
    for user in test_users:
        token = user_tokens.get(user['email'])
        
        if not token:
            print(f"\n⚠️  Skipping {user['name']}: No authentication token")
            for audio_file in audio_files:
                results.append({
                    'user_name': user['name'],
                    'user_email': user['email'],
                    'audio_file': audio_file.name,
                    'success': False
                })
            continue
        
        for audio_file in audio_files:
            test_count += 1
            print(f"\n{'='*70}")
            print(f"TEST {test_count}/{len(test_users) * len(audio_files)}")
            print(f"User: {user['name']} | Audio: {audio_file.name}")
            print(f"{'='*70}")
            
            success = test_voice_for_user(user, audio_file, token)
            results.append({
                'user_name': user['name'],
                'user_email': user['email'],
                'audio_file': audio_file.name,
                'success': success
            })
            
            # Small delay to avoid overwhelming the server
            import time
            time.sleep(0.5)
    
    # Summary by user
    print("\n" + "="*70)
    print("  TEST SUMMARY BY USER")
    print("="*70)
    
    for user in test_users:
        user_results = [r for r in results if r['user_email'] == user['email']]
        user_passed = sum(1 for r in user_results if r['success'])
        user_total = len(user_results)
        
        status = "✅" if user_passed == user_total else "⚠️"
        print(f"\n{status} {user['name']} ({user['email']})")
        print(f"   Passed: {user_passed}/{user_total}")
        
        # Show which audio files passed/failed
        for result in user_results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"   {status_icon} {result['audio_file']}")
    
    # Summary by audio file
    print("\n" + "="*70)
    print("  TEST SUMMARY BY AUDIO FILE")
    print("="*70)
    
    for audio_file in audio_files:
        file_results = [r for r in results if r['audio_file'] == audio_file.name]
        file_passed = sum(1 for r in file_results if r['success'])
        file_total = len(file_results)
        
        status = "✅" if file_passed == file_total else "⚠️"
        print(f"{status} {audio_file.name}: {file_passed}/{file_total} passed")
    
    # Overall summary
    print("\n" + "="*70)
    print("  OVERALL SUMMARY")
    print("="*70)
    
    total_tests = len(results)
    total_passed = sum(1 for r in results if r['success'])
    total_failed = total_tests - total_passed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Users: {len(test_users)}")
    print(f"Audio Files: {len(audio_files)}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Pass Rate: {pass_rate:.1f}%")
    
    print(f"\n{'='*70}")
    
    if total_failed == 0:
        print("\n🎉 ALL VOICE TESTS PASSED!")
    else:
        print(f"\n⚠️  {total_failed} test(s) failed")
    
    print(f"\n{'='*70}")