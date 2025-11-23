import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class ConversationService:
    def __init__(self):
        """Initialize Conversation Service"""
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "your_password"),
            "database": os.getenv("DB_NAME", "finvoice_db")
        }
        print(" ConversationService initialized")
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def save_voice_session(
        self,
        user_id: str,
        language: str,
        transcribed_text: str,
        intent: str,
        response_text: str,
        confidence: float,
        audio_file_path: Optional[str] = None
    ) -> int:
        """
        Save voice session to database
        
        Args:
            user_id: User identifier
            language: Language code (en, hi, ta, etc.)
            transcribed_text: What user said
            intent: Detected intent (CHECK_BALANCE, FUND_TRANSFER, etc.)
            response_text: AI's response
            confidence: Overall confidence score
            audio_file_path: Optional path to cached audio
            
        Returns:
            session_id: ID of created session
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert voice session
            cursor.execute("""
                INSERT INTO voice_sessions (
                    user_id, language, transcribed_text, intent,
                    response_text, confidence, audio_file_path, timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING session_id
            """, (
                user_id, language, transcribed_text, intent,
                response_text, confidence, audio_file_path, datetime.now()
            ))
            
            session_id = cursor.fetchone()[0]
            conn.commit()
            
            print(f" Saved voice session: {session_id}")
            return session_id
            
        except Exception as e:
            print(f" Error saving voice session: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    def save_conversation_turn(
        self,
        user_id: str,
        session_id: int,
        role: str,  # 'user' or 'assistant'
        message: str,
        language: str
    ) -> bool:
        """
        Save individual conversation turn
        Args:
            user_id: User identifier
            session_id: Voice session ID
            role: 'user' or 'assistant'
            message: Message text
            language: Language code
        Returns:
            bool: Success status
        """
        conn = None
        cursor = None   
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversation_history (
                    user_id, session_id, role, message, language, timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, session_id, role, message, language, datetime.now()))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error saving conversation turn: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent conversations for user
        
        Args:
            user_id: User identifier
            limit: Number of sessions to return
            
        Returns:
            List of conversation sessions
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get recent voice sessions
            cursor.execute("""
                SELECT 
                    session_id, language, transcribed_text,
                    intent, response_text, confidence, timestamp
                FROM voice_sessions
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conversations.append({
                    "session_id": row[0],
                    "language": row[1],
                    "user_message": row[2],
                    "intent": row[3],
                    "assistant_response": row[4],
                    "confidence": float(row[5]),
                    "timestamp": row[6].isoformat()
                })
            
            return conversations
            
        except Exception as e:
            print(f" Error getting conversations: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_conversation_by_session(
        self,
        session_id: int
    ) -> Dict:
        """
        Get full conversation details by session ID
        
        Args:
            session_id: Voice session ID
            
        Returns:
            Complete conversation with all turns
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get session details
            cursor.execute("""
                SELECT 
                    user_id, language, transcribed_text,
                    intent, response_text, confidence, timestamp
                FROM voice_sessions
                WHERE session_id = %s
            """, (session_id,))
            
            session = cursor.fetchone()
            
            if not session:
                return {"error": "Session not found"}
            
            # Get conversation turns
            cursor.execute("""
                SELECT role, message, timestamp
                FROM conversation_history
                WHERE session_id = %s
                ORDER BY timestamp ASC
            """, (session_id,))
            
            turns = []
            for row in cursor.fetchall():
                turns.append({
                    "role": row[0],
                    "message": row[1],
                    "timestamp": row[2].isoformat()
                })
            
            return {
                "session_id": session_id,
                "user_id": session[0],
                "language": session[1],
                "intent": session[3],
                "confidence": float(session[5]),
                "timestamp": session[6].isoformat(),
                "conversation": turns
            }
            
        except Exception as e:
            print(f" Error getting conversation: {e}")
            return {"error": str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
