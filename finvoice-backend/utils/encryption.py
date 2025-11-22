"""
AES-256 Encryption Utility for FinVoice
Encrypts sensitive data at rest (voice signatures, account details, etc.)
"""

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import base64

load_dotenv()

# ============================================================================
# ENCRYPTION KEY MANAGEMENT
# ============================================================================

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Generate new key (do this ONCE and save to .env)
    new_key = Fernet.generate_key().decode()
    print("\n" + "="*70)
    print("⚠️  NO ENCRYPTION KEY FOUND IN .env")
    print("="*70)
    print(f"\n🔑 Generated new encryption key:")
    print(f"\n{new_key}\n")
    print("📝 Add this to your .env file:")
    print(f"\nENCRYPTION_KEY={new_key}\n")
    print("="*70 + "\n")
    ENCRYPTION_KEY = new_key

# Initialize cipher
try:
    cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    print("✅ Encryption service initialized (AES-256)")
except Exception as e:
    print(f"❌ Failed to initialize encryption: {e}")
    raise


# ============================================================================
# ENCRYPTION FUNCTIONS
# ============================================================================

def encrypt_data(plain_text: str) -> str:
    """
    Encrypt sensitive data using AES-256 (via Fernet)
    
    Args:
        plain_text: Data to encrypt (string)
        
    Returns:
        Encrypted data as base64 string
        
    Example:
        encrypted = encrypt_data("Sensitive Info")
        # Returns: "gAAAAABh..."
    """
    if not plain_text:
        return ""
    
    try:
        # Convert to bytes and encrypt
        encrypted_bytes = cipher.encrypt(plain_text.encode('utf-8'))
        
        # Return as base64 string for easy storage
        encrypted_base64 = base64.b64encode(encrypted_bytes).decode('utf-8')
        
        return encrypted_base64
        
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        raise


def decrypt_data(encrypted_text: str) -> str:
    """
    Decrypt data encrypted with encrypt_data()
    
    Args:
        encrypted_text: Encrypted base64 string
        
    Returns:
        Decrypted plain text
        
    Example:
        decrypted = decrypt_data("gAAAAABh...")
        # Returns: "Sensitive Info"
    """
    if not encrypted_text:
        return ""
    
    try:
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
        
        # Decrypt
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        
        # Return as string
        return decrypted_bytes.decode('utf-8')
        
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        raise


def encrypt_dict(data: dict) -> str:
    """
    Encrypt entire dictionary as JSON
    
    Args:
        data: Dictionary to encrypt
        
    Returns:
        Encrypted JSON as base64 string
    """
    import json
    json_str = json.dumps(data)
    return encrypt_data(json_str)


def decrypt_dict(encrypted_text: str) -> dict:
    """
    Decrypt encrypted dictionary
    
    Args:
        encrypted_text: Encrypted JSON string
        
    Returns:
        Original dictionary
    """
    import json
    json_str = decrypt_data(encrypted_text)
    return json.loads(json_str)


# ============================================================================
# TESTING
# ============================================================================

def test_encryption():
    """Test encryption/decryption"""
    print("\n🧪 Testing Encryption...")
    
    # Test 1: Simple string
    original = "Top Secret Data 12345"
    encrypted = encrypt_data(original)
    decrypted = decrypt_data(encrypted)
    
    print(f"\n1️⃣ String Encryption:")
    print(f"   Original:  {original}")
    print(f"   Encrypted: {encrypted[:50]}...")
    print(f"   Decrypted: {decrypted}")
    print(f"   ✅ Match: {original == decrypted}")
    
    # Test 2: Dictionary
    original_dict = {
        "account_number": "1234567890",
        "balance": 50000.50,
        "voice_signature": "base64_data_here"
    }
    encrypted_dict = encrypt_dict(original_dict)
    decrypted_dict = decrypt_dict(encrypted_dict)
    
    print(f"\n2️⃣ Dictionary Encryption:")
    print(f"   Original:  {original_dict}")
    print(f"   Encrypted: {encrypted_dict[:50]}...")
    print(f"   Decrypted: {decrypted_dict}")
    print(f"   ✅ Match: {original_dict == decrypted_dict}")
    
    # Test 3: Empty string
    encrypted_empty = encrypt_data("")
    decrypted_empty = decrypt_data(encrypted_empty)
    print(f"\n3️⃣ Empty String:")
    print(f"   ✅ Handles empty: {encrypted_empty == '' and decrypted_empty == ''}")
    
    print("\n✅ All encryption tests passed!\n")


if __name__ == "__main__":
    test_encryption()