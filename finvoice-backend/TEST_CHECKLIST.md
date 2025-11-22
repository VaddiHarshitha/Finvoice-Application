# 🧪 Voice API Testing Checklist

## Progress: 0/16 Completed

**Generated:** 16 test audio files
**Server:** http://localhost:8000/docs
**Endpoint:** POST /api/voice/process

---

## 📋 Test Instructions

1. Start server: `python main.py`
2. Open: http://localhost:8000/docs
3. Find: `POST /api/voice/process`
4. Click: "Try it out"
5. For each test:
   - Upload audio file
   - Set `user_id`: `user001`
   - Set `language` (as shown below)
   - Click "Execute"
   - Verify response
   - Check box when done

---

## Test Cases


### [EN-01] English - Balance Query
- [ ] **File:** `test_audio/01_en_balance.mp3`
- **Language:** `en-IN`
- **Expected Intent:** `CHECK_BALANCE`
- **Test Input:** "What is my account balance?"


### [EN-02] English - Transfer Request
- [ ] **File:** `test_audio/02_en_transfer.mp3`
- **Language:** `en-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "Send five thousand rupees to Mom"


### [EN-03] English - Transaction History
- [ ] **File:** `test_audio/03_en_history.mp3`
- **Language:** `en-IN`
- **Expected Intent:** `TRANSACTION_HISTORY`
- **Test Input:** "Show my last three transactions"


### [EN-04] English - List Beneficiaries
- [ ] **File:** `test_audio/04_en_beneficiaries.mp3`
- **Language:** `en-IN`
- **Expected Intent:** `LIST_BENEFICIARIES`
- **Test Input:** "Who can I send money to?"


### [HI-01] Hindi - Balance Query
- [ ] **File:** `test_audio/05_hi_balance.mp3`
- **Language:** `hi-IN`
- **Expected Intent:** `CHECK_BALANCE`
- **Test Input:** "मेरा बैलेंस क्या है?"


### [HI-02] Hindi - Transfer Request
- [ ] **File:** `test_audio/06_hi_transfer.mp3`
- **Language:** `hi-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "माँ को पांच हजार रुपये भेजें"


### [HI-03] Hindi - Transaction History
- [ ] **File:** `test_audio/07_hi_history.mp3`
- **Language:** `hi-IN`
- **Expected Intent:** `TRANSACTION_HISTORY`
- **Test Input:** "मेरे आखिरी तीन लेनदेन दिखाएं"


### [HI-04] Hindi - List Beneficiaries
- [ ] **File:** `test_audio/08_hi_beneficiaries.mp3`
- **Language:** `hi-IN`
- **Expected Intent:** `LIST_BENEFICIARIES`
- **Test Input:** "मैं किसे पैसे भेज सकता हूं?"


### [TA-01] Tamil - Balance Query
- [ ] **File:** `test_audio/09_ta_balance.mp3`
- **Language:** `ta-IN`
- **Expected Intent:** `CHECK_BALANCE`
- **Test Input:** "என் இருப்பு என்ன?"


### [TA-02] Tamil - Transfer Request
- [ ] **File:** `test_audio/10_ta_transfer.mp3`
- **Language:** `ta-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "அம்மாவுக்கு ஐயாயிரம் ரூபாய் அனுப்பு"


### [BN-01] Bengali - Balance Query
- [ ] **File:** `test_audio/11_bn_balance.mp3`
- **Language:** `bn-IN`
- **Expected Intent:** `CHECK_BALANCE`
- **Test Input:** "আমার ব্যালেন্স কত?"


### [BN-02] Bengali - Transfer Request
- [ ] **File:** `test_audio/12_bn_transfer.mp3`
- **Language:** `bn-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "মা কে পাঁচ হাজার টাকা পাঠান"


### [MR-01] Marathi - Balance Query
- [ ] **File:** `test_audio/13_mr_balance.mp3`
- **Language:** `mr-IN`
- **Expected Intent:** `CHECK_BALANCE`
- **Test Input:** "माझं बॅलन्स किती आहे?"


### [MR-02] Marathi - Transfer Request
- [ ] **File:** `test_audio/14_mr_transfer.mp3`
- **Language:** `mr-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "आईला पाच हजार रुपये पाठवा"


### [EDGE-01] Edge - Different Recipient
- [ ] **File:** `test_audio/15_edge_brother_transfer.mp3`
- **Language:** `en-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "Transfer three thousand to Brother"


### [EDGE-02] Edge - Large Amount
- [ ] **File:** `test_audio/16_edge_large_amount.mp3`
- **Language:** `en-IN`
- **Expected Intent:** `FUND_TRANSFER`
- **Test Input:** "Send ten thousand rupees to Dad"


---

## ✅ Expected Response Format
```json
{
  "success": true,
  "language": "en-IN",
  "transcribed_text": "What is my account balance?",
  "intent": "CHECK_BALANCE",
  "confidence": 0.95,
  "response_text": "Balance: ₹75,230.50 in SAVINGS account",
  "response_audio": "base64_encoded_audio..."
}
```

---

## 📊 Test Results

| Category | Tests | Passed | Failed |
|----------|-------|--------|--------|
| English | 4 | ___ | ___ |
| Hindi | 4 | ___ | ___ |
| Tamil | 2 | ___ | ___ |
| Bengali | 2 | ___ | ___ |
| Marathi | 2 | ___ | ___ |
| Edge Cases | 2 | ___ | ___ |
| **TOTAL** | **16** | **___** | **___** |

---

## 🎯 Success Criteria

- ✅ All tests return `"success": true`
- ✅ Intent matches expected
- ✅ Confidence > 0.85
- ✅ Response in correct language
- ✅ Response time < 5 seconds

---

**Notes:**
(Add any observations or issues here)

