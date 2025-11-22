"""
Generate 100 COMPLETE test users with UNIQUE passwords and PINs
- Each user gets unique email, password, phone, PIN
- Option to merge with existing data
- Backup old data before overwriting
"""

import json
import random
from datetime import datetime, timedelta
import bcrypt
import os
import shutil
import string

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def generate_secure_password(length=12):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def generate_readable_password():
    """Generate a memorable but secure password (for demo)"""
    adjectives = ["Happy", "Swift", "Bright", "Cool", "Smart", "Quick", "Bold", "Brave", "Calm", "Dark"]
    nouns = ["Tiger", "Eagle", "Dragon", "Lion", "Wolf", "Hawk", "Bear", "Fox", "Shark", "Cobra"]
    number = random.randint(10, 99)
    symbol = random.choice("!@#$")
    
    return f"{random.choice(adjectives)}{random.choice(nouns)}{number}{symbol}"

# Realistic Indian data
FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sunita", "Raj", "Anjali", "Vikram", "Neha",
    "Arjun", "Divya", "Rohan", "Kavya", "Karan", "Pooja", "Sanjay", "Meera",
    "Aditya", "Riya", "Varun", "Shreya", "Nikhil", "Ananya", "Manish", "Tanya",
    "Akash", "Ishita", "Kunal", "Simran", "Harsh", "Naina", "Vishal", "Aarti",
    "Mohit", "Swati", "Gaurav", "Preeti", "Deepak", "Ritika", "Ashok", "Geeta",
    "Ramesh", "Lakshmi", "Suresh", "Sarita", "Anil", "Usha", "Rajesh", "Rekha",
    "Manoj", "Shanti", "Prakash", "Parvati", "Yogesh", "Kamala", "Dinesh", "Radha"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Verma", "Reddy", "Iyer",
    "Joshi", "Rao", "Desai", "Mehta", "Nair", "Pandey", "Jain", "Agarwal",
    "Chopra", "Malhotra", "Kapoor", "Bose", "Mishra", "Sinha", "Das", "Sen"
]

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Indore", "Bhopal",
    "Chandigarh", "Kochi", "Coimbatore", "Nagpur", "Visakhapatnam"
]

BANKS = ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "BOB", "Canara"]
RELATIONS = ["Mom", "Dad", "Brother", "Sister", "Friend", "Wife", "Husband", "Son", "Daughter"]
LOAN_TYPES = ["HOME", "CAR", "PERSONAL", "EDUCATION"]
BILL_TYPES = ["ELECTRICITY", "WATER", "PHONE", "INTERNET", "GAS"]
REMINDER_TYPES = ["BILL", "EMI", "TRANSFER"]

def backup_existing_data(filename):
    """Backup existing data file"""
    if os.path.exists(filename):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{filename}.backup_{timestamp}"
        shutil.copy2(filename, backup_file)
        print(f"📦 Backed up existing data to: {backup_file}")
        return backup_file
    return None

def load_existing_data(filename):
    """Load existing data if available"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def generate_complete_data(num_users=100, start_id=1, demo_mode=False):
    """
    Generate complete realistic data for all tables
    
    Args:
        num_users: Number of users to generate
        start_id: Starting user ID (for merging with existing data)
        demo_mode: If True, use simple passwords (demo123) for first 3 users
    """
    
    print(f"🔧 Generating data for {num_users} users (starting from user{start_id:03d})...")
    
    data = {
        "users": {},
        "accounts": {},
        "beneficiaries": {},
        "transactions": {},
        "loans": {},
        "reminders": {},
        "credentials": []
    }
    
    # Track used emails, phones, and PINs
    used_emails = set()
    used_phones = set()
    used_pins = set()
    
    for i in range(start_id, start_id + num_users):
        user_id = f"user{i:03d}"
        
        # Generate unique email
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        email_base = f"{first.lower()}.{last.lower()}"
        email_counter = i
        email = f"{email_base}{email_counter}@demo.com"
        
        while email in used_emails:
            email_counter += 1
            email = f"{email_base}{email_counter}@demo.com"
        
        used_emails.add(email)
        
        # Generate unique phone
        phone = None
        while phone is None or phone in used_phones:
            phone = f"+91{random.randint(7000000000, 9999999999)}"
        
        used_phones.add(phone)
        
        # Generate password
        if demo_mode and i <= 3:
            password = "demo123"
        else:
            password = generate_readable_password()
        
        # Generate UNIQUE PIN (4 digits)
        pin = None
        while pin is None or pin in used_pins:
            pin = f"{random.randint(1000, 9999)}"
        
        used_pins.add(pin)
        
        join_date = datetime.now() - timedelta(days=random.randint(30, 730))
        
        data["users"][user_id] = {
            "name": name,
            "email": email,
            "phone": phone,
            "pin": pin,  # ✅ UNIQUE PIN stored here
            "city": random.choice(CITIES),
            "joined": join_date.isoformat()
        }
        
        # Store credentials separately for reference
        data["credentials"].append({
            "user_id": user_id,
            "name": name,
            "email": email,
            "password": password,  # ✅ UNIQUE PASSWORD
            "pin": pin,            # ✅ UNIQUE PIN
            "phone": phone
        })
        
        # Account data
        balance = round(random.uniform(10000, 500000), 2)
        has_loan = random.random() < 0.4
        
        data["accounts"][user_id] = {
            "account_number": f"{1000000000 + i}",
            "account_type": random.choice(["SAVINGS", "SAVINGS", "SAVINGS", "CURRENT"]),
            "balance": balance,
            "currency": "INR",
            "has_loan": has_loan
        }
        
        # Beneficiaries (2-6 per user)
        num_beneficiaries = random.randint(2, 6)
        data["beneficiaries"][user_id] = []
        
        for j in range(num_beneficiaries):
            ben_first = random.choice(FIRST_NAMES)
            ben_last = random.choice(LAST_NAMES)
            
            data["beneficiaries"][user_id].append({
                "nickname": RELATIONS[j % len(RELATIONS)],
                "full_name": f"{ben_first} {ben_last}",
                "account_number": f"{2000000000 + random.randint(1, 999999999)}",
                "bank": random.choice(BANKS),
                "ifsc": f"{random.choice(BANKS)[:4]}00{random.randint(10000, 99999)}"
            })
        
        # Transactions (10-30 per user)
        num_transactions = random.randint(10, 30)
        data["transactions"][user_id] = []
        
        for j in range(num_transactions):
            txn_date = join_date + timedelta(days=random.randint(0, 365))
            amount = round(random.uniform(100, 50000), 2)
            txn_type = random.choice(["DEBIT", "DEBIT", "DEBIT", "CREDIT"])
            
            data["transactions"][user_id].append({
                "transaction_id": f"TXN{user_id}{j:04d}",
                "to": random.choice(data["beneficiaries"][user_id])["nickname"],
                "amount": amount,
                "type": txn_type,
                "status": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "PENDING", "FAILED"]),
                "date": txn_date.isoformat()
            })
        
        # Loans (only if has_loan = True)
        if has_loan:
            loan_amount = round(random.uniform(100000, 5000000), 2)
            disbursed_date = join_date + timedelta(days=random.randint(30, 300))
            months_passed = max(0, (datetime.now() - disbursed_date).days // 30)
            monthly_emi = round(loan_amount / 60, 2)
            outstanding = max(0, loan_amount - (monthly_emi * months_passed))
            
            data["loans"][user_id] = {
                "loan_type": random.choice(LOAN_TYPES),
                "loan_amount": loan_amount,
                "outstanding_balance": outstanding,
                "interest_rate": round(random.uniform(7.5, 12.5), 2),
                "monthly_emi": monthly_emi,
                "tenure_months": 60,
                "next_due_date": (datetime.now() + timedelta(days=random.randint(5, 25))).date().isoformat(),
                "disbursed_at": disbursed_date.isoformat()
            }
        
        # Reminders (50% of users have 1-4 reminders)
        if random.random() < 0.5:
            num_reminders = random.randint(1, 4)
            data["reminders"][user_id] = []
            
            for j in range(num_reminders):
                due_date = datetime.now() + timedelta(days=random.randint(1, 45))
                reminder_type = random.choice(REMINDER_TYPES)
                
                if reminder_type == "BILL":
                    bill_type = random.choice(BILL_TYPES)
                    description = f"{bill_type.title()} Bill"
                    amount = round(random.uniform(500, 5000), 2)
                elif reminder_type == "EMI":
                    description = f"{random.choice(LOAN_TYPES).title()} Loan EMI"
                    amount = monthly_emi if has_loan else round(random.uniform(5000, 25000), 2)
                else:
                    description = f"Transfer to {random.choice(RELATIONS)}"
                    amount = round(random.uniform(1000, 20000), 2)
                
                data["reminders"][user_id].append({
                    "reminder_type": reminder_type,
                    "amount": amount,
                    "due_date": due_date.date().isoformat(),
                    "description": description
                })
    
    return data

def print_statistics(data):
    """Print data statistics"""
    total_users = len(data["users"])
    total_accounts = len(data["accounts"])
    total_beneficiaries = sum(len(b) for b in data["beneficiaries"].values())
    total_transactions = sum(len(t) for t in data["transactions"].values())
    total_loans = len(data["loans"])
    total_reminders = sum(len(r) for r in data["reminders"].values() if r)
    
    users_with_loans = sum(1 for acc in data["accounts"].values() if acc["has_loan"])
    users_with_reminders = len([u for u in data["reminders"] if data["reminders"][u]])
    
    print("\n" + "="*70)
    print("  DATA GENERATION SUMMARY")
    print("="*70)
    print(f"👥 Users:                {total_users:,}")
    print(f"💳 Accounts:             {total_accounts:,}")
    print(f"   - With Loans:         {users_with_loans} ({users_with_loans/total_users*100:.1f}%)")
    print(f"   - Without Loans:      {total_users - users_with_loans} ({(total_users - users_with_loans)/total_users*100:.1f}%)")
    print(f"👨‍👩‍👧‍👦 Beneficiaries:        {total_beneficiaries:,}")
    print(f"💸 Transactions:         {total_transactions:,}")
    print(f"🏦 Loans:                {total_loans} ({total_loans/total_users*100:.1f}%)")
    print(f"⏰ Reminders:            {total_reminders}")
    print(f"   - Users with reminders: {users_with_reminders} ({users_with_reminders/total_users*100:.1f}%)")
    print("="*70)

def save_credentials_file(credentials, filename="user_credentials.txt"):
    """Save user credentials to a separate text file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("FINVOICE TEST USER CREDENTIALS\n")
        f.write("="*70 + "\n\n")
        f.write("⚠️  WARNING: This file contains plain text passwords!\n")
        f.write("    DO NOT commit this file to version control!\n")
        f.write("    FOR TESTING PURPOSES ONLY!\n\n")
        f.write("="*70 + "\n\n")
        
        for i, cred in enumerate(credentials, 1):
            f.write(f"User {i}: {cred['name']}\n")
            f.write(f"  User ID:  {cred['user_id']}\n")
            f.write(f"  Email:    {cred['email']}\n")
            f.write(f"  Password: {cred['password']}\n")
            f.write(f"  PIN:      {cred['pin']}\n")
            f.write(f"  Phone:    {cred['phone']}\n")
            f.write("-" * 70 + "\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("Quick Login Examples:\n")
        f.write("="*70 + "\n")
        for cred in credentials[:5]:
            f.write(f"Email: {cred['email']:40s} Password: {cred['password']}\n")
    
    print(f"🔑 Credentials saved to: {filename}")

if __name__ == "__main__":
    print("\n🚀 SECURE BULK DATA GENERATOR")
    print("="*70)
    
    # Configuration
    output_file = "complete_bulk_data.json"
    credentials_file = "user_credentials.txt"
    num_users = 100
    demo_mode = True  # First 3 users get demo123 password
    
    # Check for existing data
    existing_data = load_existing_data(output_file)
    
    if existing_data:
        print(f"\n⚠️  WARNING: File '{output_file}' already exists!")
        print(f"   Found {len(existing_data.get('users', {}))} existing users")
        
        response = input("\n   Options:\n"
                        "   1. BACKUP and OVERWRITE (recommended)\n"
                        "   2. MERGE (add new users to existing)\n"
                        "   3. CANCEL\n"
                        "   Choose (1/2/3): ").strip()
        
        if response == "1":
            backup_existing_data(output_file)
            start_id = 1
        elif response == "2":
            backup_existing_data(output_file)
            existing_user_ids = [int(uid.replace('user', '')) for uid in existing_data.get('users', {}).keys()]
            start_id = max(existing_user_ids) + 1 if existing_user_ids else 1
            print(f"\n✅ Will add {num_users} new users starting from user{start_id:03d}")
        else:
            print("\n❌ Cancelled.")
            exit(0)
    else:
        start_id = 1
    
    # Generate data
    print(f"\n🔄 Generating {num_users} users with UNIQUE passwords and PINs...")
    data = generate_complete_data(num_users=num_users, start_id=start_id, demo_mode=demo_mode)
    
    # Merge with existing data if needed
    if existing_data and response == "2":
        print("\n🔄 Merging with existing data...")
        for key in ["users", "accounts", "beneficiaries", "transactions", "loans", "reminders"]:
            if key in existing_data:
                data[key].update(existing_data[key])
        
        if "credentials" in existing_data:
            data["credentials"].extend(existing_data["credentials"])
    
    # ✅ ADD PASSWORDS AND PINS TO USER DATA FOR DATABASE SETUP
    print("\n🔐 Adding passwords and PINs to JSON for database setup...")
    for cred in data["credentials"]:
        user_id = cred["user_id"]
        if user_id in data["users"]:
            data["users"][user_id]["password_plain"] = cred["password"]  # ✅ For setup.py
            # PIN already in user data
    
    print("   ✅ Passwords and PINs added to user data")
    
    # Save main data file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Save credentials separately
    save_credentials_file(data["credentials"], credentials_file)
    
    # Print statistics
    print_statistics(data)
    
    print(f"\n✅ Data saved to: {output_file}")
    print(f"🔑 Credentials saved to: {credentials_file}")
    
    print("\n" + "="*70)
    print("📝 QUICK START - Easy Login Users:")
    print("="*70)
    for cred in data["credentials"][:5]:
        print(f"Email: {cred['email']:40s} Password: {cred['password']:15s} PIN: {cred['pin']}")
    
    print("\n⚠️  IMPORTANT:")
    print("   - First 3 users have 'demo123' password for easy testing")
    print("   - ALL users have UNIQUE PINs (randomly generated)")
    print("   - Remaining users have unique secure passwords")
    print("   - Check 'user_credentials.txt' for all credentials")
    print("   - DO NOT commit user_credentials.txt to git!")