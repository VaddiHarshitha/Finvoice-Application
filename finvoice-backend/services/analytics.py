import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Any

class AnalyticsService:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_usage_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get usage metrics for last N days"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT COUNT(*) FROM voice_sessions
                WHERE timestamp >= %s
            """, (cutoff_date,))
            total_conversations = cursor.fetchone()[0] or 0
            
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) FROM voice_sessions
                WHERE timestamp >= %s
            """, (cutoff_date,))
            active_users = cursor.fetchone()[0] or 0
            
            cursor.close()
            conn.close()
            
            return {
                "period_days": days,
                "total_conversations": total_conversations,
                "active_users": active_users,
                "avg_conversations_per_user": round(total_conversations / max(active_users, 1), 2)
            }
        except Exception as e:
            print(f" Analytics error: {e}")
            return {
                "period_days": days,
                "total_conversations": 0,
                "active_users": 0,
                "avg_conversations_per_user": 0
            }
    
    def get_transaction_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get transaction metrics"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_txns,
                    COALESCE(SUM(amount), 0) as total_amount
                FROM transactions
                WHERE timestamp >= %s
            """, (cutoff_date,))
            
            row = cursor.fetchone()
            total_txns = row[0] or 0
            total_amount = float(row[1]) if row[1] else 0
            
            cursor.close()
            conn.close()
            
            return {
                "period_days": days,
                "total_transactions": total_txns,
                "total_amount": round(total_amount, 2)
            }
        except Exception as e:
            print(f" Analytics error: {e}")
            return {
                "period_days": days,
                "total_transactions": 0,
                "total_amount": 0
            }
    
    def calculate_roi(self) -> Dict[str, Any]:
        """Calculate estimated ROI metrics"""
        usage = self.get_usage_metrics(days=30)
        
        monthly_conversations = usage['total_conversations']
        cost_per_call_center = 50
        ai_cost_per_interaction = 2
        
        traditional_cost = monthly_conversations * cost_per_call_center
        ai_cost = monthly_conversations * ai_cost_per_interaction
        monthly_savings = traditional_cost - ai_cost
        
        return {
            "monthly_conversations": monthly_conversations,
            "monthly_savings_inr": monthly_savings,
            "annual_savings_inr": monthly_savings * 12

        }
