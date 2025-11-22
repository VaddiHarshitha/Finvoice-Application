"""
Debug script to parse user_credentials.txt
Shows exactly what's being read
"""

from pathlib import Path

CREDENTIALS_FILE = Path("user_credentials.txt")

if not CREDENTIALS_FILE.exists():
    print("❌ File not found!")
    exit(1)

print(f"📄 Reading: {CREDENTIALS_FILE}")
print(f"📍 Full path: {CREDENTIALS_FILE.absolute()}")
print()

with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"📝 Total lines: {len(lines)}")
print()

# Show first 30 lines to understand format
print("="*70)
print("FIRST 30 LINES:")
print("="*70)
for i, line in enumerate(lines[:30], 1):
    print(f"{i:3d}: {repr(line[:80])}")

print()
print("="*70)

# Now try to parse
users = []
current_user = {}

for i, line in enumerate(lines, 1):
    original = line
    line = line.rstrip('\n\r')  # Remove only newlines, keep spaces
    
    # Skip truly empty lines
    if not line.strip():
        continue
    
    # Skip header lines
    if '=====' in line:
        continue
    if 'FINVOICE TEST USER CREDENTIALS' in line:
        continue
    if 'WARNING' in line:
        continue
    if 'DO NOT commit' in line:
        continue
    if 'FOR TESTING PURPOSES ONLY' in line:
        continue
    if 'Quick Login Examples:' in line:
        break  # Stop at the examples section
    
    # Check for "User X: Name" pattern
    if line.startswith('User ') and ': ' in line:
        # Save previous user
        if current_user and 'email' in current_user and 'password' in current_user:
            users.append(current_user)
            print(f"✅ Saved user {len(users)}: {current_user['name']}")
        
        # Start new user
        name = line.split(': ', 1)[1]
        current_user = {'name': name}
        print(f"🆕 Found user: {name}")
    
    # Check for field lines (start with spaces)
    elif line.startswith('  ') and ': ' in line:
        field_name = line.split(':', 1)[0].strip()
        field_value = line.split(':', 1)[1].strip()
        
        if field_name == 'User ID':
            current_user['user_id'] = field_value
        elif field_name == 'Email':
            current_user['email'] = field_value
            print(f"   📧 Email: {field_value}")
        elif field_name == 'Password':
            current_user['password'] = field_value
            print(f"   🔑 Password: {field_value}")
        elif field_name == 'PIN':
            current_user['pin'] = field_value
        elif field_name == 'Phone':
            current_user['phone'] = field_value
    
    # Separator line means user is complete
    elif line.startswith('------'):
        if current_user and 'email' in current_user and 'password' in current_user:
            users.append(current_user)
            print(f"✅ Saved user {len(users)}: {current_user['name']} (separator)")
            current_user = {}

# Last user
if current_user and 'email' in current_user and 'password' in current_user:
    users.append(current_user)
    print(f"✅ Saved last user: {current_user['name']}")

print()
print("="*70)
print(f"🎉 TOTAL USERS LOADED: {len(users)}")
print("="*70)

if users:
    print("\n📋 First 5 users:")
    for i, user in enumerate(users[:5], 1):
        print(f"\n{i}. {user.get('name', 'NO NAME')}")
        print(f"   User ID:  {user.get('user_id', 'MISSING')}")
        print(f"   Email:    {user.get('email', 'MISSING')}")
        print(f"   Password: {user.get('password', 'MISSING')}")
        print(f"   PIN:      {user.get('pin', 'MISSING')}")
else:
    print("\n❌ NO USERS FOUND!")
    print("\n🔍 Debugging tips:")
    print("1. Check if file format matches expected pattern")
    print("2. Look at the first 30 lines printed above")
    print("3. Verify 'User X: Name' pattern exists")
    print("4. Check for proper indentation on field lines")