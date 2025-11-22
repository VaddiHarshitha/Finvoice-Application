"""
Performance Monitoring Service
Tracks API performance, identifies bottlenecks, and provides insights
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics
import json

class PerformanceMonitor:
    """
    Advanced performance monitoring with insights
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.request_times = defaultdict(list)
        self.endpoint_calls = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.status_codes = defaultdict(lambda: defaultdict(int))
        self.hourly_stats = defaultdict(lambda: {"requests": 0, "avg_time": 0})
        
        print("✅ PerformanceMonitor initialized")
    
    def record_request(
        self,
        endpoint: str,
        duration: float,
        status_code: int,
        method: str = "GET"
    ):
        """
        Record a request for monitoring
        
        Args:
            endpoint: API endpoint path
            duration: Request duration in seconds
            status_code: HTTP status code
            method: HTTP method
        """
        # Record timing
        self.request_times[endpoint].append(duration)
        self.endpoint_calls[endpoint] += 1
        
        # Record status code
        self.status_codes[endpoint][status_code] += 1
        
        # Record errors
        if status_code >= 400:
            self.error_counts[endpoint] += 1
        
        # Record hourly stats
        hour = datetime.now().strftime("%Y-%m-%d %H:00")
        self.hourly_stats[hour]["requests"] += 1
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get detailed stats for specific endpoint"""
        times = self.request_times[endpoint]
        
        if not times:
            return {"error": "No data for this endpoint"}
        
        return {
            "endpoint": endpoint,
            "total_calls": self.endpoint_calls[endpoint],
            "avg_time": round(statistics.mean(times), 3),
            "median_time": round(statistics.median(times), 3),
            "min_time": round(min(times), 3),
            "max_time": round(max(times), 3),
            "p95_time": round(statistics.quantiles(times, n=20)[18], 3) if len(times) > 20 else round(max(times), 3),
            "p99_time": round(statistics.quantiles(times, n=100)[98], 3) if len(times) > 100 else round(max(times), 3),
            "total_time": round(sum(times), 2),
            "errors": self.error_counts[endpoint],
            "error_rate": round(self.error_counts[endpoint] / self.endpoint_calls[endpoint] * 100, 2) if self.endpoint_calls[endpoint] > 0 else 0,
            "status_codes": dict(self.status_codes[endpoint])
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all endpoints"""
        all_stats = {}
        
        for endpoint in self.request_times.keys():
            all_stats[endpoint] = self.get_endpoint_stats(endpoint)
        
        # Sort by average time (slowest first)
        sorted_stats = dict(
            sorted(all_stats.items(), key=lambda x: x[1].get('avg_time', 0), reverse=True)
        )
        
        return sorted_stats
    
    def get_slow_endpoints(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get endpoints slower than threshold
        
        Args:
            threshold: Threshold in seconds
            
        Returns:
            List of slow endpoints with details
        """
        slow_endpoints = []
        
        for endpoint, stats in self.get_all_stats().items():
            if stats.get('avg_time', 0) > threshold:
                slow_endpoints.append({
                    "endpoint": endpoint,
                    "avg_time": stats['avg_time'],
                    "max_time": stats['max_time'],
                    "calls": stats['total_calls'],
                    "warning": "⚠️ SLOW ENDPOINT"
                })
        
        return sorted(slow_endpoints, key=lambda x: x['avg_time'], reverse=True)
    
    def get_error_prone_endpoints(self, min_error_rate: float = 5.0) -> List[Dict[str, Any]]:
        """
        Get endpoints with high error rates
        
        Args:
            min_error_rate: Minimum error rate percentage
            
        Returns:
            List of error-prone endpoints
        """
        error_endpoints = []
        
        for endpoint, stats in self.get_all_stats().items():
            error_rate = stats.get('error_rate', 0)
            if error_rate >= min_error_rate:
                error_endpoints.append({
                    "endpoint": endpoint,
                    "error_rate": error_rate,
                    "errors": stats['errors'],
                    "total_calls": stats['total_calls'],
                    "warning": "🚨 HIGH ERROR RATE"
                })
        
        return sorted(error_endpoints, key=lambda x: x['error_rate'], reverse=True)
    
    def get_most_used_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently called endpoints"""
        endpoints = []
        
        for endpoint, count in self.endpoint_calls.items():
            endpoints.append({
                "endpoint": endpoint,
                "calls": count,
                "percentage": round(count / sum(self.endpoint_calls.values()) * 100, 2)
            })
        
        return sorted(endpoints, key=lambda x: x['calls'], reverse=True)[:limit]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        all_times = []
        for times in self.request_times.values():
            all_times.extend(times)
        
        total_requests = sum(self.endpoint_calls.values())
        total_errors = sum(self.error_counts.values())
        
        return {
            "total_requests": total_requests,
            "total_endpoints": len(self.request_times),
            "total_errors": total_errors,
            "overall_error_rate": round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0,
            "avg_response_time": round(statistics.mean(all_times), 3) if all_times else 0,
            "median_response_time": round(statistics.median(all_times), 3) if all_times else 0,
            "slowest_request": round(max(all_times), 3) if all_times else 0,
            "fastest_request": round(min(all_times), 3) if all_times else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        # Check for slow endpoints
        slow = self.get_slow_endpoints(threshold=1.0)
        if slow:
            recommendations.append(
                f"⚠️ {len(slow)} endpoints are slower than 1 second. Consider optimization."
            )
        
        # Check for error-prone endpoints
        errors = self.get_error_prone_endpoints(min_error_rate=5.0)
        if errors:
            recommendations.append(
                f"🚨 {len(errors)} endpoints have error rates above 5%. Review error handling."
            )
        
        # Check overall performance
        summary = self.get_summary()
        if summary['avg_response_time'] > 0.5:
            recommendations.append(
                "📊 Average response time is above 500ms. Consider caching or optimization."
            )
        
        # Check for unbalanced load
        most_used = self.get_most_used_endpoints(limit=3)
        if most_used and most_used[0]['percentage'] > 50:
            recommendations.append(
                f"⚖️ Endpoint '{most_used[0]['endpoint']}' handles {most_used[0]['percentage']}% of traffic. Consider load balancing."
            )
        
        if not recommendations:
            recommendations.append("✅ All systems performing well!")
        
        return recommendations
    
    def reset_stats(self):
        """Reset all statistics"""
        self.request_times = defaultdict(list)
        self.endpoint_calls = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.status_codes = defaultdict(lambda: defaultdict(int))
        print("🔄 Performance stats reset")


# Global instance
performance_monitor = PerformanceMonitor()