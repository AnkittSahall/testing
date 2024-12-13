# import logging
# from datetime import datetime
# from supabase import create_client
# from typing import Dict

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Initialize Supabase client
# SUPABASE_URL = "https://bpqhyuekxyzgvumdgycr.supabase.co"
# SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwcWh5dWVreHl6Z3Z1bWRneWNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA3NDI1NjIsImV4cCI6MjA0NjMxODU2Mn0.rfPR6JJ9i7qcvthPlkq-YtJgx5k31qWd1wybS8BimWA"

# class DataManager:
#     def __init__(self):
#         self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#     def register_user(self, user_data: Dict) -> bool:
#         """Register or update a user in Supabase"""
#         try:
#             current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
#             # First check if user exists
#             response = self.supabase.table('users')\
#                 .select('*')\
#                 .eq('user_id', user_data['user_id'])\
#                 .execute()
                
#             if response.data:
#                 # Update existing user
#                 update_data = {
#                     'username': user_data.get('username', ''),
#                     'first_name': user_data.get('first_name', ''),
#                     'last_name': user_data.get('last_name', ''),
#                     'last_active': current_time
#                 }
                
#                 response = self.supabase.table('users')\
#                     .update(update_data)\
#                     .eq('user_id', user_data['user_id'])\
#                     .execute()
#             else:
#                 # Add new user
#                 new_user_data = {
#                     'user_id': user_data['user_id'],
#                     'username': user_data.get('username', ''),
#                     'first_name': user_data.get('first_name', ''),
#                     'last_name': user_data.get('last_name', ''),
#                     'registration_date': current_time,
#                     'last_active': current_time,
#                     'li_at_cookie': ''
#                 }
                
#                 response = self.supabase.table('users')\
#                     .insert(new_user_data)\
#                     .execute()

#             return True
#         except Exception as e:
#             logger.error(f"Error registering user: {str(e)}")
#             return False

#     def update_linkedin_cookie(self, user_id: int, li_at_cookie: str) -> bool:
#         """Update user's LinkedIn cookie in Supabase"""
#         try:
#             update_data = {
#                 'li_at_cookie': li_at_cookie,
#                 'last_active': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             }
            
#             response = self.supabase.table('users')\
#                 .update(update_data)\
#                 .eq('user_id', user_id)\
#                 .execute()
                
#             if response.data:
#                 return True
#             return False
            
#         except Exception as e:
#             logger.error(f"Error updating LinkedIn cookie: {str(e)}")
#             return False

#     def record_job_application(self, application_data):
#         """Save job application just like CSV but in Supabase"""
#         try:
#             data = {
#                 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'job_id': application_data.get('job_id', ''),
#                 'user_id': application_data['user_id'],
#                 'job_title': application_data['job_title'],
#                 'company_name': application_data['company_name'],
#                 'job_location': application_data.get('job_location', ''),
#                 'workplace_type': application_data.get('workplace_type', ''),
#                 'job_url': application_data['job_url'],
#                 'application_status': application_data['application_status'],
#                 'applicant_count': application_data.get('applicant_count', ''),
#                 'error_message': application_data.get('error_message', ''),
#                 'keyword_searched': application_data.get('keyword_searched', '')
#             }
#             self.supabase.table('job_applications').insert(data).execute()
#             return True
#         except Exception as e:
#             logger.error(f"Error recording job application: {str(e)}")
#             return False

#     def is_job_applied(self, job_id: str, user_id: int) -> bool:
#         """Check if job was applied (kept for compatibility)"""
#         try:
#             response = self.supabase.table('job_applications')\
#                 .select('*')\
#                 .eq('job_id', job_id)\
#                 .eq('user_id', user_id)\
#                 .eq('application_status', 'success')\
#                 .execute()
#             return len(response.data) > 0
#         except Exception as e:
#             logger.error(f"Error checking job application: {str(e)}")
#             return False

#     def handle_offer_response(self, user_id: int, response: str, file_path: str = None):
#         """Store offer letter response like we did with files"""
#         try:
#             data = {
#                 'user_id': user_id,
#                 'response': response,
#                 'file_path': file_path,
#                 'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'review_status': 'pending' if file_path else 'no_upload'
#             }
#             self.supabase.table('offer_letters').insert(data).execute()
#             return True
#         except Exception as e:
#             logger.error(f"Error handling offer response: {str(e)}")
#             return False

#     def upload_offer_letter(self, user_id: int, file_data: bytes, file_name: str) -> bool:
#         """Upload offer letter and record it"""
#         try:
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
#             file_path = f"user_{user_id}/{timestamp}_{file_name}"
            
#             # Upload file
#             response = self.supabase.storage\
#                 .from_('offer_letters')\
#                 .upload(
#                     path=file_path,
#                     file=file_data,
#                     file_options={"content-type": "application/pdf"}
#                 )
            
#             if response:
#                 # Record the upload
#                 self.handle_offer_response(user_id, 'yes', file_path)
#                 return True
#             return False
#         except Exception as e:
#             logger.error(f"Error uploading offer letter: {str(e)}")
#             return False

#     def get_user_name(self, user_id: int) -> str:
#         """Get user's name from Supabase"""
#         try:
#             response = self.supabase.table('users')\
#                 .select('first_name')\
#                 .eq('user_id', user_id)\
#                 .execute()
            
#             if response.data and len(response.data) > 0:
#                 return response.data[0].get('first_name', 'there')
#             return 'there'
#         except Exception as e:
#             logger.error(f"Error getting user name: {str(e)}")
#             return 'there'
        
#     def update_user_activity(self, user_id: int) -> bool:
#         """Update user's last active timestamp"""
#         try:
#             current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
#             response = self.supabase.table('users').update({
#                 'last_active': current_time
#             }).eq('user_id', user_id).execute()
            
#             logger.info(f"Updated last active time for user {user_id}")
#             return True
#         except Exception as e:
#             logger.error(f"Error updating user activity: {str(e)}")
#             return False    








#current file mew updated
import logging
import os
from datetime import datetime
from supabase import create_client
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import timedelta
# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self):
        """Initialize Supabase client with environment variables"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase configuration. Check your .env file.")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("DataManager initialized successfully")

    def _get_current_time(self) -> str:
        """Get formatted current timestamp"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _ensure_user_exists(self, user_data: dict) -> bool:
        """Helper method to ensure user record exists and is up to date"""
        try:
            # Check if user exists
            existing_user = self.supabase.table('users')\
                .select('*')\
                .eq('user_id', user_data['user_id'])\
                .execute()
                
            if existing_user.data and len(existing_user.data) > 0:
                # Update existing user
                update_response = self.supabase.table('users')\
                    .update(user_data)\
                    .eq('user_id', user_data['user_id'])\
                    .execute()
                return bool(update_response.data)
            else:
                # Create new user
                insert_response = self.supabase.table('users')\
                    .insert(user_data)\
                    .execute()
                return bool(insert_response.data)
                
        except Exception as e:
            logger.error(f"Error ensuring user exists: {str(e)}")
            return False

    def verify_access_key(self, access_key: str) -> Tuple[bool, dict]:
        """Verify access key and return user data if valid"""
        try:
            logger.info(f"Verifying access key...")
        
            # Clean the access key
            access_key = access_key.strip()
        
            # Query the database
            response = self.supabase.table('accelerator_users')\
                .select('*')\
                .eq('access_key', access_key)\
                .eq('signed_contract', True)\
                .execute()
        
            logger.info(f"Access key verification response: {response}")
        
            # Check if we have data and it's not empty
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"Found user with access key: {user_data}")
                return True, user_data
        
            logger.info("No user found with this access key or contract not signed")
            return False, {}
            
        except Exception as e:
            logger.error(f"Error verifying access key: {str(e)}")
            return False, {}

    def link_telegram_user(self, access_key: str, telegram_data: dict) -> bool:
        try:
            logger.info(f"Starting to link telegram user with access key: {access_key}")
        
            # 1. Get accelerator user first
            acc_user_response = self.supabase.table('accelerator_users')\
                .select('*')\
                .eq('access_key', access_key)\
                .execute()

            if not acc_user_response.data or len(acc_user_response.data) == 0:
                logger.error("No accelerator user found with this access key")
                return False

            accelerator_user_id = acc_user_response.data[0]['id']
            logger.info(f"Found accelerator user ID: {accelerator_user_id}")

            # 2. Update accelerator_users with telegram info
            current_time = datetime.now().isoformat()
            telegram_update = {
                'telegram_user_id': str(telegram_data['user_id']),
                'telegram_bot_user_id': str(telegram_data['user_id']),
                'last_login_attempt': current_time
            }
            
            logger.info(f"Telegram update payload: {telegram_update}")

            update_response = self.supabase.table('accelerator_users')\
                .update(telegram_update)\
                .eq('id', accelerator_user_id)\
                .execute()
                
            logger.info(f"Update response: {update_response}")
            
            # Verify the update by fetching the updated record
            verify_response = self.supabase.table('accelerator_users')\
                .select('*')\
                    .eq('id', accelerator_user_id)\
                        .single()\
                            .execute()
                            
            logger.info(f"Verification response: {verify_response}")
            
            if verify_response.data and verify_response.data.get('telegram_user_id') == str(telegram_data['user_id']):
                logger.info("Successfully verified telegram user update")
            else:
                logger.error("Update verification failed - trying alternative update method")
                
                # Alternative update method using upsert
                telegram_update['id'] = accelerator_user_id # Include ID for upsert
                update_response = self.supabase.table('accelerator_users')\
                    .upsert(telegram_update)\
                        .execute()
                        
                # Verify again
                verify_response = self.supabase.table('accelerator_users')\
                    .select('*')\
                        .eq('id', accelerator_user_id)\
                            .single()\
                                .execute()
                                
                logger.info(f"Second verification response: {verify_response.data}")
                
                if not (verify_response.data and verify_response.data.get('telegram_user_id') == str(telegram_data['user_id'])):
                    logger.error("Both update methods failed")
                    return False

            # 3. First check if user exists in users table
            user_exists = self.supabase.table('users')\
                .select('*')\
                .eq('user_id', telegram_data['user_id'])\
                .execute()

            if user_exists.data and len(user_exists.data) > 0:
                # Update existing user
                users_update = {
                    'accelerator_user_id': accelerator_user_id,
                    'username': telegram_data.get('username', ''),
                    'first_name': telegram_data.get('first_name', ''),
                    'last_name': telegram_data.get('last_name', ''),
                    'last_active': current_time
                }
                
                users_response = self.supabase.table('users')\
                    .update(users_update)\
                    .eq('user_id', telegram_data['user_id'])\
                    .execute()
            else:
                # Create new user
                users_response = self.supabase.table('users')\
                    .insert({
                        'user_id': telegram_data['user_id'],
                        'accelerator_user_id': accelerator_user_id,
                        'username': telegram_data.get('username', ''),
                        'first_name': telegram_data.get('first_name', ''),
                        'last_name': telegram_data.get('last_name', ''),
                        'registration_date': current_time,
                        'last_active': current_time
                    })\
                    .execute()

            # Changed response check - Supabase returns empty data array on success
            if users_response is None:
                logger.error("Failed to update/create user record - No response received")
                return False

            logger.info("Successfully linked telegram user and updated records")
            return True

        except Exception as e:
            logger.error(f"Error linking telegram user: {str(e)}")
            return False

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """Get user data by telegram ID"""
        try:
            logger.info(f"Getting user data for telegram ID: {telegram_id}")
            
            response = self.supabase.table('accelerator_users')\
                .select('*, users!inner(*)')\
                .eq('telegram_user_id', str(telegram_id))\
                .execute()
                    
            if response.data and len(response.data) > 0:
                logger.info(f"Found user data: {response.data[0]}")
                return response.data[0]
                
            logger.info("No user found with provided telegram ID")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None

    def get_user_complete_data(self, telegram_id: int) -> Optional[dict]:
        """Get complete user data including all relationships"""
        try:
            # Get accelerator user and basic info
            acc_user_response = self.supabase.table('accelerator_users')\
                .select('*')\
                .eq('telegram_user_id', str(telegram_id))\
                .single()\
                .execute()

            if not acc_user_response.data:
                return None

            acc_user = acc_user_response.data
            acc_user_id = acc_user['id']

            # Get user details
            user_response = self.supabase.table('users')\
                .select('*')\
                .eq('accelerator_user_id', acc_user_id)\
                .single()\
                .execute()

            # Get job applications
            jobs_response = self.supabase.table('job_applications')\
                .select('*')\
                .eq('accelerator_user_id', acc_user_id)\
                .execute()

            # Get offer letters
            offers_response = self.supabase.table('offer_letters')\
                .select('*')\
                .eq('accelerator_user_id', acc_user_id)\
                .execute()

            # Combine all data
            complete_data = {
                **acc_user,
                'user_details': user_response.data if user_response.data else {},
                'job_applications': jobs_response.data if jobs_response.data else [],
                'offer_letters': offers_response.data if offers_response.data else []
            }

            return complete_data

        except Exception as e:
            logger.error(f"Error getting complete user data: {str(e)}")
            return None

    def get_accelerator_user_id(self, telegram_id: int) -> Optional[int]:
        """Helper method to get accelerator_user_id from telegram_id"""
        try:
            response = self.supabase.table('accelerator_users')\
                .select('id')\
                .eq('telegram_user_id', str(telegram_id))\
                .single()\
                .execute()
                            
            if response.data:
                return response.data['id']
            return None
        except Exception as e:
            logger.error(f"Error getting accelerator_user_id: {str(e)}")
            return None

    def log_chat_interaction(self, telegram_id: int, message_type: str, content: str, direction: str, interaction_type: str = None):
        """Log chat interactions between user and bot"""
        try:
            accelerator_user_id = self.get_accelerator_user_id(telegram_id)
            
            chat_data = {
                'telegram_user_id': telegram_id,
                'accelerator_user_id': accelerator_user_id,
                'message_type': message_type,
                'content': content,
                'direction': direction,
                'interaction_type': interaction_type,  # Added this field
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.supabase.table('chat_logs')\
                .insert(chat_data)\
                .execute()
                    
            return bool(response.data)
        
        except Exception as e:
            logger.error(f"Error logging chat interaction: {str(e)}")
            return False

    def register_user(self, user_data: Dict) -> bool:
        """Register or update a user in Supabase"""
        try:
            current_time = self._get_current_time()
            user_id = user_data['user_id']

            # Check if user exists
            response = self.supabase.table('users')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()

            if response.data:
                # Update existing user
                update_data = {
                    'username': user_data.get('username', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'last_active': current_time
                }
                
                self.supabase.table('users')\
                    .update(update_data)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Add new user
                new_user_data = {
                    'user_id': user_id,
                    'username': user_data.get('username', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'registration_date': current_time,
                    'last_active': current_time,
                    'li_at_cookie': ''
                }
                
                self.supabase.table('users')\
                    .insert(new_user_data)\
                    .execute()

            logger.info(f"Successfully {'updated' if response.data else 'registered'} user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error registering user {user_data.get('user_id')}: {str(e)}")
            return False

    def update_linkedin_cookie(self, user_id: int, li_at_cookie: str) -> bool:
        """Update user's LinkedIn cookie"""
        try:
            response = self.supabase.table('users')\
                .update({
                    'li_at_cookie': li_at_cookie,
                    'last_active': self._get_current_time()
                })\
                .eq('user_id', user_id)\
                .execute()
                
            success = bool(response.data)
            if success:
                logger.info(f"Updated LinkedIn cookie for user {user_id}")
            return success

        except Exception as e:
            logger.error(f"Error updating LinkedIn cookie for user {user_id}: {str(e)}")
            return False

    def record_job_application(self, application_data: Dict) -> bool:
        """Record job application with accelerator_user_id"""
        try:
            accelerator_user_id = self.get_accelerator_user_id(application_data['user_id'])
            if not accelerator_user_id:
                logger.error(f"No accelerator_user_id found for user {application_data['user_id']}")
                return False

            job_data = {
                'timestamp': datetime.now().isoformat(),
                'job_id': application_data.get('job_id', ''),
                'user_id': application_data['user_id'],
                'accelerator_user_id': accelerator_user_id,
                'job_title': application_data['job_title'],
                'company_name': application_data['company_name'],
                'job_location': application_data.get('job_location', ''),
                'job_url': application_data['job_url'],
                'application_status': application_data['application_status'],
                'workplace_type': application_data.get('workplace_type', ''),
                'applicant_count': application_data.get('applicant_count', ''),
                'error_message': application_data.get('error_message', ''),
                'keyword_searched': application_data.get('keyword_searched', ''),
                'platform': application_data.get('platform', 'linkedin')
                
            }

            response = self.supabase.table('job_applications')\
                .insert(job_data)\
                .execute()

            # Log the interaction
            self.log_chat_interaction(
                telegram_id=application_data['user_id'],
                message_type='job_application',
                content=f"Applied to {application_data['job_title']} at {application_data['company_name']}",
                direction='outgoing',
                interaction_type='job_application'
            )

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error recording job application: {str(e)}")
            return False

    def is_job_applied(self, job_id: str, user_id: int) -> bool:
        """Check if job was already applied to"""
        try:
            response = self.supabase.table('job_applications')\
                .select('*')\
                .eq('job_id', job_id)\
                .eq('user_id', user_id)\
                .eq('application_status', 'success')\
                .execute()
                
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error checking job application status: {str(e)}")
            return False

    def handle_offer_response(self, user_id: int, response: str, file_path: Optional[str] = None) -> bool:
        """Store offer letter response with accelerator_user_id"""
        try:
            # Get accelerator_user_id
            accelerator_user_id = self.get_accelerator_user_id(user_id)
            if not accelerator_user_id:
                logger.error(f"No accelerator_user_id found for user {user_id}")
                return False
            
            offer_data = {
                'user_id': user_id,
                'accelerator_user_id': accelerator_user_id,
                'response': response,
                'file_path': file_path,
                'upload_date': datetime.now().isoformat(),
                'review_status': 'pending' if file_path else 'no_upload'
            }
            
            response = self.supabase.table('offer_letters')\
                .insert(offer_data)\
                .execute()
                    
            # Log the interaction
            self.log_chat_interaction(
                telegram_id=user_id,
                message_type='offer_letter',
                content=f"Offer letter submitted: {file_path if file_path else 'No_file'}",
                direction='incoming',
                interaction_type='offer_submission'
            )
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error handling offer response: {str(e)}")
            return False

    def upload_offer_letter(self, user_id: int, file_data: bytes, file_name: str) -> bool:
        """Upload offer letter to storage and record it"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"user_{user_id}/{timestamp}_{file_name}"
            
            # Upload file to storage
            response = self.supabase.storage\
                .from_('offer_letters')\
                .upload(
                    path=file_path,
                    file=file_data,
                    file_options={"content-type": "application/pdf"}
                )
            
            if response:
                # Record the upload
                success = self.handle_offer_response(user_id, 'yes', file_path)
                if success:
                    logger.info(f"Successfully uploaded offer letter for user {user_id}")
                return success

            return False

        except Exception as e:
            logger.error(f"Error uploading offer letter: {str(e)}")
            return False

    def get_user_name(self, user_id: int) -> str:
        """Get user's first name"""
        try:
            response = self.supabase.table('users')\
                .select('first_name')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data and response.data[0].get('first_name'):
                return response.data[0]['first_name']
            return 'there'

        except Exception as e:
            logger.error(f"Error getting user name: {str(e)}")
            return 'there'

    def update_user_activity(self, user_id: int) -> bool:
        """Update user's last active timestamp"""
        try:
            response = self.supabase.table('users')\
                .update({'last_active': self._get_current_time()})\
                .eq('user_id', user_id)\
                .execute()
            
            success = bool(response.data)
            if success:
                logger.info(f"Updated last active time for user {user_id}")
            return success

        except Exception as e:
            logger.error(f"Error updating user activity: {str(e)}")
            return False
        
    def get_recent_users(self, days: int = 30) -> list:
        """Get list of user IDs active in the last X days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table('users')\
                .select('user_id')\
                .gte('last_active', cutoff_date)\
                .execute()
                
            if response.data:
                # Convert all user_ids to integers and remove any None values
                user_ids = [int(user['user_id']) for user in response.data if user.get('user_id')]
                return user_ids
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent users: {str(e)}")
            return []    