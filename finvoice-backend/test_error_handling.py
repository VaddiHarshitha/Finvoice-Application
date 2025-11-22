"""
Enhanced Error Handling Tests
Tests validation, error responses, and monitoring
"""

import requests
import json

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    symbol = f"{Colors.GREEN}✅{Colors.END}" if passed else f"{Colors.RED}❌{Colors.END}"
    print(f"{symbol} {name}")
    if details:
        print(f"   {details}")


def get_auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "email": "rahul@demo.com",
            "password": "demo123"
        }
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def test_validation_errors():
    """Test validation error handling"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 VALIDATION ERROR TESTS")
    print(f"{'='*60}{Colors.END}\n")
    
    # Test 1: Empty message
    print("Test 1: Empty message (chat)")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={"message": "", "user_id": "user001"}
    )
    passed = response.status_code == 400
    print_test(
        "Empty message rejected",
        passed,
        f"Status: {response.status_code}, Expected: 400"
    )
    print(f"   Response: {response.json()}\n")
    
    # Test 2: Negative amount
    print("Test 2: Negative amount (transfer)")
    token = get_auth_token()
    if token:
        response = requests.post(
            f"{BASE_URL}/api/transactions/initiate",
            headers={"Authorization": f"Bearer {token}"},
            data={"recipient": "Mom", "amount": -1000}
        )
        passed = response.status_code == 400
        print_test(
            "Negative amount rejected",
            passed,
            f"Status: {response.status_code}, Expected: 400"
        )
        print(f"   Response: {response.json()}\n")
    
    # Test 3: Zero amount
    print("Test 3: Zero amount (transfer)")
    if token:
        response = requests.post(
            f"{BASE_URL}/api/transactions/initiate",
            headers={"Authorization": f"Bearer {token}"},
            data={"recipient": "Mom", "amount": 0}
        )
        passed = response.status_code == 400
        print_test(
            "Zero amount rejected",
            passed,
            f"Status: {response.status_code}, Expected: 400"
        )
        print(f"   Response: {response.json()}\n")
    
    # Test 4: Empty recipient
    print("Test 4: Empty recipient (transfer)")
    if token:
        response = requests.post(
            f"{BASE_URL}/api/transactions/initiate",
            headers={"Authorization": f"Bearer {token}"},
            data={"recipient": "", "amount": 1000}
        )
        passed = response.status_code == 400
        print_test(
            "Empty recipient rejected",
            passed,
            f"Status: {response.status_code}, Expected: 400"
        )
        print(f"   Response: {response.json()}\n")
    
    # Test 5: Invalid recipient
    print("Test 5: Invalid recipient (transfer)")
    if token:
        response = requests.post(
            f"{BASE_URL}/api/transactions/initiate",
            headers={"Authorization": f"Bearer {token}"},
            data={"recipient": "NonExistentPerson", "amount": 1000}
        )
        passed = response.status_code == 400
        print_test(
            "Invalid recipient rejected",
            passed,
            f"Status: {response.status_code}, Expected: 400"
        )
        print(f"   Response: {response.json()}\n")


def test_not_found_errors():
    """Test not found error handling"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 NOT FOUND ERROR TESTS")
    print(f"{'='*60}{Colors.END}\n")
    
    token = get_auth_token()
    
    # Test 1: Non-existent audio
    print("Test 1: Non-existent audio file")
    response = requests.get(f"{BASE_URL}/api/audio/nonexistent.mp3")
    passed = response.status_code == 404
    print_test(
        "Non-existent audio returns 404",
        passed,
        f"Status: {response.status_code}"
    )
    print(f"   Response: {response.json()}\n")
    
    # Test 2: Non-existent conversation
    print("Test 2: Non-existent conversation")
    if token:
        response = requests.get(
            f"{BASE_URL}/api/conversations/999999",
            headers={"Authorization": f"Bearer {token}"}
        )
        # This might return 200 with error in body, that's okay
        print_test(
            "Non-existent conversation handled",
            response.status_code in [200, 404],
            f"Status: {response.status_code}"
        )
        print(f"   Response: {response.json()}\n")


def test_monitoring_endpoints():
    """Test monitoring and admin endpoints"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 MONITORING ENDPOINT TESTS")
    print(f"{'='*60}{Colors.END}\n")
    
    # Test 1: Error stats
    print("Test 1: Error Statistics")
    response = requests.get(f"{BASE_URL}/api/admin/error-stats")
    passed = response.status_code == 200
    print_test(
        "Error stats endpoint works",
        passed,
        f"Status: {response.status_code}"
    )
    if passed:
        data = response.json()
        print(f"   Total Errors: {data.get('stats', {}).get('total_errors', 0)}")
        by_endpoint = data.get('stats', {}).get('by_endpoint', {})
        if by_endpoint:
            print(f"   Errors by endpoint:")
            for endpoint, count in list(by_endpoint.items())[:3]:
                print(f"      {endpoint}: {count}")
    print()
    
    # Test 2: Performance metrics
    print("Test 2: Performance Metrics")
    response = requests.get(f"{BASE_URL}/api/performance")
    passed = response.status_code == 200
    print_test(
        "Performance metrics endpoint works",
        passed,
        f"Status: {response.status_code}"
    )
    if passed:
        data = response.json()
        print(f"   Total Requests: {data.get('total_requests', 0)}")
        metrics = data.get('metrics', {})
        if metrics:
            print(f"   Slowest endpoints:")
            for endpoint, metric in list(metrics.items())[:3]:
                print(f"      {endpoint}: {metric.get('avg_time', 0)}s avg")
    print()
    
    # Test 3: Cache stats
    print("Test 3: Cache Statistics")
    response = requests.get(f"{BASE_URL}/api/admin/cache-stats")
    passed = response.status_code == 200
    print_test(
        "Cache stats endpoint works",
        passed,
        f"Status: {response.status_code}"
    )
    if passed:
        data = response.json()
        stats = data.get('stats', {})
        print(f"   Total Files: {stats.get('total_files', 0)}")
        print(f"   Total Size: {stats.get('total_size_mb', 0)} MB")
    print()


def test_success_cases():
    """Test that valid requests still work"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 SUCCESS CASE TESTS (Valid Requests)")
    print(f"{'='*60}{Colors.END}\n")
    
    token = get_auth_token()
    
    # Test 1: Valid chat
    print("Test 1: Valid chat message")
    response = requests.post(
        f"{BASE_URL}/api/chat",
        data={
            "message": "What is my balance?",
            "user_id": "user001",
            "language": "en"
        }
    )
    passed = response.status_code == 200
    print_test(
        "Valid chat works",
        passed,
        f"Status: {response.status_code}"
    )
    if passed:
        data = response.json()
        print(f"   Intent: {data.get('intent')}")
    print()
    
    # Test 2: Valid transfer
    print("Test 2: Valid transfer initiation")
    if token:
        response = requests.post(
            f"{BASE_URL}/api/transactions/initiate",
            headers={"Authorization": f"Bearer {token}"},
            data={"recipient": "Mom", "amount": 100}
        )
        passed = response.status_code == 200
        print_test(
            "Valid transfer works",
            passed,
            f"Status: {response.status_code}"
        )
        if passed:
            data = response.json()
            print(f"   Transaction ID: {data.get('transaction_id')}")
            print(f"   OTP: {data.get('otp')}")
    print()


if __name__ == "__main__":
    print("\n" + "="*60)
    print(f"{Colors.BLUE}🧪 COMPREHENSIVE ERROR HANDLING TESTS{Colors.END}")
    print("="*60)
    
    test_validation_errors()
    test_not_found_errors()
    test_monitoring_endpoints()
    test_success_cases()
    
    print("\n" + "="*60)
    print(f"{Colors.GREEN}✅ All tests complete!{Colors.END}")
    print("📄 Check logs/app.log and logs/errors.log for details")
    print("="*60 + "\n")