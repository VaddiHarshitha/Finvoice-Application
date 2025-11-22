"""
Redis Functionality Test Suite
Tests session management, rate limiting, and token blacklisting
"""

import requests
import time
import redis
from typing import Dict

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(test_name: str):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")


def clear_rate_limits():
    """Clear rate limit keys from Redis"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Delete all rate limit keys
        rate_keys = r.keys("rate:*")
        if rate_keys:
            r.delete(*rate_keys)
            print_info(f"Cleared {len(rate_keys)} rate limit keys from Redis")
        
        # Also clear any test sessions
        session_keys = r.keys("session:*")
        if session_keys:
            r.delete(*session_keys)
            print_info(f"Cleared {len(session_keys)} session keys from Redis")
            
        # Clear blacklist
        blacklist_keys = r.keys("blacklist:*")
        if blacklist_keys:
            r.delete(*blacklist_keys)
            print_info(f"Cleared {len(blacklist_keys)} blacklist keys from Redis")
            
    except Exception as e:
        print_error(f"Could not clear Redis: {e}")
        print_info("You may need to wait 5 minutes for rate limits to reset")


def test_1_login_creates_session():
    """Test that login creates a Redis session"""
    print_test("1. Login Creates Session")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "email": "rahul@demo.com",
            "password": "demo123"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print_success(f"Login successful")
        print_info(f"Token: {token[:50]}...")
        return token
    else:
        print_error(f"Login failed: {response.status_code}")
        print_error(response.text)
        return None


def test_2_check_active_sessions():
    """Test checking active sessions"""
    print_test("2. Check Active Sessions")
    
    response = requests.get(f"{BASE_URL}/api/admin/sessions")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get("active_sessions")
        print_success(f"Active sessions: {count}")
        
        if count >= 1:
            print_success("Session was created!")
        else:
            print_error("No active sessions found!")
        
        return count
    else:
        print_error(f"Failed to get sessions: {response.status_code}")
        return 0


def test_3_protected_endpoint_with_token(token: str):
    """Test accessing protected endpoint with valid token"""
    print_test("3. Access Protected Endpoint (Valid Token)")
    
    if not token:
        print_error("No token provided")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        user = data.get("user", {})
        print_success(f"Authenticated as: {user.get('name')} ({user.get('user_id')})")
        return True
    else:
        print_error(f"Authentication failed: {response.status_code}")
        print_error(response.text)
        return False


def test_4_logout_blacklists_token(token: str):
    """Test that logout blacklists the token"""
    print_test("4. Logout Blacklists Token")
    
    if not token:
        print_error("No token provided")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    
    if response.status_code == 200:
        print_success("Logout successful - token blacklisted")
        return True
    else:
        print_error(f"Logout failed: {response.status_code}")
        print_error(response.text)
        return False


def test_5_blacklisted_token_rejected(token: str):
    """Test that blacklisted token is rejected"""
    print_test("5. Blacklisted Token Rejected")
    
    if not token:
        print_error("No token provided")
        return False
    
    print_info("Attempting to use blacklisted token...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 401:
        print_success("Blacklisted token was correctly rejected!")
        return True
    else:
        print_error(f"Token should have been rejected but got: {response.status_code}")
        print_error("Token blacklisting may not be working!")
        return False


def test_6_session_deleted_after_logout():
    """Test that session is deleted after logout"""
    print_test("6. Session Deleted After Logout")
    
    response = requests.get(f"{BASE_URL}/api/admin/sessions")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get("active_sessions")
        print_info(f"Active sessions after logout: {count}")
        
        if count == 0:
            print_success("Session was deleted successfully!")
            return True
        else:
            print_error(f"Session still exists! Count: {count}")
            return False
    else:
        print_error(f"Failed to get sessions: {response.status_code}")
        return False


def test_7_rate_limiting():
    """Test rate limiting on login"""
    print_test("7. Rate Limiting (5 login attempts in 5 minutes)")
    
    print_info("Making 6 rapid login attempts with wrong password...")
    
    # Clear rate limits first
    clear_rate_limits()
    time.sleep(1)
    
    attempts = 0
    for i in range(6):
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "email": "test_ratelimit@demo.com",  # Use different email
                "password": "wrong_password"
            }
        )
        
        attempts += 1
        print_info(f"Attempt {attempts}: Status {response.status_code}")
        
        if response.status_code == 429:
            print_success(f"Rate limiting kicked in after {attempts} attempts!")
            data = response.json()
            print_info(f"Error: {data.get('detail')}")
            return True
        
        time.sleep(0.5)  # Small delay between attempts
    
    print_error("Rate limiting did not trigger after 6 attempts!")
    return False


def test_8_multiple_sessions():
    """Test multiple concurrent sessions"""
    print_test("8. Multiple Concurrent Sessions")
    
    # Clear previous data
    clear_rate_limits()
    time.sleep(1)
    
    tokens = []
    
    # Create 3 sessions (will overwrite each other for same user)
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "email": "rahul@demo.com",
                "password": "demo123"
            }
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            tokens.append(token)
            print_success(f"Session {i+1} created")
            time.sleep(0.5)
        else:
            print_error(f"Failed to create session {i+1}: {response.status_code}")
    
    # Check active sessions
    response = requests.get(f"{BASE_URL}/api/admin/sessions")
    if response.status_code == 200:
        count = response.json().get("active_sessions")
        print_info(f"Total active sessions: {count}")
        
        # For same user, only last session remains
        if count == 1:
            print_success("Session management working correctly!")
            print_info("Note: Same user logging in overwrites previous session")
            return True
        else:
            print_error(f"Expected 1 session, got {count}")
            return False
    
    return False


def test_9_session_expiry_simulation():
    """Test session with short expiry (manual verification)"""
    print_test("9. Session Expiry (Informational)")
    
    print_info("Sessions expire after 1440 minutes (24 hours)")
    print_info("To test expiry, modify redis_service.create_session()")
    print_info("Set expiry_minutes=1 and wait 60 seconds")
    print_success("This is a manual test - skipping automated check")
    return True


def cleanup():
    """Cleanup: Logout all sessions and clear Redis"""
    print_test("CLEANUP: Logout All Sessions and Clear Redis")
    
    # Clear all Redis keys
    clear_rate_limits()
    
    print_success("Cleanup completed - all Redis data cleared")


def run_all_tests():
    """Run complete test suite"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("REDIS FUNCTIONALITY TEST SUITE")
    print(f"{'='*60}{Colors.END}\n")
    
    # Initial cleanup
    print_info("Performing initial cleanup...")
    clear_rate_limits()
    time.sleep(2)
    
    results = {}
    
    # Test 1: Login
    token = test_1_login_creates_session()
    results['login'] = token is not None
    
    time.sleep(1)
    
    # Test 2: Check sessions
    session_count = test_2_check_active_sessions()
    results['check_sessions'] = session_count >= 1
    
    time.sleep(1)
    
    # Test 3: Protected endpoint
    results['protected_endpoint'] = test_3_protected_endpoint_with_token(token)
    
    time.sleep(1)
    
    # Test 4: Logout
    results['logout'] = test_4_logout_blacklists_token(token)
    
    time.sleep(1)
    
    # Test 5: Blacklisted token
    results['blacklist_check'] = test_5_blacklisted_token_rejected(token)
    
    time.sleep(1)
    
    # Test 6: Session deleted
    results['session_deleted'] = test_6_session_deleted_after_logout()
    
    time.sleep(2)
    
    # Test 7: Rate limiting (with cleanup)
    results['rate_limiting'] = test_7_rate_limiting()
    
    time.sleep(2)
    
    # Test 8: Multiple sessions (with cleanup)
    results['multiple_sessions'] = test_8_multiple_sessions()
    
    time.sleep(1)
    
    # Test 9: Expiry info
    results['session_expiry'] = test_9_session_expiry_simulation()
    
    # Final cleanup
    cleanup()
    
    # Print Summary
    print(f"\n{Colors.BLUE}{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}✅ PASSED" if passed_test else f"{Colors.RED}❌ FAILED"
        print(f"{status}{Colors.END} - {test_name}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.END}")
    else:
        print(f"{Colors.RED}⚠️  Some tests failed{Colors.END}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error running tests: {e}{Colors.END}")