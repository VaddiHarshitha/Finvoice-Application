"""
Performance Monitoring Tests
Tests performance tracking and analysis features
"""

import requests
import time

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def make_test_requests():
    """Make various test requests to generate performance data"""
    print(f"\n{Colors.YELLOW}📊 Generating test traffic...{Colors.END}\n")
    
    # Get token
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"email": "rahul@demo.com", "password": "demo123"}
    )
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make various requests
    endpoints = [
        ("GET", "/api/health", None, None),
        ("GET", "/", None, None),
        ("POST", "/api/chat", {"message": "What is my balance?", "user_id": "user001"}, None),
        ("POST", "/api/chat", {"message": "Show my last 5 transactions", "user_id": "user001"}, None),
        ("GET", "/api/conversations", None, headers),
        ("GET", "/api/security/events", None, headers),
        ("GET", "/api/languages", None, None),
        ("GET", "/api/stats", None, None),
    ]
    
    for method, endpoint, data, auth_headers in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", data=data, headers=auth_headers)
            
            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {method} {endpoint}: {response.status_code}")
            
            time.sleep(0.1)  # Small delay
        except Exception as e:
            print(f"❌ {method} {endpoint}: {str(e)}")
    
    print()


def test_performance_summary():
    """Test performance summary endpoint"""
    print(f"{Colors.BLUE}{'='*60}")
    print("📈 PERFORMANCE SUMMARY")
    print(f"{'='*60}{Colors.END}\n")
    
    response = requests.get(f"{BASE_URL}/api/performance/summary")
    
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        
        print(f"{Colors.GREEN}✅ Performance Summary:{Colors.END}")
        print(f"   Total Requests: {summary.get('total_requests', 0)}")
        print(f"   Total Endpoints: {summary.get('total_endpoints', 0)}")
        print(f"   Avg Response Time: {summary.get('avg_response_time', 0)}s")
        print(f"   Median Response Time: {summary.get('median_response_time', 0)}s")
        print(f"   Total Errors: {summary.get('total_errors', 0)}")
        print(f"   Error Rate: {summary.get('overall_error_rate', 0)}%")
        
        print(f"\n{Colors.YELLOW}💡 Recommendations:{Colors.END}")
        for rec in data.get('recommendations', []):
            print(f"   {rec}")
        
    else:
        print(f"{Colors.RED}❌ Failed: {response.status_code}{Colors.END}")
    
    print()


def test_slow_endpoints():
    """Test slow endpoints detection"""
    print(f"{Colors.BLUE}{'='*60}")
    print("⚠️ SLOW ENDPOINTS")
    print(f"{'='*60}{Colors.END}\n")
    
    response = requests.get(f"{BASE_URL}/api/performance/slow?threshold=0.5")
    
    if response.status_code == 200:
        data = response.json()
        slow = data.get('slow_endpoints', [])
        
        if slow:
            print(f"{Colors.YELLOW}⚠️ Found {len(slow)} slow endpoints:{Colors.END}")
            for endpoint in slow[:5]:
                print(f"   • {endpoint['endpoint']}")
                print(f"     Avg: {endpoint['avg_time']}s, Max: {endpoint['max_time']}s")
        else:
            print(f"{Colors.GREEN}✅ No slow endpoints found!{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Failed: {response.status_code}{Colors.END}")
    
    print()


def test_popular_endpoints():
    """Test most used endpoints"""
    print(f"{Colors.BLUE}{'='*60}")
    print("🔥 MOST POPULAR ENDPOINTS")
    print(f"{'='*60}{Colors.END}\n")
    
    response = requests.get(f"{BASE_URL}/api/performance/popular?limit=10")
    
    if response.status_code == 200:
        data = response.json()
        popular = data.get('popular_endpoints', [])
        
        print(f"{Colors.GREEN}Top {len(popular)} endpoints by traffic:{Colors.END}")
        for i, endpoint in enumerate(popular, 1):
            print(f"   {i}. {endpoint['endpoint']}")
            print(f"      Calls: {endpoint['calls']} ({endpoint['percentage']}%)")
    else:
        print(f"{Colors.RED}❌ Failed: {response.status_code}{Colors.END}")
    
    print()


def test_endpoint_details():
    """Test detailed endpoint stats"""
    print(f"{Colors.BLUE}{'='*60}")
    print("🔍 ENDPOINT DETAILS")
    print(f"{'='*60}{Colors.END}\n")
    
    endpoint_to_check = "/api/chat"
    response = requests.get(f"{BASE_URL}/api/performance/endpoint{endpoint_to_check}")
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get('stats', {})
        
        print(f"{Colors.GREEN}Stats for {endpoint_to_check}:{Colors.END}")
        print(f"   Total Calls: {stats.get('total_calls', 0)}")
        print(f"   Avg Time: {stats.get('avg_time', 0)}s")
        print(f"   Median Time: {stats.get('median_time', 0)}s")
        print(f"   Min Time: {stats.get('min_time', 0)}s")
        print(f"   Max Time: {stats.get('max_time', 0)}s")
        print(f"   P95: {stats.get('p95_time', 0)}s")
        print(f"   P99: {stats.get('p99_time', 0)}s")
        print(f"   Errors: {stats.get('errors', 0)}")
        print(f"   Error Rate: {stats.get('error_rate', 0)}%")
    else:
        print(f"{Colors.RED}❌ Failed: {response.status_code}{Colors.END}")
    
    print()


def test_full_metrics():
    """Test full performance metrics"""
    print(f"{Colors.BLUE}{'='*60}")
    print("📊 FULL PERFORMANCE METRICS")
    print(f"{'='*60}{Colors.END}\n")
    
    response = requests.get(f"{BASE_URL}/api/performance")
    
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        endpoints = data.get('endpoints', {})
        
        print(f"{Colors.GREEN}Overall Summary:{Colors.END}")
        print(f"   Tracked Endpoints: {len(endpoints)}")
        print(f"   Total Requests: {summary.get('total_requests', 0)}")
        print(f"   Avg Response: {summary.get('avg_response_time', 0)}s")
        
        print(f"\n{Colors.YELLOW}Top 3 Slowest:{Colors.END}")
        sorted_endpoints = sorted(
            endpoints.items(),
            key=lambda x: x[1].get('avg_time', 0),
            reverse=True
        )
        for endpoint, stats in sorted_endpoints[:3]:
            print(f"   • {endpoint}: {stats.get('avg_time', 0)}s avg")
    else:
        print(f"{Colors.RED}❌ Failed: {response.status_code}{Colors.END}")
    
    print()


if __name__ == "__main__":
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 PERFORMANCE MONITORING TESTS")
    print(f"{'='*60}{Colors.END}")
    
    # Generate test traffic
    make_test_requests()
    
    # Run tests
    test_performance_summary()
    test_slow_endpoints()
    test_popular_endpoints()
    test_endpoint_details()
    test_full_metrics()
    
    print(f"{Colors.BLUE}{'='*60}")
    print(f"{Colors.GREEN}✅ All performance tests complete!{Colors.END}")
    print(f"{'='*60}{Colors.END}\n")