from services.banking_service import BankingService

# Initialize
bank = BankingService()

# Test 1: Get balance
print("\n💰 Test 1: Get Balance")
result = bank.get_balance("user001")
print(f"Result: {result}")

# Test 2: Transfer money
print("\n💸 Test 2: Transfer Money")
result = bank.transfer_money("user001", "Mom", 5000)
print(f"Result: {result}")

# Test 3: Get transactions
print("\n📜 Test 3: Get Transactions")
result = bank.get_transactions("user001", limit=3)
print(f"Result: {result}")

print("\n✅ All banking tests complete!")