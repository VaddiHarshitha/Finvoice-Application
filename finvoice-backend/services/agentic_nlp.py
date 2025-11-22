"""
Agentic NLP Processor using LangChain + Gemini
WITH ENHANCED MULTILINGUAL SUPPORT AND OTP VERIFICATION
UPDATED: Added Loans, Bill Payments, and Reminders support
"""

import os
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool

# Load environment
load_dotenv()


class AgenticNLP:
    """
    Intelligent AI Agent for Banking WITH MULTILINGUAL SUPPORT & OTP FLOW
    - Understands complex requests in multiple languages
    - Translates to English for processing
    - Translates responses back to user's language
    - PRESERVES OTP patterns during translation
    - Handles OTP verification flow
    - Supports Loans, Bill Payments, and Reminders
    - Reasons about user intent
    - Makes decisions autonomously
    """
    
    def __init__(self, banking_service=None):
        """
        Initialize Agentic AI with Gemini + Translation
        
        Args:
            banking_service: Banking service instance for executing operations
        """
        print("🤖 Initializing Agentic AI...")
        
        # Store banking service reference
        self.banking_service = banking_service
        
        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash-exp",
            temperature=0.0,  # Deterministic for banking
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        # Create agent tools
        self.tools = self._create_tools()
        
        # Conversation history (simple list for now)
        self.conversation_history = []
        
        # Supported languages
        self.supported_languages = {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "mr": "Marathi",
            "gu": "Gujarati",
            "kn": "Kannada",
            "ml": "Malayalam",
            "pa": "Punjabi"
        }
        
        print("✅ Agentic AI initialized with Gemini 2.0 Flash")
        print(f"✅ Available tools: {len(self.tools)}")
        print(f"✅ Supported languages: {len(self.supported_languages)}")
    
    
    # =========================================
    # TRANSLATION METHODS
    # =========================================
    
    def _translate_to_english(self, text: str, source_lang: str = "auto") -> tuple:
        """
        Translate input text to English for processing
        
        Args:
            text: Input text in any language
            source_lang: Source language code (auto for auto-detect)
            
        Returns:
            tuple: (translated_text, detected_language)
        """
        # If already English, return as is
        if source_lang in ["en", "en-IN", "en-US"]:
            return text, "en"
        
        try:
            from deep_translator import GoogleTranslator
            
            # Create translator
            if source_lang == "auto":
                translator = GoogleTranslator(source='auto', target='en')
                detected = "hi"  # Default assumption
            else:
                translator = GoogleTranslator(source=source_lang, target='en')
                detected = source_lang
            
            # Translate
            translated = translator.translate(text)
            
            print(f"🌍 Translation: '{text}' ({detected}) → '{translated}' (en)")
            return translated, detected
            
        except Exception as e:
            print(f"⚠️ Translation failed: {e}. Using original text.")
            return text, "en"
    
    
    def _translate_response(self, text: str, target_lang: str = "en") -> str:
        """
        Translate response back to target language, PRESERVING OTP pattern
        
        Args:
            text: Response text in English
            target_lang: Target language code
            
        Returns:
            str: Translated response with OTP preserved in English
        """
        # If target is English, return as is
        if target_lang in ["en", "en-IN", "en-US"]:
            return text
        
        try:
            from deep_translator import GoogleTranslator
            
            # STEP 1: Extract OTP pattern BEFORE translation
            otp_match = re.search(r'(OTP:\s*\d{6})', text)
            otp_text = ""
            text_without_otp = text
            
            if otp_match:
                otp_text = " " + otp_match.group(1)  # Keep with space
                text_without_otp = text.replace(otp_match.group(1), "").strip()
                print(f"🔐 Extracted OTP pattern: {otp_match.group(1)}")
            
            # STEP 2: Translate the text WITHOUT OTP
            translator = GoogleTranslator(source='en', target=target_lang)
            translated = translator.translate(text_without_otp)
            
            # STEP 3: Re-add OTP in ENGLISH at the end
            final_response = translated + otp_text
            
            print(f"🌍 Response translation: (en) → ({target_lang})")
            print(f"✅ Final response: {final_response[:100]}...")
            
            return final_response
            
        except Exception as e:
            print(f"⚠️ Response translation failed: {e}. Using English.")
            return text
    
    
    # =========================================
    # TOOLS DEFINITION (UPDATED)
    # =========================================
    
    def _create_tools(self) -> List[Tool]:
        """
        Create tools that the AI agent can use
        These are the "skills" of your AI
        """
        
        tools = [
            Tool(
                name="check_balance",
                func=self._tool_check_balance,
                description="Check user account balance. Input: user_id"
            ),
            
            Tool(
                name="find_beneficiary",
                func=self._tool_find_beneficiary,
                description="Find beneficiary by nickname. Input: user_id|nickname"
            ),
            
            Tool(
                name="transfer_money",
                func=self._tool_transfer_money,
                description="Transfer money to beneficiary. Input: user_id|nickname|amount"
            ),
            
            Tool(
                name="get_transaction_history",
                func=self._tool_get_transactions,
                description="Get transaction history. Input: user_id|count"
            ),
            
            Tool(
                name="list_beneficiaries",
                func=self._tool_list_beneficiaries,
                description="List all beneficiaries. Input: user_id"
            ),
            
            # NEW TOOLS 👇
            Tool(
                name="check_loans",
                func=self._tool_check_loans,
                description="Check user's active loans. Input: user_id"
            ),
            
            Tool(
                name="check_loan_eligibility",
                func=self._tool_check_loan_eligibility,
                description="Check loan eligibility. Input: user_id|amount"
            ),
            
            Tool(
                name="pay_bill",
                func=self._tool_pay_bill,
                description="Pay utility bill. Input: user_id|bill_type|biller_name|amount"
            ),
            
            Tool(
                name="get_upcoming_payments",
                func=self._tool_get_upcoming_payments,
                description="Get upcoming payment reminders. Input: user_id|days"
            ),
        ]
        
        return tools
    
    
    # =========================================
    # EXISTING TOOL IMPLEMENTATIONS
    # =========================================
    
    def _tool_check_balance(self, user_id: str) -> str:
        """Tool: Check account balance"""
        if not self.banking_service:
            return "Banking service not available"
        
        result = self.banking_service.get_balance(user_id)
        
        if result['success']:
            return f"Balance: ₹{result['balance']:,.2f} in {result['account_type']} account"
        else:
            return f"Error: {result.get('error', 'Unknown error')}"
    
    
    def _tool_find_beneficiary(self, input_str: str) -> str:
        """Tool: Find beneficiary details"""
        try:
            user_id, nickname = input_str.split('|')
            
            if not self.banking_service:
                return "Banking service not available"
            
            beneficiary = self.banking_service.find_beneficiary(user_id, nickname)
            
            if beneficiary:
                return f"Found: {beneficiary['full_name']} (Account: {beneficiary['account_number']}, Bank: {beneficiary['bank']})"
            else:
                available = self.banking_service.get_beneficiaries(user_id)
                names = [b['nickname'] for b in available]
                return f"Beneficiary '{nickname}' not found. Available: {', '.join(names)}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    def _tool_transfer_money(self, input_str: str) -> str:
        """Tool: Transfer money with OTP"""
        try:
            user_id, recipient, amount_str = input_str.split('|')
            amount = float(amount_str)
            
            if not self.banking_service:
                return "Banking service not available"
            
            result = self.banking_service.transfer_money(user_id, recipient, amount)
            
            if result['success']:
                return (
                    f"Transfer initiated: ₹{amount:,.0f} to {result['recipient']}. "
                    f"Please verify with OTP. OTP: {result['otp']}"
                )
            else:
                return f"Transfer failed: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    def _tool_get_transactions(self, input_str: str) -> str:
        """Tool: Get transaction history"""
        try:
            user_id, limit_str = input_str.split('|')
            limit = int(limit_str)
            
            if not self.banking_service:
                return "Banking service not available"
            
            result = self.banking_service.get_transactions(user_id, limit)
            
            if result['success'] and result['count'] > 0:
                transactions = result['transactions']
                summary = f"Found {result['count']} transaction(s):\n"
                for txn in transactions[:limit]:
                    summary += f"- {txn['date']}: ₹{txn['amount']:,.0f} to {txn['to']} ({txn['status']})\n"
                return summary
            else:
                return "No transactions found"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    def _tool_list_beneficiaries(self, user_id: str) -> str:
        """Tool: List all beneficiaries"""
        if not self.banking_service:
            return "Banking service not available"
        
        beneficiaries = self.banking_service.get_beneficiaries(user_id)
        
        if beneficiaries:
            names = [f"{b['nickname']} ({b['full_name']})" for b in beneficiaries]
            return f"You can send money to: {', '.join(names)}"
        else:
            return "No beneficiaries found. Please add beneficiaries first."
    
    
    # =========================================
    # NEW TOOL IMPLEMENTATIONS 👇
    # =========================================
    
    def _tool_check_loans(self, user_id: str) -> str:
        """Tool: Check user's loans"""
        if not self.banking_service:
            return "Banking service not available"
        
        result = self.banking_service.get_loan_info(user_id)
        
        if result['success'] and result['loans']:
            summary = f"You have {len(result['loans'])} active loan(s):\n"
            for loan in result['loans']:
                summary += (
                    f"- {loan['loan_type']}: ₹{loan['outstanding']:,.0f} outstanding "
                    f"(EMI: ₹{loan['monthly_emi']:,.0f}/month, "
                    f"Interest: {loan['interest_rate']}%)\n"
                )
            summary += f"\nTotal Outstanding: ₹{result['total_outstanding']:,.0f}"
            return summary
        else:
            return "You have no active loans."
    
    
    def _tool_check_loan_eligibility(self, input_str: str) -> str:
        """Tool: Check loan eligibility"""
        try:
            user_id, amount_str = input_str.split('|')
            amount = float(amount_str)
            
            if not self.banking_service:
                return "Banking service not available"
            
            result = self.banking_service.get_loan_eligibility(user_id, amount)
            
            if result['success']:
                if result['eligible']:
                    return (
                        f"Good news! You are eligible for a loan of ₹{amount:,.0f}.\n"
                        f"Interest Rate: {result['interest_rate']}% per annum\n"
                        f"Tenure: {result['tenure_months']} months\n"
                        f"Monthly EMI: ₹{result['monthly_emi']:,.0f}\n"
                        f"Would you like to apply?"
                    )
                else:
                    return (
                        f"You are not eligible for ₹{amount:,.0f}.\n"
                        f"Maximum eligible amount: ₹{result['max_eligible']:,.0f}\n"
                        f"Based on your current balance of ₹{result['current_balance']:,.0f}"
                    )
            else:
                return f"Error checking eligibility: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    def _tool_pay_bill(self, input_str: str) -> str:
        """Tool: Pay utility bill"""
        try:
            parts = input_str.split('|')
            user_id = parts[0]
            bill_type = parts[1]
            biller_name = parts[2]
            amount = float(parts[3])
            
            if not self.banking_service:
                return "Banking service not available"
            
            result = self.banking_service.pay_bill(
                user_id=user_id,
                bill_type=bill_type,
                biller_name=biller_name,
                amount=amount
            )
            
            if result['success']:
                return (
                    f"Bill payment successful!\n"
                    f"Paid ₹{amount:,.0f} to {biller_name} for {bill_type}\n"
                    f"Reference: {result['bill_reference']}"
                )
            else:
                return f"Bill payment failed: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    def _tool_get_upcoming_payments(self, input_str: str) -> str:
        """Tool: Get upcoming payment reminders"""
        try:
            user_id, days_str = input_str.split('|')
            days = int(days_str)
            
            if not self.banking_service:
                return "Banking service not available"
            
            result = self.banking_service.get_upcoming_payments(user_id, days)
            
            if result['success'] and result['upcoming_payments']:
                summary = f"You have {result['count']} upcoming payment(s) in next {days} days:\n"
                for payment in result['upcoming_payments']:
                    summary += (
                        f"- {payment['type']}: ₹{payment['amount']:,.0f} "
                        f"due on {payment['due_date']} ({payment['description']})\n"
                    )
                summary += f"\nTotal: ₹{result['total_amount']:,.0f}"
                return summary
            else:
                return f"No upcoming payments in next {days} days."
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    
    # =========================================
    # OTP VERIFICATION METHODS
    # =========================================
    
    def _is_otp_verification(self, text_english: str, text_original: str) -> bool:
        """Check if user is providing OTP"""
        otp_keywords_english = [
            'otp is', 'my otp', 'the otp', 'otp:', 'otp code',
            'code is', 'verification code', 'verification is',
            'pin is', 'password is'
        ]
        
        otp_keywords_multilang = [
            'otp hai', 'mera otp', 'code hai', 'otp ka code',
            'otp', 'code'
        ]
        
        has_otp_keyword_english = any(keyword in text_english.lower() for keyword in otp_keywords_english)
        has_otp_keyword_original = any(keyword in text_original.lower() for keyword in otp_keywords_multilang)
        
        digits = re.findall(r'\d', text_english)
        has_six_digits = len(digits) == 6
        
        return has_otp_keyword_english or has_otp_keyword_original or has_six_digits
    
    
    def _extract_otp(self, text: str) -> str:
        """Extract 6-digit OTP from text"""
        digits = ''.join(re.findall(r'\d', text))
        
        if len(digits) >= 6:
            return digits[:6]
        
        return None
    
    
    # =========================================
    # MAIN PROCESSING METHOD (UPDATED)
    # =========================================
    
    def process(self, text: str, user_id: str = "user001", language: str = "auto") -> Dict[str, Any]:
        """
        Process user input with multilingual support and ALL features
        """
        
        try:
            print(f"\n🤖 Agent processing: '{text}'")
            print(f"👤 User ID: {user_id}")
            print(f"🌍 Input Language: {language}")
            
            # STEP 1: Translate to English
            text_english, detected_lang = self._translate_to_english(text, language)
            text_lower = text_english.lower()
            text_original_lower = text.lower()
            
            tool_result = ""
            intent = "UNKNOWN"
            otp_extracted = None
            
            # =========================================
            # 1. OTP VERIFICATION (HIGHEST PRIORITY)
            # =========================================
            if self._is_otp_verification(text_lower, text_original_lower):
                otp_extracted = self._extract_otp(text_english)
                
                if otp_extracted:
                    tool_result = f"OTP_PROVIDED:{otp_extracted}"
                    intent = "OTP_VERIFICATION"
                    print(f"✅ OTP detected: {otp_extracted}")
                else:
                    tool_result = "Could not extract OTP. Please say your 6-digit OTP clearly."
                    intent = "OTP_VERIFICATION_FAILED"
            
            # =========================================
            # 2. LOAN QUERIES 🏦
            # =========================================
            elif self._is_loan_query(text_lower, text_original_lower):
                # Check if asking for eligibility
                if self._is_loan_eligibility_query(text_lower):
                    amount = self._extract_number(text_english)
                    if amount:
                        tool_result = self._tool_check_loan_eligibility(f"{user_id}|{amount}")
                        intent = "LOAN_ELIGIBILITY"
                    else:
                        tool_result = "Please specify the loan amount. For example: 'Am I eligible for a loan of 500000?'"
                        intent = "LOAN_ELIGIBILITY"
                else:
                    # Just checking existing loans
                    tool_result = self._tool_check_loans(user_id)
                    intent = "CHECK_LOANS"
            
            # =========================================
            # 3. BILL PAYMENT 💡
            # =========================================
            elif self._is_bill_payment_query(text_lower, text_original_lower):
                bill_info = self._extract_bill_info(text_english)
                
                if bill_info['amount'] and bill_info['bill_type']:
                    biller_name = bill_info.get('biller_name', f"{bill_info['bill_type']} Provider")
                    tool_result = self._tool_pay_bill(
                        f"{user_id}|{bill_info['bill_type']}|{biller_name}|{bill_info['amount']}"
                    )
                    intent = "BILL_PAYMENT"
                else:
                    tool_result = "Please specify the bill type and amount. For example: 'Pay my electricity bill of 2500'"
                    intent = "BILL_PAYMENT"
            
            # =========================================
            # 4. PAYMENT REMINDERS ⏰
            # =========================================
            elif self._is_reminder_query(text_lower, text_original_lower):
                days = self._extract_number(text_english, default="7")
                tool_result = self._tool_get_upcoming_payments(f"{user_id}|{days}")
                intent = "UPCOMING_PAYMENTS"
            
            # =========================================
            # 5. CHECK BALANCE
            # =========================================
            elif self._is_balance_query(text_lower, text_original_lower):
                tool_result = self._tool_check_balance(user_id)
                intent = "CHECK_BALANCE"
            
            # =========================================
            # 6. LIST BENEFICIARIES
            # =========================================
            elif self._is_list_beneficiaries_query(text_lower, text_original_lower):
                tool_result = self._tool_list_beneficiaries(user_id)
                intent = "LIST_BENEFICIARIES"
            
            # =========================================
            # 7. TRANSACTION HISTORY
            # =========================================
            elif self._is_transaction_query(text_lower, text_original_lower):
                count = self._extract_number(text_english, default="5")
                tool_result = self._tool_get_transactions(f"{user_id}|{count}")
                intent = "TRANSACTION_HISTORY"
            
            # =========================================
            # 8. TRANSFER MONEY
            # =========================================
            elif self._is_transfer_query(text_lower, text_original_lower):
                amount = self._extract_number(text_english)
                recipient = self._extract_recipient(text_lower, user_id)
                
                if not amount:
                    tool_result = "Please specify the amount you want to transfer. For example: 'Send 5000 to Mom'"
                    intent = "FUND_TRANSFER"
                elif not recipient:
                    available_ben = self._tool_list_beneficiaries(user_id)
                    tool_result = f"Please specify the recipient. {available_ben}"
                    intent = "FUND_TRANSFER"
                else:
                    tool_result = self._execute_transfer(user_id, recipient, amount)
                    intent = "FUND_TRANSFER"
            
            # =========================================
            # 9. GENERAL INQUIRY
            # =========================================
            else:
                tool_result = self._get_help_message()
                intent = "GENERAL_INQUIRY"
            
            # STEP 2: Translate response
            if intent == "OTP_VERIFICATION":
                response_translated = tool_result
            else:
                response_translated = self._translate_response(tool_result, detected_lang)
            
            # Store in history
            self.conversation_history.append({
                "user": text,
                "response": response_translated,
                "intent": intent,
                "language": detected_lang
            })
            
            print(f"✅ Agent response: '{response_translated[:100]}...'")
            
            result = {
                "success": True,
                "intent": intent,
                "response": response_translated,
                "confidence": 0.95,
                "original_text": text,
                "translated_text": text_english if detected_lang != "en" else None,
                "detected_language": detected_lang
            }
            
            if otp_extracted:
                result["otp_extracted"] = otp_extracted
            
            return result
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            error_msg = "I apologize, but I encountered an error processing your request. Please try again."
            
            try:
                if language not in ["en", "auto"]:
                    error_msg = self._translate_response(error_msg, language)
            except:
                pass
            
            return {
                "success": False,
                "intent": "ERROR",
                "response": error_msg,
                "error": str(e),
                "confidence": 0.0
            }
    
    
    # =========================================
    # NEW INTENT DETECTION METHODS 👇
    # =========================================
    
    def _is_loan_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is about loans"""
        loan_keywords = [
            'loan', 'emi', 'interest rate', 'borrow', 'credit',
            'home loan', 'car loan', 'personal loan', 'education loan',
            'loan eligibility', 'eligible for loan', 'apply for loan'
        ]
        
        multilang_loan = [
            'karza', 'loan', 'byaj', 'suddi', 'vaddi', 'kadan',
            'udhaar', 'qarz', 'rin', 'karz'
        ]
        
        return any(kw in text_english for kw in loan_keywords) or \
               any(kw in text_original for kw in multilang_loan)
    
    
    def _is_loan_eligibility_query(self, text: str) -> bool:
        """Check if specifically asking for loan eligibility"""
        eligibility_keywords = [
            'eligible', 'eligibility', 'can i get', 'qualify',
            'am i eligible', 'do i qualify', 'can i apply'
        ]
        return any(kw in text for kw in eligibility_keywords)
    
    
    def _is_bill_payment_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is about bill payment"""
        bill_keywords = [
            'pay bill', 'bill payment', 'electricity bill', 'water bill',
            'phone bill', 'internet bill', 'mobile bill', 'utility bill',
            'pay my bill', 'pay the bill'
        ]
        
        multilang_bill = [
            'bill', 'bijli', 'pani', 'phone', 'internet',
            'bill bharana', 'bill pay', 'bill payment'
        ]
        
        return any(kw in text_english for kw in bill_keywords) or \
               any(kw in text_original for kw in multilang_bill)
    
    
    def _is_reminder_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is about payment reminders"""
        reminder_keywords = [
            'upcoming payment', 'pending payment', 'due payment',
            'what is due', 'payment due', 'reminder', 'upcoming bill'
        ]
        
        multilang_reminder = [
            'aane wala payment', 'pending payment', 'reminder',
            'yaad dilana', 'due'
        ]
        
        return any(kw in text_english for kw in reminder_keywords) or \
               any(kw in text_original for kw in multilang_reminder)
    
    
    def _extract_bill_info(self, text: str) -> Dict[str, Any]:
        """Extract bill type and amount from text"""
        bill_types = {
            'electricity': 'ELECTRICITY',
            'electric': 'ELECTRICITY',
            'bijli': 'ELECTRICITY',
            'water': 'WATER',
            'pani': 'WATER',
            'phone': 'PHONE',
            'mobile': 'PHONE',
            'internet': 'INTERNET',
            'wifi': 'INTERNET',
            'gas': 'GAS'
        }
        
        # Find bill type
        bill_type = None
        for key, value in bill_types.items():
            if key in text.lower():
                bill_type = value
                break
        
        # Extract amount
        amount = self._extract_number(text)
        
        return {
            'bill_type': bill_type,
            'amount': amount,
            'biller_name': None
        }
    
    
    # =========================================
    # EXISTING INTENT DETECTION METHODS
    # =========================================
    
    def _is_balance_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is about balance"""
        balance_keywords = ['balance', 'how much money', 'account', 'funds', 'available']
        multilang_balance = [
            'balance', 'balans', 'kitna paisa', 'kitne paise', 'kitna rupya', 
            'account', 'khata', 'khaate', 'neruppu', 'kaasu', 'rupa', 'kadan',
            'bakee', 'dabbu', 'taka', 'hisab', 'hishab', 'baki', 'shillak', 
            'khate', 'rupaye', 'balan', 'balanse'
        ]
        transfer_keywords = ['transfer', 'send', 'pay', 'give', 'bhej', 'anuppu', 'pathav']
        
        has_balance_english = any(keyword in text_english for keyword in balance_keywords)
        has_balance_original = any(keyword in text_original for keyword in multilang_balance)
        has_transfer = any(keyword in text_english for keyword in transfer_keywords)
        
        return (has_balance_english or has_balance_original) and not has_transfer
    
    
    def _is_list_beneficiaries_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is asking for list of beneficiaries"""
        list_phrases = [
            'who can i send', 'who can i transfer', 'list beneficiary', 'list beneficiaries',
            'show beneficiary', 'show beneficiaries', 'show me all beneficiary',
            'show me all beneficiaries', 'show all beneficiary', 'show all beneficiaries',
            'available beneficiary', 'available beneficiaries', 'who can i pay',
            'whom can i send', 'whom can i transfer', 'hu can i', 'hu can i send',
            'kise bhej', 'kisko bhej', 'kaun kaun', 'suchi', 'list',
            'kisi', 'kisi ko', 'kisi paise bhej', 'kisi ko paise',
            'yaar yaar', 'anuppu mudiyum', 'evari ki', 'kake pathabo', 'kona kona'
        ]
        
        has_who = any(word in text_english for word in ['who', 'whom', 'hu'])
        has_who_multilang = any(word in text_original for word in ['kisi', 'kisko', 'kise'])
        has_send = any(word in text_english for word in ['send', 'transfer'])
        has_send_multilang = any(word in text_original for word in ['bhej', 'bheje'])
        has_list_pattern = (has_who or has_who_multilang) and (has_send or has_send_multilang)
        
        return any(phrase in text_english for phrase in list_phrases) or \
               any(phrase in text_original for phrase in ['kise', 'kisko', 'kaun', 'kisi']) or \
               has_list_pattern
    
    
    def _is_transaction_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is about transaction history"""
        transaction_keywords = [
            'transaction', 'history', 'statement', 'past payment', 'previous transfer',
            'last', 'recent', 'previous', 'past'
        ]
        multilang_transaction = [
            'lenden', 'lene dene', 'lekha', 'aakhri', 'pichle', 'purane',
            'teen', 'paanch', 'das', 'varalaru', 'munpadi', 'kadasi', 'muru', 'aindu',
            'charitra', 'kramam', 'chivari', 'mundati', 'itihas', 'shesh', 'agamir',
            'vyavahar', 'mage', 'pichla'
        ]
        
        has_last = any(word in text_english for word in ['last', 'recent', 'previous'])
        has_last_multilang = any(word in text_original for word in ['aakhri', 'kadasi', 'chivari', 'shesh', 'mage'])
        has_number = bool(re.search(r'\d+', text_english))
        
        has_transaction_english = any(keyword in text_english for keyword in transaction_keywords)
        has_transaction_multilang = any(keyword in text_original for keyword in multilang_transaction)
        
        return has_transaction_english or has_transaction_multilang or \
               ((has_last or has_last_multilang) and has_number)
    
    
    def _is_transfer_query(self, text_english: str, text_original: str) -> bool:
        """Check if query is about transferring money"""
        transfer_keywords = [
            'transfer', 'send', 'pay', 'give', 'can i transfer', 'can i send'
        ]
        multilang_transfer = [
            'bhej', 'bheje', 'bhejo', 'bhejdo', 'transfer', 'paisa', 'rupay', 'rupya',
            'dedo', 'de do', 'den', 'dena', 'anuppu', 'anuppunga', 'kodunga', 'kodu',
            'rubai', 'ruba', 'ammavukku', 'amma', 'pampu', 'pampandi', 'ivvu', 'ivvandi',
            'rupayalu', 'dabbu', 'pathao', 'pathaan', 'pathate', 'taka', 'poisha',
            'pathabo', 'den', 'pathav', 'pathva', 'pathwa', 'pathavun', 'rupaye',
            'de', 'dya', 'moklo', 'apo', 'rupiya'
        ]
        
        has_amount = bool(re.search(r'\d{3,}', text_english))
        has_recipient = any(name in text_english for name in ['mom', 'dad', 'brother', 'sister', 'mother', 'father']) or \
                       any(name in text_original for name in ['man', 'ko', 'amma', 'ammavukku', 'appa', 'anna'])
        
        has_transfer_english = any(keyword in text_english for keyword in transfer_keywords)
        has_transfer_multilang = any(keyword in text_original for keyword in multilang_transfer)
        
        return has_transfer_english or has_transfer_multilang or (has_amount and has_recipient)
    
    
    def _extract_number(self, text: str, default: str = None) -> str:
        """Extract number from text"""
        numbers = re.findall(r'\d+', text)
        if numbers:
            return str(max(int(n) for n in numbers))
        return default
    
    
    def _extract_recipient(self, text: str, user_id: str) -> str:
        """Extract recipient from text"""
        recipient_keywords = [
            'mom', 'mother', 'dad', 'father', 'brother', 'sister', 
            'friend', 'wife', 'husband', 'son', 'daughter'
        ]
        
        multilang_recipients = {
            'man': 'Mom', 'maa': 'Mom', 'mata': 'Mom', 'amma': 'Mom', 'ammavukku': 'Mom',
            'bap': 'Dad', 'pita': 'Dad', 'appa': 'Dad', 'father': 'Dad',
            'bhai': 'Brother', 'anna': 'Brother', 'dada': 'Brother',
            'behen': 'Sister', 'bahin': 'Sister', 'akka': 'Sister',
            'dost': 'Friend', 'mitra': 'Friend', 'nanban': 'Friend'
        }
        
        for keyword in recipient_keywords:
            if keyword in text:
                return keyword.capitalize()
        
        for key, value in multilang_recipients.items():
            if key in text:
                return value
        
        if self.banking_service:
            beneficiaries = self.banking_service.get_beneficiaries(user_id)
            for ben in beneficiaries:
                if ben['nickname'].lower() in text:
                    return ben['nickname']
        
        return None
    
    
    def _execute_transfer(self, user_id: str, recipient: str, amount: str) -> str:
        """Execute multi-step transfer process"""
        try:
            amount_float = float(amount)
            
            ben_result = self._tool_find_beneficiary(f"{user_id}|{recipient}")
            
            if "Found:" not in ben_result:
                return ben_result
            
            bal_result = self._tool_check_balance(user_id)
            
            balance_match = re.search(r'₹([\d,]+\.\d+)', bal_result)
            if balance_match:
                balance = float(balance_match.group(1).replace(',', ''))
                
                if balance < amount_float:
                    return f"Insufficient balance. You have ₹{balance:,.2f} but need ₹{amount_float:,.2f}"
            
            transfer_result = self._tool_transfer_money(f"{user_id}|{recipient}|{amount}")
            
            return transfer_result
        
        except Exception as e:
            return f"Transfer failed: {str(e)}"
    
    
    def _get_help_message(self) -> str:
        """Get help message for user"""
        return """I can help you with:

💰 Check Balance: "What's my balance?"

💸 Transfer Money: "Send 5000 to Mom"

📜 Transaction History: "Show my last 5 transactions"

👥 List Beneficiaries: "Who can I send money to?"

🏦 Loans: "What are my loans?" or "Am I eligible for a loan of 500000?"

💡 Bill Payments: "Pay my electricity bill of 2500"

⏰ Upcoming Payments: "What payments are due?"

How can I help you today?"""
    
    
    # =========================================
    # CONVERSATION MANAGEMENT
    # =========================================
    
    def reset_memory(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🔄 Conversation memory cleared")
    
    
    def get_memory(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history