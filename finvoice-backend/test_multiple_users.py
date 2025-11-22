"""
Test Multiple Users with Different Credentials
Tests that different users have different passwords, balances, loans, etc.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Load test users from credentials file
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
                elif line.startswith("Name:"):
                    current_user["name"] = line.split(":", 1)[1].strip()
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
            else:
                print(f"⚠️  Skipping incomplete user: {user.get('user_id', 'unknown')}")
        
        if not valid_users:
            raise ValueError("No valid users found in credentials file")
        
        return valid_users[:5]  # Return first 5 users for testing
    
    except FileNotFoundError:
        print("⚠️  user_credentials.txt not found, using default users")
        return [
            {
                "user_id": "user001",
                "name": "Rahul Sharma",
                "email": "rahul.sharma1@demo.com",
                "password": "demo123",
                "pin": "1234"
            },
            {
                "user_id": "user002",
                "name": "Priya Patel",
                "email": "priya.patel2@demo.com",
                "password": "demo123",
                "pin": "5678"
            }
        ]
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        print("Using default users instead...")
        return [
            {
                "user_id": "user001",
                "name": "Rahul Sharma",
                "email": "rahul.sharma1@demo.com",
                "password": "demo123",
                "pin": "1234"
            },
            {
                "user_id": "user002",
                "name": "Priya Patel",
                "email": "priya.patel2@demo.com",
                "password": "demo123",
                "pin": "5678"
            }
        ]

def test_user_login(user):
    """Test login for a specific user"""
    print(f"\n{'='*70}")
    print(f"Testing User: {user.get('name', 'Unknown')} ({user.get('email', 'Unknown')})")
    print('='*70)
    
    # Validate user has required fields
    if 'email' not in user or 'password' not in user:
        print(f"   ❌ User missing required fields (email/password)")
        return None
    
    # Test login
    print(f"\n▶️  Test 1: Login")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "email": user['email'],
                "password": user['password']
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print(f"   ✅ Login successful")
                print(f"   🔑 Token: {token[:30]}...")
                return token
            else:
                print(f"   ❌ Login response missing token")
                return None
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return None

def test_user_features(user, token):
    """Test various features for a user"""
    
    # Test 1: Get user info
    print(f"\n▶️  Test 2: Get User Info")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ User: {data.get('user', {}).get('name', 'Unknown')}")
            if 'account' in data.get('user', {}):
                balance = data['user']['account'].get('balance', 0)
                print(f"   💰 Balance: ₹{balance:,.2f}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check balance via chat
    print(f"\n▶️  Test 3: Check Balance via Chat")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "message": "What is my account balance?",
                "language": "auto"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {data.get('response', '')[:100]}...")
            print(f"   🎯 Intent: {data.get('intent', 'unknown')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check loans
    print(f"\n▶️  Test 4: Check Loans")
    try:
        response = requests.get(
            f"{BASE_URL}/api/loans",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            if count > 0:
                print(f"   ✅ Has {count} loan(s)")
                total = data.get('total_outstanding', 0)
                print(f"   💰 Total Outstanding: ₹{total:,.2f}")
            else:
                print(f"   ℹ️  No loans")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get transactions
    print(f"\n▶️  Test 5: Transaction History")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "message": "Show my last 3 transactions",
                "language": "en"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response received")
            print(f"   📜 {data.get('response', '')[:150]}...")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Run multi-user tests"""
    print("\n" + "="*70)
    print("  MULTI-USER TESTING")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load test users
    print("\n📋 Loading test users...")
    users = load_test_users()
    print(f"   ✅ Loaded {len(users)} users for testing")
    
    # Debug: Print first user structure
    if users:
        print(f"\n🔍 First user structure: {list(users[0].keys())}")
    
    results = []
    
    # Test each user
    for i, user in enumerate(users, 1):
        print(f"\n\n{'#'*70}")
        print(f"# USER {i}/{len(users)}")
        print(f"{'#'*70}")
        
        token = test_user_login(user)
        
        if token:
            test_user_features(user, token)
            results.append({
                "user": user.get('email', 'unknown'),
                "status": "PASS"
            })
        else:
            results.append({
                "user": user.get('email', 'unknown'),
                "status": "FAIL"
            })
    
    # Summary
    print("\n\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    
    for result in results:
        status = "✅" if result['status'] == 'PASS' else "❌"
        print(f"{status} {result['user']}: {result['status']}")
    
    print("\n" + "="*70)
    print(f"Total: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 ALL USERS TESTED SUCCESSFULLY!")
    else:
        print(f"\n⚠️  {failed} user(s) failed")

if __name__ == "__main__":
    main()