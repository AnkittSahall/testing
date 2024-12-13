import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import json
from supabase import create_client
import timedelta
from dotenv import load_dotenv
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

@dataclass

class MessageMetadata:
    message_id: int
    chat_id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_bot: bool = False
    chat_type: Optional[str] = None
    reply_to_message_id: Optional[int] = None

class MessageLogger:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    def _get_accelerator_user_id(self, telegram_id: int) -> Optional[int]:
        """Get accelerator_user_id from telegram_id"""
        try:
            response = self.supabase.table('accelerator_users')\
                .select('id')\
                .eq('telegram_user_id', str(telegram_id))\
                .single()\
                .execute()
            
            if response.data and 'id' in response.data:
                # Convert id to int explicitly
                return int(response.data['id'])
            return None
            
        except Exception as e:
            logger.error(f"Error getting accelerator_user_id: {str(e)}")
            return None

    def _extract_message_metadata(self, message) -> MessageMetadata:
        """Extract metadata from telegram message object"""
        return MessageMetadata(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=message.from_user.id if message.from_user else None,
            username=message.from_user.username if message.from_user else None,
            first_name=message.from_user.first_name if message.from_user else None,
            last_name=message.from_user.last_name if message.from_user else None,
            is_bot=message.from_user.is_bot if message.from_user else False,
            chat_type=message.chat.type,
            reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None
        )

    def _extract_message_content(self, message) -> Dict[str, Any]:
        """Extract content from different types of messages"""
        content = {}

        if message.text:
            content['text'] = message.text
            content['entities'] = [
                {
                    'type': entity.type,
                    'offset': entity.offset,
                    'length': entity.length
                }
                for entity in message.entities
            ] if message.entities else []

        elif message.document:
            content['document'] = {
                'file_id': message.document.file_id,
                'file_name': message.document.file_name,
                'mime_type': message.document.mime_type,
                'file_size': message.document.file_size
            }
            content['caption'] = message.caption if message.caption else None

        elif message.photo:
            content['photo'] = [
                {
                    'file_id': photo.file_id,
                    'width': photo.width,
                    'height': photo.height,
                    'file_size': photo.file_size
                }
                for photo in message.photo
            ]
            content['caption'] = message.caption if message.caption else None

        return content

    def log_incoming_message(self, message) -> bool:
        """Log incoming message from user"""
        try:
            metadata = self._extract_message_metadata(message)
            content = self._extract_message_content(message)

            telegram_user_id = int(metadata.user_id) if metadata.user_id else None
            accelerator_user_id = self._get_accelerator_user_id(telegram_user_id)

            # Determine message type
            if message.text and message.text.startswith('/'):
                message_type = 'command'
            elif message.document:
                message_type = 'document'
            elif message.photo:
                message_type = 'photo'
            else:
                message_type = 'text'

            log_data = {
                'timestamp': datetime.now().isoformat(),
                'telegram_user_id': telegram_user_id,
                'accelerator_user_id': accelerator_user_id,
                'message_id': metadata.message_id,
                'chat_id': metadata.chat_id,
                'direction': 'incoming',
                'message_type': message_type,
                'content': json.dumps(content),
                'metadata': json.dumps({
                    'username': metadata.username,
                    'first_name': metadata.first_name,
                    'last_name': metadata.last_name,
                    'chat_type': metadata.chat_type,
                    'reply_to_message_id': metadata.reply_to_message_id,
                    'is_bot': metadata.is_bot
                }),
                'session_data': json.dumps({
                    'user_state': self._get_user_state(telegram_user_id),
                    'current_operation': self._get_current_operation(telegram_user_id)
                })
            }

            # Remove None values
            log_data = {k: v for k, v in log_data.items() if v is not None}

            response = self.supabase.table('chat_logs')\
                .upsert(log_data)\
                .execute()

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error logging incoming message: {str(e)}")
            return False

    def log_outgoing_message(self, message, bot_response: Union[str, Dict], response_type: str = 'text') -> bool:
        """Log outgoing message from bot"""
        try:
            metadata = self._extract_message_metadata(message)
            # Ensure telegram_user_id is int
            telegram_user_id = int(metadata.user_id) if metadata.user_id else None
            accelerator_user_id = self._get_accelerator_user_id(telegram_user_id)

            # Handle different types of bot responses
            content = {}
            if isinstance(bot_response, str):
                content['text'] = bot_response
            elif isinstance(bot_response, dict):
                content = bot_response
            else:
                content['data'] = str(bot_response)
            
            # content = self._prepare_content(bot_response)

            log_data = {
                'timestamp': datetime.now().isoformat(),
                'telegram_user_id': telegram_user_id,
                'accelerator_user_id': accelerator_user_id,
                'message_id': metadata.message_id,
                'chat_id': metadata.chat_id,
                'direction': 'outgoing',
                'message_type': response_type,
                'content': json.dumps(content),
                'metadata': json.dumps({
                    'is_bot': True,
                    'chat_type': metadata.chat_type,
                    'reply_to_message_id': metadata.message_id
                }),
                'session_data': json.dumps({
                    'user_state': self._get_user_state(metadata.user_id),
                    'current_operation': self._get_current_operation(metadata.user_id)
                })
            }

            # Remove None values
            log_data = {k: v for k, v in log_data.items() if v is not None}

            response = self.supabase.table('chat_logs')\
                .upsert(log_data)\
                .execute()

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error logging outgoing message: {str(e)}")
            return False

    def log_error(self, user_id: int, error_message: str, context: Optional[Dict] = None) -> bool:
        """Log error messages and exceptions"""
        try:
            accelerator_user_id = self._get_accelerator_user_id(user_id)
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'telegram_user_id': user_id,
                'accelerator_user_id': accelerator_user_id,
                'direction': 'system',
                'message_type': 'error',
                'content': json.dumps({
                    'error_message': error_message,
                    'context': context or {}
                }),
                'metadata': json.dumps({
                    'is_bot': True,
                    'error_type': type(error_message).__name__ if not isinstance(error_message, str) else 'String'
                }),
                'session_data': json.dumps({
                    'user_state': self._get_user_state(user_id),
                    'current_operation': self._get_current_operation(user_id)
                })
            }

            response = self.supabase.table('chat_logs').insert(log_data).execute()
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error logging error message: {str(e)}")
            return False

    def _get_user_state(self, user_id: int) -> Optional[str]:
        """Get current user state from global state"""
        try:
            from bot_handlers import get_user_state
            return get_user_state(user_id)
        except Exception:
            return None

    def _get_current_operation(self, user_id: int) -> Optional[str]:
        """Get current operation from user data"""
        try:
            from bot_handlers import user_data
            if user_id in user_data:
                return user_data[user_id].get('current_operation')
            return None
        except Exception:
            return None

    def get_conversation_history(self, user_id: int, limit: int = 50, offset: int = 0) -> list:
        """Retrieve conversation history for a specific user"""
        try:
            response = self.supabase.table('chat_logs')\
                .select('*')\
                .eq('telegram_user_id', user_id)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []

    def search_conversations(self, query: str, filters: Dict = None) -> list:
        """Search through conversations with optional filters"""
        try:
            base_query = self.supabase.table('chat_logs')\
                .select('*')

            # Apply text search on content
            if query:
                base_query = base_query.textSearch('content', query)

            # Apply additional filters
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        base_query = base_query.eq(key, value)

            response = base_query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error searching conversations: {str(e)}")
            return []

    def clear_old_logs(self, days: int = 90) -> bool:
        """Clear logs older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            response = self.supabase.table('chat_logs')\
                .delete()\
                .lt('timestamp', cutoff_date.isoformat())\
                .execute()

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error clearing old logs: {str(e)}")
            return False

# Initialize global message logger
message_logger = MessageLogger()