import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, max_sessions: int = 50, session_timeout: int = 600):
        self.user_data = {}
        self.user_states = {}
        self.active_drivers = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self.last_cleanup = datetime.now()

    def cleanup_inactive_sessions(self):
        """Remove inactive sessions"""
        current_time = datetime.now()
        if (current_time - self.last_cleanup).seconds > 300:  # Check every 5 minutes
            for user_id in list(self.active_drivers.keys()):
                if user_id not in self.user_states or not self.user_states[user_id]:
                    self.cleanup_user_session(user_id)
            self.last_cleanup = current_time

    def cleanup_user_session(self, user_id: int):
        """Clean up a specific user's session"""
        try:
            if user_id in self.active_drivers:
                try:
                    self.active_drivers[user_id].quit()
                except Exception as e:
                    logger.error(f"Error closing driver for user {user_id}: {str(e)}")
                finally:
                    self.active_drivers.pop(user_id, None)

            self.user_data.pop(user_id, None)
            self.user_states.pop(user_id, None)
            logger.info(f"Cleaned up session for user {user_id}")
        except Exception as e:
            logger.error(f"Error in cleanup_user_session for {user_id}: {str(e)}")

    def set_state(self, user_id: int, state: Optional[str]):
        """Set user state with logging"""
        self.cleanup_inactive_sessions()
        previous_state = self.user_states.get(user_id)
        self.user_states[user_id] = state
        logger.info(f"User {user_id} state changed: {previous_state} -> {state}")

    def get_state(self, user_id: int) -> Optional[str]:
        """Get user's current state"""
        return self.user_states.get(user_id)

    def store_driver(self, user_id: int, driver, driver_type: str = 'linkedin'):
        """Store selenium driver reference"""
        self.cleanup_inactive_sessions()
        if len(self.active_drivers) >= self.max_sessions:
            oldest_user = next(iter(self.active_drivers))
            self.cleanup_user_session(oldest_user)

        if user_id in self.active_drivers:
            try:
                self.active_drivers[user_id].quit()
            except:
                pass
        self.active_drivers[user_id] = driver
        logger.info(f"Stored {driver_type} driver for user {user_id}")

    def get_driver(self, user_id: int):
        """Get stored selenium driver"""
        return self.active_drivers.get(user_id)

    def store_data(self, user_id: int, key: str, value: Any):
        """Store user data"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id][key] = value
        logger.info(f"Stored data '{key}' for user {user_id}")

    def get_data(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get user data with default value"""
        return self.user_data.get(user_id, {}).get(key, default)

    def clear_data(self, user_id: int):
        """Clear user data"""
        self.user_data.pop(user_id, None)
        logger.info(f"Cleared data for user {user_id}")

    def is_state_locked(self, user_id: int) -> bool:
        """Check if user's state is locked"""
        current_state = self.get_state(user_id)
        return current_state in ['offer_check', 'awaiting_offer_upload']

    def is_user_busy(self, user_id: int) -> bool:
        """Check if user is in a busy state"""
        busy_states = [
            'waiting_for_platform_selection',
            'waiting_for_linkedin_cookie',
            'waiting_for_job_keyword',
            'applying_to_jobs',
            'processing_applications',
            'waiting_for_resume',
            'processing_resume',
            'waiting_for_linkedin_profile',
            'processing_linkedin_profile',
            'internshala_cookie',
            'phpsessid_waiting',
            'processing_internshala',
            'awaiting_offer_upload',
            'offer_check'
            'waiting_for_access_key',
            'main_menu'
        ]
        return self.get_state(user_id) in busy_states

# Create global instance
session_manager = SessionManager()