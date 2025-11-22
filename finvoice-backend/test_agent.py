from services.banking_service import BankingService
from services.agentic_nlp import AgenticNLP

# Initialize services
print("Initializing services...")
banking = BankingService()
agent = AgenticNLP(banking_service=banking)

print("\n🧪 TESTING AGENTIC AI")
print("=" * 60)

# Comprehensive test cases
test_queries = [
    # Balance queries
    "What's my balance?",
    "How much money do I have?",
    "Check my account balance",
    
    # Transfer queries
    "Can I transfer 5000 to Mom?",
    "Send 3000 to Brother",
    "I want to send 2000 rupees to Dad",
    "Transfer 1500 to Sister",
    "Pay 4000 to Friend",
    
    # Transaction history
    "Show me my last 3 transactions",
    "Transaction history",
    "Show my last 5 transactions",
    
    # List beneficiaries
    "Who can I send money to?",
    "Show me all beneficiaries",
    "List all people I can transfer money to",
    
    # Edge cases
    "Transfer money to someone",  # No amount/recipient
    "Send 100000 to Mom",  # Insufficient balance
    "Send 5000 to Stranger",  # Unknown beneficiary
    
    # General inquiry
    "Hello",
    "Help me",
]

for query in test_queries:
    print(f"\n👤 User: {query}")
    result = agent.process(query, user_id="user001")
    
    # Print response with proper formatting
    response_lines = result['response'].split('\n')
    for line in response_lines:
        print(f"🤖 {line}")
    
    print(f"📊 Intent: {result['intent']}")
    print(f"✅ Confidence: {int(result['confidence']*100)}%")
    print("-" * 60)

print("\n✅ All tests complete!")