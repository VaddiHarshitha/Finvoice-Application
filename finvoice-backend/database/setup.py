import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import sys
from dotenv import load_dotenv
import json
import bcrypt

# Load environment from correct location
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "finvoice_db")
}

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_file_path(filename):
    """
    Smart path resolution - works whether script is run from:
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try current directory first
    path1 = os.path.join(script_dir, filename)
    if os.path.exists(path1):
        return path1
    
    # Try parent directory (if running from database folder)
    path2 = os.path.join(script_dir, '..', 'database', filename)
    if os.path.exists(path2):
        return path2
    
    # Try database subdirectory (if running from project root)
    path3 = os.path.join(script_dir, 'database', filename)
    if os.path.exists(path3):
        return path3
    
    return None

def create_database():
    """Create database if not exists"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        print(f" Database '{DB_CONFIG['database']}' created")
        
        cursor.close()
        conn.close()
    except psycopg2.errors.DuplicateDatabase:
        print(f"  Database '{DB_CONFIG['database']}' already exists")
    except Exception as e:
        print(f" Error creating database: {e}")

def create_tables(drop_existing=False):
    """Create all tables from schema.sql"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if drop_existing:
            print("  Dropping existing tables...")
            cursor.execute("""
                DROP TABLE IF EXISTS payment_reminders CASCADE;
                DROP TABLE IF EXISTS loans CASCADE;
                DROP TABLE IF EXISTS conversation_history CASCADE;
                DROP TABLE IF EXISTS voice_sessions CASCADE;
                DROP TABLE IF EXISTS security_events CASCADE;
                DROP TABLE IF EXISTS sessions CASCADE;
                DROP TABLE IF EXISTS pending_transactions CASCADE;
                DROP TABLE IF EXISTS transactions CASCADE;
                DROP TABLE IF EXISTS beneficiaries CASCADE;
                DROP TABLE IF EXISTS accounts CASCADE;
                DROP TABLE IF EXISTS users CASCADE;
            """)
            conn.commit()
            print(" Existing tables dropped")
        
        # Smart schema file detection
        schema_files = ['Schema.sql', 'schema.sql']
        schema_path = None
        
        for schema_file in schema_files:
            path = get_file_path(schema_file)
            if path:
                schema_path = path
                break
        
        if not schema_path:
            raise FileNotFoundError(
                f"Schema file not found! Tried:\n" + 
                "\n".join([f"  - {get_file_path(f) or f}" for f in schema_files])
            )
        
        print(f"📄 Reading schema from: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        cursor.execute(schema)
        conn.commit()
        
        print("All tables created successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n Created {len(tables)} tables:")
        for table in tables:
            print(f"   ✓ {table}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f" Error creating tables: {e}")
        import traceback
        traceback.print_exc()

def seed_complete_data():
"""Insert complete bulk data from JSON WITH UNIQUE PASSWORDS & PINS"""
    try:
        # Smart data file detection
        data_files = [
            'complete_bulk_data.json',
            'fake_bank_data.json'
        ]
        
        data_file = None
        for df in data_files:
            path = get_file_path(df)
            if path:
                data_file = path
                break
        
        if not data_file:
            print(f" Data file not found! Tried:")
            for df in data_files:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                print(f"   - {os.path.join(script_dir, df)}")
            print("\n Generate data first:")
            print("   python generate_complete_bulk_data.py")
            return
        
        print(f" Loading data from: {data_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n Inserting data...")
        
        # 1. INSERT USERS WITH UNIQUE PASSWORDS & PINS
        user_count = len(data['users'])
        print(f"👥 Inserting {user_count} users...")
        
        unique_password_count = 0
        unique_pin_count = 0
        
        for user_id, user_data in data['users'].items():
            #  Use plain password from JSON if available
            if 'password_plain' in user_data and user_data['password_plain']:
                password_hash = hash_password(user_data['password_plain'])
                unique_password_count += 1
            else:
                password_hash = hash_password("demo123")  # Fallback
            
            #  Use unique PIN from JSON
            pin = user_data.get('pin', '1234')
            pin_hash = hash_password(pin)
            if pin != '1234':
                unique_pin_count += 1
            
            cursor.execute("""
                INSERT INTO users (user_id, name, email, phone, password_hash, pin_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    password_hash = EXCLUDED.password_hash,
                    pin_hash = EXCLUDED.pin_hash
            """, (user_id, user_data['name'], user_data['email'],
                  user_data['phone'], password_hash, pin_hash))
        
        conn.commit()
        print(f"    {user_count} users inserted")
        print(f"    {unique_password_count} users have unique passwords")
        print(f"    {unique_pin_count} users have unique PINs")
        if user_count - unique_password_count > 0:
            print(f"  {user_count - unique_password_count} users have default password 'demo123'")
        
        # 2. INSERT ACCOUNTS
        account_count = len(data['accounts'])
        print(f" Inserting {account_count} accounts...")
        
        for user_id, account_data in data['accounts'].items():
            has_loan = account_data.get('has_loan', False)
            
            cursor.execute("""
                INSERT INTO accounts (
                    user_id, account_number, account_type, balance, 
                    currency, is_primary, has_loan
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (account_number) DO UPDATE SET
                    balance = EXCLUDED.balance,
                    has_loan = EXCLUDED.has_loan
            """, (user_id, account_data['account_number'], account_data['account_type'],
                  account_data['balance'], account_data['currency'], True, has_loan))
        
        conn.commit()
        print(f"  {account_count} accounts inserted")
        
        # 3. INSERT BENEFICIARIES
        total_beneficiaries = sum(len(b) for b in data['beneficiaries'].values())
        print(f" Inserting {total_beneficiaries} beneficiaries...")
        
        for user_id, beneficiaries in data['beneficiaries'].items():
            for ben in beneficiaries:
                cursor.execute("""
                    INSERT INTO beneficiaries (
                        user_id, nickname, full_name, account_number, 
                        bank_name, ifsc_code
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, ben['nickname'], ben['full_name'],
                      ben['account_number'], ben.get('bank', 'SBI'), 
                      ben.get('ifsc', 'SBIN0000000')))
        
        conn.commit()
        print(f"   {total_beneficiaries} beneficiaries inserted")
        
        # 4. INSERT TRANSACTIONS
        total_transactions = sum(len(t) for t in data['transactions'].values())
        print(f" Inserting {total_transactions} transactions...")
        
        for user_id, transactions in data['transactions'].items():
            for txn in transactions:
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, user_id, from_account, to_account,
                        recipient_name, amount, type, status, timestamp
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (transaction_id) DO NOTHING
                """, (txn['transaction_id'], user_id,
                      data['accounts'][user_id]['account_number'],
                      '', txn['to'], txn['amount'], txn['type'],
                      txn['status'], txn['date']))
        
        conn.commit()
        print(f"   {total_transactions} transactions inserted")
        
        # 5. INSERT LOANS
        if 'loans' in data and data['loans']:
            loan_count = len(data['loans'])
            print(f" Inserting {loan_count} loans...")
            
            for user_id, loan in data['loans'].items():
                loan_id = f"LOAN{user_id}"
                
                cursor.execute("""
                    INSERT INTO loans (
                        loan_id, user_id, loan_type, loan_amount,
                        outstanding_balance, interest_rate, monthly_emi,
                        tenure_months, next_due_date, status, disbursed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', %s)
                    ON CONFLICT (loan_id) DO NOTHING
                """, (loan_id, user_id, loan['loan_type'], loan['loan_amount'],
                      loan['outstanding_balance'], loan['interest_rate'],
                      loan['monthly_emi'], loan['tenure_months'],
                      loan['next_due_date'], loan.get('disbursed_at', 'now')))
            
            conn.commit()
            print(f"   {loan_count} loans inserted")
        else:
            print("  No loan data found in JSON")
        
        # 6. INSERT REMINDERS
        if 'reminders' in data and data['reminders']:
            total_reminders = sum(len(r) for r in data['reminders'].values() if r)
            print(f" Inserting {total_reminders} reminders...")
            
            reminder_count = 0
            for user_id, reminders in data['reminders'].items():
                if not reminders:
                    continue
                for reminder in reminders:
                    reminder_id = f"REM{user_id}{reminder_count:04d}"
                    reminder_count += 1
                    
                    cursor.execute("""
                        INSERT INTO payment_reminders (
                            reminder_id, user_id, reminder_type, amount,
                            due_date, description, status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
                    """, (reminder_id, user_id, reminder['reminder_type'],
                          reminder['amount'], reminder['due_date'], reminder['description']))
            
            conn.commit()
            print(f"  {total_reminders} reminders inserted")
        else:
            print("  No reminder data found in JSON")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print(" ALL DATA SEEDED SUCCESSFULLY!")
        print("="*70)
        
        # Get credentials info
        cred_file = get_file_path('user_credentials.txt')
        
        if cred_file:
            print("\n Login Credentials:")
            print(f"  Full list: {cred_file}")
            print("\n  Quick Test Logins:")
            
            # Try to show first 3 users
            try:
                with open(cred_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    user_count = 0
                    current_email = None
                    current_password = None
                    
                    for line in lines:
                        if "Email:" in line and not line.startswith(" "):
                            continue
                        if "  Email:" in line:
                            current_email = line.split(":", 1)[1].strip()
                        elif "  Password:" in line:
                            current_password = line.split(":", 1)[1].strip()
                            if current_email and current_password:
                                print(f"   - Email: {current_email:35s} Password: {current_password}")
                                user_count += 1
                                current_email = None
                                current_password = None
                                if user_count >= 3:
                                    break
            except:
                print("   - Email: rahul.sharma1@demo.com        Password: demo123")
        else:
            print("\n Default Login Credentials:")
            print("   Email: rahul.sharma1@demo.com")
            print("   Password: demo123")
            print("   PIN: 1234")
        
        print("\n💡 Security Features:")
        print("  Each user has UNIQUE password")
        print("  Each user has UNIQUE PIN")
        print("  All passwords are bcrypt hashed")
        print("  First 3 users use 'demo123' for easy testing")
        
    except Exception as e:
        print(f" Error seeding data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n  FINVOICE DATABASE SETUP - COMPLETE VERSION")
    print("="*70)
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
    
    reset = '--reset' in sys.argv or '-r' in sys.argv
    
    if reset:
        print("  RESET MODE: Dropping all existing tables")
    
    create_database()
    create_tables(drop_existing=reset)
    seed_complete_data()
