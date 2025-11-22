"""
Debug script to see the actual format of user_credentials.txt
"""

def debug_credentials():
    """Show the first few users in the credentials file"""
    try:
        with open('database/user_credentials.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("="*70)
        print("CREDENTIALS FILE DEBUG")
        print("="*70)
        print(f"\nTotal lines: {len(lines)}")
        print("\nFirst 30 lines:")
        print("-"*70)
        
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:3d}: {repr(line)}")
        
        print("\n" + "="*70)
        print("PARSING TEST")
        print("="*70)
        
        current_user = {}
        users = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and separator lines
            if not line or line.startswith('=') or line.startswith('-') or line.startswith('⚠️'):
                continue
            
            print(f"\nLine {line_num}: {repr(line)}")
            
            # Parse "User N: Name" format (but not "User ID:")
            if line.startswith("User ") and ":" in line and not line.startswith("User ID:"):
                # Save previous user if exists
                if current_user and 'user_id' in current_user:
                    print(f"  → Saving user: {current_user}")
                    users.append(current_user)
                # Extract name from "User 1: Sarita Sen"
                name = line.split(":", 1)[1].strip()
                current_user = {"name": name}
                print(f"  → New user started with name: {name}")
            elif line.startswith("User ID:"):
                current_user["user_id"] = line.split(":", 1)[1].strip()
                print(f"  → Added user_id: {current_user['user_id']}")
            elif line.startswith("Name:"):
                current_user["name"] = line.split(":", 1)[1].strip()
                print(f"  → Added name: {current_user['name']}")
            elif line.startswith("Email:"):
                current_user["email"] = line.split(":", 1)[1].strip()
                print(f"  → Added email: {current_user['email']}")
            elif line.startswith("Password:"):
                current_user["password"] = line.split(":", 1)[1].strip()
                print(f"  → Added password: {current_user['password']}")
            elif line.startswith("PIN:"):
                current_user["pin"] = line.split(":", 1)[1].strip()
                print(f"  → Added PIN: {current_user['pin']}")
            elif line.startswith("Phone:"):
                current_user["phone"] = line.split(":", 1)[1].strip()
                print(f"  → Added phone: {current_user['phone']}")
            else:
                print(f"  → Skipped: {line[:50]}")
            
            # Stop after first 2 users for debugging
            if len(users) >= 2:
                break
        
        # Add last user
        if current_user:
            print(f"\n  → Saving last user: {current_user}")
            users.append(current_user)
        
        print("\n" + "="*70)
        print("PARSED USERS")
        print("="*70)
        
        for i, user in enumerate(users, 1):
            print(f"\nUser {i}:")
            for key, value in user.items():
                print(f"  {key}: {value}")
            
            # Check completeness
            missing = []
            for required in ['user_id', 'name', 'email', 'password']:
                if required not in user:
                    missing.append(required)
            
            if missing:
                print(f"  ⚠️  Missing fields: {missing}")
            else:
                print(f"  ✅ Complete")
        
    except FileNotFoundError:
        print("❌ File not found: database/user_credentials.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_credentials()