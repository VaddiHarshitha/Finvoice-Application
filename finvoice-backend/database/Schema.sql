-- 1. USERS TABLE
CREATE TABLE users (
user_id VARCHAR(50) PRIMARY KEY,
name VARCHAR(100) NOT NULL,
email VARCHAR(100) UNIQUE NOT NULL,
phone VARCHAR(20) UNIQUE NOT NULL,
password_hash VARCHAR(255) NOT NULL,  -- Bcrypt hashed
pin_hash VARCHAR(255),                -- Encrypted PIN
voice_signature BYTEA,                -- Voice biometric data
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
is_active BOOLEAN DEFAULT TRUE
);
-- 2. ACCOUNTS TABLE
CREATE TABLE accounts (
account_id SERIAL PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
account_number VARCHAR(20) UNIQUE NOT NULL,
account_type VARCHAR(20) DEFAULT 'SAVINGS',
balance DECIMAL(15, 2) DEFAULT 0.00,
currency VARCHAR(3) DEFAULT 'INR',
is_primary BOOLEAN DEFAULT TRUE,
has_loan BOOLEAN DEFAULT FALSE, 
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 3. BENEFICIARIES TABLE
CREATE TABLE beneficiaries (
beneficiary_id SERIAL PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
nickname VARCHAR(50) NOT NULL,
full_name VARCHAR(100) NOT NULL,
account_number VARCHAR(20) NOT NULL,
bank_name VARCHAR(100),
ifsc_code VARCHAR(11),
added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
is_active BOOLEAN DEFAULT TRUE
);
-- 4. TRANSACTIONS TABLE
CREATE TABLE transactions (
transaction_id VARCHAR(50) PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
from_account VARCHAR(20),
to_account VARCHAR(20),
recipient_name VARCHAR(100),
amount DECIMAL(15, 2) NOT NULL,
type VARCHAR(20) NOT NULL,  -- DEBIT, CREDIT
status VARCHAR(20) DEFAULT 'SUCCESS',  -- SUCCESS, FAILED, PENDING
reference_number VARCHAR(50),
description TEXT,
initiated_via VARCHAR(20) DEFAULT 'VOICE',  -- VOICE, APP, WEB
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 5. PENDING_TRANSACTIONS TABLE (for OTP verification)
CREATE TABLE pending_transactions (
pending_id SERIAL PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
from_account VARCHAR(20),
to_account VARCHAR(20),
recipient_name VARCHAR(100),
amount DECIMAL(15, 2) NOT NULL,
otp_hash VARCHAR(255),  -- Hashed OTP
otp_expiry TIMESTAMP,
status VARCHAR(20) DEFAULT 'PENDING_OTP',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 6. SESSIONS TABLE (active logins)
CREATE TABLE sessions (
session_id VARCHAR(100) PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
token TEXT NOT NULL,
device_info JSONB,
ip_address VARCHAR(50),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
expires_at TIMESTAMP NOT NULL,
is_active BOOLEAN DEFAULT TRUE
);
-- 7. VOICE_SESSIONS TABLE (conversation logs)
CREATE TABLE voice_sessions (
session_id SERIAL PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
language VARCHAR(10),
transcribed_text TEXT,
intent VARCHAR(50),
response_text TEXT,
confidence DECIMAL(5, 2),
audio_file_path VARCHAR(255),
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 8. CONVERSATION_HISTORY TABLE
CREATE TABLE conversation_history (
conversation_id SERIAL PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
session_id INT REFERENCES voice_sessions(session_id) ON DELETE CASCADE,
role VARCHAR(20),  -- 'user' or 'assistant'
message TEXT NOT NULL,
language VARCHAR(10),
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 9. SECURITY_EVENTS TABLE
CREATE TABLE security_events (
event_id SERIAL PRIMARY KEY,
user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
event_type VARCHAR(50),  -- LOGIN_SUCCESS, LOGIN_FAILED, OTP_FAILED
ip_address VARCHAR(50),
device_info JSONB,
details TEXT,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- LOANS TABLE
CREATE TABLE loans (
    loan_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    loan_type VARCHAR(50) NOT NULL,  -- HOME, CAR, PERSONAL
    loan_amount DECIMAL(15, 2) NOT NULL,
    outstanding_balance DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    monthly_emi DECIMAL(10, 2) NOT NULL,
    tenure_months INT NOT NULL,
    next_due_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    disbursed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PAYMENT REMINDERS TABLE
CREATE TABLE payment_reminders (
    reminder_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,  -- BILL, EMI, TRANSFER
    amount DECIMAL(15, 2) NOT NULL,
    due_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_accounts_has_loan ON accounts(has_loan);

CREATE INDEX idx_reminders_user ON payment_reminders(user_id);
CREATE INDEX idx_reminders_due_date ON payment_reminders(due_date);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status); 
CREATE INDEX idx_loans_user ON loans(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_accounts_user ON accounts(user_id);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_voice_sessions_user ON voice_sessions(user_id);

CREATE INDEX idx_conversation_history_user ON conversation_history(user_id);
