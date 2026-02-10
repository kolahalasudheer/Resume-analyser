"""
API Usage Tracker
Monitors Gemini API usage and displays quota information to users.
Uses session state for real-time updates across the app.
"""

import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class APIUsageTracker:
    """Track and display API usage statistics using session state"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure one tracker instance"""
        if cls._instance is None:
            cls._instance = super(APIUsageTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize tracker with session state"""
        if self._initialized:
            return
            
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Try to get streamlit session state
        try:
            import streamlit as st
            if 'api_usage_stats' not in st.session_state:
                st.session_state.api_usage_stats = {
                    'requests_made': 0,
                    'tokens_used': 0,
                    'last_error': None
                }
            self.usage_stats = st.session_state.api_usage_stats
            self._has_session_state = True
        except:
            # Fallback to instance variable if streamlit not available
            self.usage_stats = {
                'requests_made': 0,
                'tokens_used': 0,
                'last_error': None
            }
            self._has_session_state = False
        
        self._initialized = True
    
    def get_quota_info(self) -> Dict:
        """
        Get API quota information
        
        Returns:
            dict: {
                'daily_limit': int,
                'requests_used': int,
                'percentage_used': float,
                'status': 'ok' | 'warning' | 'critical',
                'message': str
            }
        """
        if not self.api_key:
            return {
                'daily_limit': 0,
                'requests_used': 0,
                'percentage_used': 0,
                'status': 'no_key',
                'message': 'No API key configured'
            }
        
        try:
            # Free tier: ~15 RPM (requests per minute), ~1500 RPD (requests per day)
            daily_limit = 1500  # Free tier daily limit
            requests_used = self.usage_stats['requests_made']
            percentage_used = (requests_used / daily_limit * 100) if daily_limit > 0 else 0
            
            # Determine status
            if percentage_used < 50:
                status = 'ok'
                message = f"✅ {requests_used}/{daily_limit} requests used today"
            elif percentage_used < 80:
                status = 'warning'
                message = f"⚠️ {requests_used}/{daily_limit} requests used ({percentage_used:.1f}%)"
            else:
                status = 'critical'
                message = f"🔴 {requests_used}/{daily_limit} requests used ({percentage_used:.1f}%) - Consider getting new key"
            
            return {
                'daily_limit': daily_limit,
                'requests_used': requests_used,
                'percentage_used': percentage_used,
                'status': status,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"Error getting quota info: {str(e)}")
            return {
                'daily_limit': 0,
                'requests_used': 0,
                'percentage_used': 0,
                'status': 'error',
                'message': f'Error checking quota: {str(e)}'
            }
    
    def increment_usage(self, tokens_estimate: int = 1000):
        """
        Increment usage counter after API call
        
        Args:
            tokens_estimate: Estimated tokens used (default 1000)
        """
        self.usage_stats['requests_made'] += 1
        self.usage_stats['tokens_used'] += tokens_estimate
        
        # Update session state if available
        if self._has_session_state:
            try:
                import streamlit as st
                st.session_state.api_usage_stats = self.usage_stats
            except:
                pass
        
        logger.info(f"API usage: {self.usage_stats['requests_made']} requests, ~{self.usage_stats['tokens_used']} tokens")
    
    def reset_daily_usage(self):
        """Reset usage counters (call this daily)"""
        self.usage_stats['requests_made'] = 0
        self.usage_stats['tokens_used'] = 0
        
        # Update session state if available
        if self._has_session_state:
            try:
                import streamlit as st
                st.session_state.api_usage_stats = self.usage_stats
            except:
                pass
        
        logger.info("API usage counters reset")
    
    def get_usage_summary(self) -> str:
        """
        Get human-readable usage summary
        
        Returns:
            str: Usage summary message
        """
        quota_info = self.get_quota_info()
        
        if quota_info['status'] == 'no_key':
            return "⚠️ No API key - AI features disabled"
        
        percentage = quota_info['percentage_used']
        
        if percentage < 50:
            emoji = "🟢"
            advice = "You have plenty of quota remaining"
        elif percentage < 80:
            emoji = "🟡"
            advice = "Consider monitoring your usage"
        else:
            emoji = "🔴"
            advice = "Get a new API key soon to avoid interruption"
        
        return f"{emoji} **{percentage:.1f}%** of daily quota used | {advice}"

