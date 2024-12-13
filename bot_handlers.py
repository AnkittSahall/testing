# import tempfile
# import os
# import logging
# from datetime import datetime, timedelta
# from telebot.types import ReplyKeyboardMarkup, KeyboardButton
# from linkedin_jobs import setup_driver, login_to_linkedin, search_jobs, apply_to_jobs, get_user_name
# from resume_generator import generate_resume
# from linkedin_improver import improve_linkedin_profile
# from internshala_automation import run_internshala_automation
# from data_manager import DataManager
# from supabase import create_client
# from typing import Optional
# from dotenv import load_dotenv
# from session_manager import session_manager  # Import the session manager
# from message import message_logger

# # Load environment variables
# load_dotenv()

# # Setup logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Initialize DataManager
# data_manager = DataManager()

# # Initialize Supabase with environment variables
# SUPABASE_URL = os.getenv('SUPABASE_URL')
# SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# if not all([SUPABASE_URL, SUPABASE_KEY]):
#     raise ValueError("Missing Supabase configuration. Check your .env file.")

# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# # Bot instance
# _bot = None
# _scheduler = None

# def initialize_bot(bot, scheduler):
#     """Initialize bot and scheduler instances"""
#     global _bot, _scheduler
#     _bot = bot
#     _scheduler = scheduler
#     logger.info("Bot initialized for handlers")

# def create_main_keyboard():
#     """Create main menu keyboard"""
#     keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
#     keyboard.add(KeyboardButton('Apply for jobs'), KeyboardButton('Improve Resume/CV'))
#     keyboard.add(KeyboardButton('Apply for Internships'), KeyboardButton('Improve LinkedIn Profile'))
#     keyboard.add(KeyboardButton('Restart'))
#     return keyboard

# def check_unverified_user(bot, message, user_data):
#     """
#     Check if user exists in users table without accelerator_user_id and handle verification
#     Returns True if verification is needed, False otherwise
#     """
#     try:
#         message_logger.log_incoming_message(message)
#         user_id = message.from_user.id
        
#         # Query users table for this telegram user
#         response = supabase.table('users')\
#             .select('*')\
#             .eq('user_id', user_id)\
#             .execute()
            
#         if response.data and len(response.data) > 0:
#             user = response.data[0]
#             # Check if user exists but doesn't have accelerator_user_id
#             if user.get('accelerator_user_id') is None:
#                 verification_msg = (
#                     "👋 Welcome back! I notice you've used our bot before, but we need to verify your account.\n\n"
#                     "🔐 To ensure your security and provide full access to all features, please verify your account:\n\n"
#                     "1️⃣ If you have an access key, please share it with me now.\n\n"
#                     "2️⃣ If you don't have an access key, you can get one by:\n"
#                     "   • Visiting: https://get-a-job.persistventures.com/\n"
#                     "   • Signing up with your LinkedIn profile\n"
#                     "   • Completing the verification process\n"
#                     "   • Signing the contract\n"
#                     "   • Checking your email for the access key\n\n"
#                     "🔄 Already registered? Get your access key at:\n"
#                     "https://get-a-job.persistventures.com/career-accelerator/login\n\n"
#                     "Please share your access key when ready! 🚀"
#                 )
#                 message_logger.log_incoming_message(message)
#                 bot.reply_to(message, verification_msg)
#                 session_manager.set_state(user_id, "waiting_for_access_key")
#                 return True
#         return False
        
#     except Exception as e:
#         logger.error(f"Error checking unverified user: {str(e)}")
#         return False

# def verify_user_access(user_id: int) -> tuple[bool, str, dict]:
#     """
#     Verify user's access and return status
#     Returns: (is_verified, message, user_data)
#     """
#     try:
#         # First check if user exists in accelerator_users
#         acc_user = data_manager.get_user_by_telegram_id(user_id)
    
#         if not acc_user:
#             # Check if user exists in users table
#             response = supabase.table('users')\
#                 .select('*')\
#                 .eq('user_id', user_id)\
#                 .execute()
            
#             if response.data and len(response.data) > 0:
#                 return False, "needs_verification", {}
#             else:
#                 return False, "new_user", {}
            
#         # User exists in accelerator_users, verify access
#         access_key = acc_user.get('access_key')
#         if not access_key:
#             return False, "needs_new_key", {}
        
#         # Verify the access key is still valid
#         is_valid, user_data = data_manager.verify_access_key(access_key)
#         if not is_valid:
#             return False, "expired_key", {}
        
#         return True, "verified", user_data
    
#     except Exception as e:
#         logger.error(f"Error in verify_user_access: {str(e)}")
#         return False, "error", {}

# def process_access_key(message, bot):
#     """
#     Process the access key provided by the user and verify their account
#     """
#     try:
#         message_logger.log_incoming_message(message)
#         # Handle restart command
#         if message.text and message.text.lower() == 'restart':
#             handle_restart(message, bot)
#             return

#         user_id = message.from_user.id
#         access_key = message.text.strip()

#         # First create/update the user record in users table
#         telegram_data = {
#             'user_id': user_id,
#             'username': message.from_user.username,
#             'first_name': message.from_user.first_name,
#             'last_name': message.from_user.last_name,
#             'registration_date': datetime.now().isoformat(),
#             'last_active': datetime.now().isoformat()
#         }
        
#         # Only update registration_date if it's a new user
#         existing_user = supabase.table('users')\
#             .select('*')\
#             .eq('user_id', user_id)\
#             .execute()
            
#         if not existing_user.data:
#             telegram_data['registration_date'] = datetime.now().isoformat()

#         data_manager.register_user(telegram_data)

#         # Then verify the access key
#         is_valid, user_data = data_manager.verify_access_key(access_key)
        
#         if not is_valid:
#             error_msg = (
#                 "❌ I couldn't verify your access key. Please check that:\n"
#                 "1. You've copied the complete key correctly\n"
#                 "2. You've signed the contract (for new users)\n"
#                 "3. Your account is fully verified\n\n"
#                 "Need a new access key?\n"
#                 "• New users: https://get-a-job.persistventures.com/\n"
#                 "• Existing users: https://get-a-job.persistventures.com/career-accelerator/login\n\n"
#                 "Please try again with a valid access key! 🔑"
#             )
#             message_logger.log_outgoing_message(message, error_msg)
#             bot.reply_to(message, error_msg)
#             session_manager.set_state(user_id, "waiting_for_access_key")
#             bot.register_next_step_handler(message, process_access_key, bot)
#             return

#         # If valid, link telegram user to accelerator user
#         if data_manager.link_telegram_user(access_key, telegram_data):
#             keyboard = create_main_keyboard()
#             success_msg = (
#                 f"🎉 Perfect! Your access key has been verified.\n\n"
#                 f"Welcome to Persist Ventures Career Accelerator, {user_data.get('full_name', 'there')}! "
#                 f"I'm excited to help you achieve your career goals!\n\n"
#                 f"Here's what I can help you with:\n"
#                 f"• Automated job applications on LinkedIn\n"
#                 f"• AI-powered resume enhancement\n"
#                 f"• LinkedIn profile optimization\n"
#                 f"• Internship applications\n"
#                 f"• Offer letter review & verification\n\n"
#                 f"What would you like to do first? Choose an option below! 👇"
#             )
#             message_logger.log_outgoing_message(message, success_msg)
#             bot.reply_to(message, success_msg, reply_markup=keyboard)
#             session_manager.set_state(user_id, "main_menu")
#         else:
#             error_msg = (
#                 "❌ I wasn't able to set up your account properly. "
#                 "Please try again or contact our support team.\n\n"
#                 "You can get help at: team@persistventures.com"
#             )
#             message_logger.log_outgoing_message(message, error_msg)
#             bot.reply_to(message, error_msg)
#             session_manager.set_state(user_id, "waiting_for_access_key")
#             bot.register_next_step_handler(message, process_access_key, bot)
            
#     except Exception as e:
#         logger.error(f"Error in process_access_key: {str(e)}")
#         error_msg = (
#             "Sorry, I encountered an error while processing your access key. "
#             "Please try again or contact our support team at team@persistventures.com"
#         )
#         message_logger.log_error(
#             message.from_user.id,
#             error_msg,
#             {"handler": "process_access_key", "error_type": type(e).__name__},
#         )
#         bot.r
#         bot.reply_to(message, error_msg)
#         session_manager.set_state(message.from_user.id, "waiting_for_access_key")
#         bot.register_next_step_handler(message, process_access_key, bot)

# def handle_start(bot, message):
#     """
#     Handle the /start command - First entry point for users
#     """
#     try:
#         message_logger.log_incoming_message(message)
#         user_id = message.from_user.id
        
#         user_data = session_manager.get_data(user_id, "user_data", {})
#         # First check if user needs verification
#         if check_unverified_user(bot, message, user_data):
#             return
        
#         # Get user data by telegram ID
#         accelerator_user = data_manager.get_user_by_telegram_id(user_id)
        
#         # If user exists and is verified
#         if accelerator_user and accelerator_user.get('telegram_user_id'):
#             keyboard = create_main_keyboard()
#             welcome_back_msg = (
#                 f"Welcome back to Persist Ventures Career Accelerator! 🎉\n\n"
#                 f"Hi {accelerator_user.get('full_name', 'there')}! I'm Hannah, "
#                 f"your AI career assistant. Let's continue your journey to success! 🚀\n\n"
#                 f"What would you like to do today?"
#             )
#             message_logger.log_outgoing_message(message, welcome_back_msg)
#             bot.reply_to(
#                 message,
#                 welcome_back_msg,
#                 reply_markup=keyboard
#             )
#             session_manager.set_state(user_id, "main_menu")
#             return

#         # For new or unverified users
#         welcome_msg = (
#             "👋 Hello! I'm Hannah, your AI-powered career guide at Persist Ventures! 🌟\n\n"
#             "I'm here to help you find amazing job opportunities and accelerate your career growth! "
#             "To get started, I'll need your access key.\n\n"
#             "🔑 Here's how to get your access key:\n\n"
#             "🆕 For New Users:\n"
#             "1. Visit: https://get-a-job.persistventures.com/\n"
#             "2. Sign up with your LinkedIn profile\n"
#             "3. Complete our AI-powered verification process\n"
#             "4. Sign the contract\n"
#             "5. Check your email for the access key\n\n"
#             "🔄 For Existing Users:\n"
#             "1. Login at: https://get-a-job.persistventures.com/career-accelerator/login\n"
#             "2. You'll receive an email with your access key\n\n"
#             "Once you have your access key, please share it with me to begin! 🚀"
#         )
#         message_logger.log_outgoing_message(message, welcome_msg)
#         bot.reply_to(message, welcome_msg)
        
#         session_manager.set_state(user_id, "waiting_for_access_key")
#         bot.register_next_step_handler(message, process_access_key, bot)
        
#     except Exception as e:
#         logger.error(f"Error in handle_start: {str(e)}")
#         error_msg = (
#             "I apologize, but I encountered an error while starting up. "
#             "Please try again or contact our support team at team@persistventures.com "
#             "if the issue persists."
#         )
#         message_logger.log_error(
#             message.from_user.id,
#             error_msg,
#             {"handler": "handle_start", "error_type": type(e).__name__},
#         )
#         bot.reply_to(message, error_msg)

# def handle_restart(message, bot):
#     chat_id = message.chat.id
#     current_state = session_manager.get_state(chat_id)
    
#     logger.info(f"Handling restart for user {chat_id} from state: {current_state}")
    
#     try:
#         message_logger.log_incoming_message(message)
#         # Don't interrupt offer check states
#         if session_manager.is_state_locked(chat_id):
#             reply_to_offer_check_msg = (
#                 "📌 Please respond to the offer check first.\n"
#                 "This helps us ensure your job search security!\n"
#                 "Once you respond, you can access all features again."
#             )
#             message_logger.log_outgoing_message(message, reply_to_offer_check_msg)
#             bot.reply_to(message, reply_to_offer_check_msg, parse_mode="HTML")
#             return

#         # First verify user access
#         is_verified, status, user_data = verify_user_access(chat_id)
        
#         # Handle different verification scenarios
#         if not is_verified:
#             if status == "error":
#                 error_msg = "❌ Sorry, there was an error verifying your access. Please try again later or contact support."
#                 message_logger.log_outgoing_message(message, error_msg)
#                 bot.reply_to(message, error_msg, parse_mode="HTML")
#                 return
                
#             elif status in ["needs_verification", "new_user"]:
#                 verification_msg = (
#                     "👋 Welcome to Persist Ventures Career Accelerator!\n\n"
#                     "🔐 To access all features, please verify your account:\n\n"
#                     "1️⃣ If you have an access key, please share it with me now.\n\n"
#                     "2️⃣ If you don't have an access key, you can get one by:\n"
#                     "   • Visiting: https://get-a-job.persistventures.com/\n"
#                     "   • Signing up with your LinkedIn profile\n"
#                     "   • Completing the verification process\n"
#                     "   • Signing the contract\n"
#                     "   • Checking your email for the access key\n\n"
#                     "🔄 Already registered? Get your access key at:\n"
#                     "https://get-a-job.persistventures.com/career-accelerator/login\n\n"
#                     "Please share your access key when ready! 🚀"
#                 )
#                 message_logger.log_outgoing_message(message, verification_msg)
#                 bot.reply_to(message, verification_msg)
#                 session_manager.set_state(chat_id, "waiting_for_access_key")
#                 bot.register_next_step_handler(message, process_access_key, bot)
#                 return
                
#             elif status in ["needs_new_key", "expired_key"]:
#                 expired_msg = (
#                     "🔑 Your access key has expired or is invalid.\n\n"
#                     "To continue using our services, please get a new access key:\n"
#                     "1. Visit: https://get-a-job.persistventures.com/career-accelerator/login\n"
#                     "2. Login with your account\n"
#                     "3. You'll receive a new access key via email\n\n"
#                     "Once you have your new access key, please share it with me! 🌟"
#                 )
#                 message_logger.log_outgoing_message(message, expired_msg)
#                 bot.reply_to(message, expired_msg)
#                 session_manager.set_state(chat_id, "waiting_for_access_key")
#                 bot.register_next_step_handler(message, process_access_key, bot)
#                 return

#         # Clean up session
#         session_manager.cleanup_user_session(chat_id)
        
#         # Get user's name for personalized message
#         user_name = user_data.get('full_name', 'there')
        
#         # Send restart confirmation
#         restart_msg = (
#             f"🔄 Welcome back, {user_name}!\n\n"
#             "I've reset everything and we're ready to start fresh. "
#             "All previous operations have been cancelled.\n\n"
#             "What would you like to do? 😊"
#         )
        
#         message_logger.log_outgoing_message(message, restart_msg)

#         bot.reply_to(
#             message,
#             restart_msg,
#             reply_markup=create_main_keyboard()
#         )
        
#         logger.info(f"Successfully restarted bot for verified user {chat_id}")
        
#     except Exception as e:
#         logger.error(f"Error during restart for user {chat_id}: {str(e)}")
#         error_msg = (
#             "❌ There was an error restarting the bot, but all processes have been stopped.\n"
#             "Please try your operation again."
#         )
#         message_logger.log_error(message.from_user.id, str(e), {
#             'handler': 'handle_restart',
#             'error_type': type(e).__name__,
#             'state': session_manager.get_state(chat_id)
#         })
#         bot.reply_to(message, error_msg, reply_markup=create_main_keyboard())

# def handle_apply_jobs(bot, message):
#     """Handle job application request"""
#     try:
#         user_id = message.from_user.id
#         session_manager.set_state(user_id, 'waiting_for_linkedin_cookie')
        
#         bot.reply_to(
#             message,
#             "🎯 Awesome! You're one step closer to your new career opportunity!\n\n"
#             "💼 To proceed with your application, I'll need your LinkedIn 'li_at' cookie value.\n\n"
#             "❓ Not sure how to find it?\n"
#             "📹 Watch this quick guide:\n"
#             "https://www.loom.com/share/aa9850210ff24a25afc949f637e01254?sid=245233a2-2140-4839-9a51-bd5d370d3573\n\n"
#             "✍️ Provide me the cookies once you have it, and we'll continue from there!\n\n"
#             "💡 Tip: Click 'restart' anytime to return to the main menu! 🔄"
#         )
#         bot.register_next_step_handler(message, process_li_at, bot)
#     except Exception as e:
#         logger.error(f"Error in handle_apply_jobs: {str(e)}")
#         session_manager.set_state(message.from_user.id, None)
#         bot.reply_to(message, "Sorry, there was an error. Please try again or click Restart.")

# def process_li_at(message, bot):
#     """Process LinkedIn cookie input"""
#     if message.text and message.text.lower() == 'restart':
#         handle_restart(message, bot)
#         return
        
#     try:
#         user_id = message.from_user.id
#         session_manager.set_state(user_id, 'waiting_for_linkedin_cookie')
        
#         li_at = message.text.strip()
#         data_manager.update_linkedin_cookie(user_id, li_at)
        
#         driver = setup_driver()
#         try:
#             session_manager.store_driver(user_id, driver, 'linkedin')
#             login_success = login_to_linkedin(driver, li_at)
            
#             if login_success:
#                 user_name = get_user_name(driver)
#                 session_manager.set_state(user_id, 'waiting_for_job_keyword')
#                 session_manager.store_data(user_id, 'li_at', li_at)  # Store for later use
                
#                 greeting = (
#                     f"Hi {user_name}! 👋 Thanks so much for logging in successfully! 🎉\n\n"
#                     "I'm excited to help you find the perfect job! ✨\n"
#                     "What kind of position are you looking for today? 💼\n"
#                     "Just enter a keyword (e.g., 'Python Developer' 👩‍💻) "
#                     "and we'll get started on your search! 🚀\n\n"
#                     "Remember, you can click 'restart' Button anytime to return to the main menu! 🔄"
#                 )
#                 bot.reply_to(message, greeting)
#                 bot.register_next_step_handler(message, lambda m: handle_job_search(m, driver, bot))
#             else:
#                 session_manager.cleanup_user_session(user_id)
#                 bot.reply_to(
#                     message, 
#                     "⚠️ Login failed! 🚫\n\n"
#                     "Please check your LinkedIn cookie and try again. 🔍\n"
#                     "Make sure you've copied the correct 'li_at' value. ✅\n\n"
#                     "You can click 'Restart' to try again! 🔄"
#                 )
#         except Exception as e:
#             session_manager.cleanup_user_session(user_id)
#             logger.error(f"Error in LinkedIn login: {str(e)}")
#             bot.reply_to(
#                 message, 
#                 f"Oh no! 😟 It looks like there was an issue logging you in.\n\n"
#                 f"❌ Error: {str(e)}\n\n"
#                 "Please check your cookie and try again by clicking 'Restart' 🔄"
#             )
#     except Exception as e:
#         logger.error(f"Error in process_li_at: {str(e)}")
#         session_manager.cleanup_user_session(message.from_user.id)
#         bot.reply_to(
#             message, 
#             "❌ Sorry, there was an error processing your LinkedIn cookie. 😕\n"
#             "Please try again by clicking 'Restart' 🔄"
#         )

# def handle_job_search(message, driver, bot):
#     """Handle job search process"""
#     user_id = message.from_user.id
    
#     if message.text and message.text.lower() == 'restart':
#         handle_restart(message, bot)
#         session_manager.cleanup_user_session(user_id)
#         return
        
#     try:
#         session_manager.set_state(user_id, 'applying_to_jobs')
#         session_manager.store_data(user_id, 'search_keyword', message.text.strip())
        
#         keyword = message.text.strip()
#         bot.reply_to(
#             message, 
#             f"Great choice! I'm on it—searching for '{keyword}' jobs with the Easy Apply filter. "
#             "This might take a moment, but I'll find the best opportunities for you! 😊 Please hold tight!"
#         )
        
#         job_listings = search_jobs(driver, keyword)
#         if not job_listings:
#             session_manager.set_state(user_id, None)
#             bot.reply_to(
#                 message, 
#                 "Oh no! I couldn't find any job listings. 😟 Let's try again—please restart the bot to start the process. "
#                 "I'm here to help you find the perfect job! 💪"
#             )
#             return
            
#         bot.reply_to(
#             message, 
#             f"Great news! 🎉 I found {len(job_listings)} job listings for you. "
#             "I'm starting to apply to them right now! 😊 Sit tight, and I'll keep you updated on the progress..."
#         )
        
#         applied_count = apply_to_jobs(driver, job_listings, bot, message)
        
#         if applied_count == 0:
#             bot.reply_to(
#                 message, 
#                 "Oh no! 😟 I wasn't able to successfully apply to any of the job listings. "
#                 "Please restart the bot to start the application process again. "
#                 "I'm here to help you every step of the way! 💪"
#             )
#         else:
#             bot.reply_to(
#                 message, 
#                 f"✅ Great! I successfully applied to {applied_count} jobs for you. 🎉 "
#                 "If you'd like to apply to more jobs with a different keyword, "
#                 "please restart the bot to start the process again. I'm here to help! 😊"
#             )
#     except Exception as e:
#         logger.error(f"Error in job search/application: {str(e)}")
#         bot.reply_to(
#             message,
#             f"Oh no! 😟 Something went wrong during the job search and application process. "
#             "Please restart the bot to try again. I'm here to help you every step of the way! 💪"
#         )
#     finally:
#         session_manager.cleanup_user_session(user_id)
        
#     # Return to main menu
#     bot.reply_to(
#         message, 
#         "We're back to the main menu! 😊 Please choose one of the options below to continue:", 
#         reply_markup=create_main_keyboard()
#     )

# def handle_improve_resume(bot, message):
#     """Handle resume improvement request"""
#     try:
#         user_id = message.from_user.id
#         session_manager.set_state(user_id, 'waiting_for_resume')
        
#         bot.reply_to(
#             message, 
#             "🎯 Sure thing!\n\n"
#             "📄 Please send me your current resume as a PDF file, and I'll help you create an enhanced version using AI.\n\n" 
#             "🚀 Let's get started!\n\n"
#             "💡 You can click 'restart' Button anytime to return to the main menu! 🔄"
#         )
#         bot.register_next_step_handler(message, process_resume, bot)
#     except Exception as e:
#         session_manager.set_state(message.from_user.id, None)
#         logger.error(f"Error in handle_improve_resume: {str(e)}")
#         bot.reply_to(message, "Sorry, there was an error. Please try again or click Restart.")

# def process_resume(message, bot):
#     """Process resume PDF upload"""
#     if message.text and message.text.lower() == 'restart':
#         handle_restart(message, bot)
#         return
        
#     try:
#         user_id = message.from_user.id
#         if session_manager.is_state_locked(user_id):
#             return
            
#         session_manager.set_state(user_id, 'processing_resume')
#         temp_file_path = None
        
#         if message.document and message.document.mime_type == 'application/pdf':
#             try:
#                 file_info = bot.get_file(message.document.file_id)
#                 downloaded_file = bot.download_file(file_info.file_path)
                
#                 with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
#                     temp_file.write(downloaded_file)
#                     temp_file_path = temp_file.name
                
#                 bot.reply_to(message, "Great! 😊 I've received your resume and I'm processing it now. 🚀 I'll get back to you shortly with an enhanced version...")
                
#                 with open(temp_file_path, 'rb') as resume_file:
#                     api_response = generate_resume(resume_file)
                
#                 if isinstance(api_response, str) and os.path.exists(api_response):
#                     with open(api_response, 'rb') as improved_resume:
#                         bot.send_document(
#                             message.chat.id, 
#                             improved_resume,
#                             caption="Here's your improved resume! 🎉 I've enhanced it to better showcase your skills and experience. Click 'restart' Button to return to the main menu!"
#                         )
#                     os.remove(api_response)
#                 else:
#                     error_message = str(api_response)[:3997] + "..." if len(str(api_response)) > 4000 else str(api_response)
#                     bot.reply_to(message, f"API Error: {error_message}")
            
#             finally:
#                 if temp_file_path and os.path.exists(temp_file_path):
#                     try:
#                         os.remove(temp_file_path)
#                     except Exception as e:
#                         logger.error(f"Error deleting temporary file: {str(e)}")
#                 session_manager.set_state(user_id, None)
        
#         else:
#             bot.reply_to(message, "Please make sure to send your resume as a PDF file.")
#             session_manager.set_state(user_id, 'waiting_for_resume')
#             bot.register_next_step_handler(message, process_resume, bot)
#             return
        
#         # Return to main menu
#         bot.reply_to(message, "Returning to main menu 😊. Choose an option:", reply_markup=create_main_keyboard())
        
#     except Exception as e:
#         logger.error(f"Error in process_resume: {str(e)}")
#         session_manager.set_state(message.from_user.id, None)
#         bot.reply_to(message, "Sorry, there was an error processing your resume. Please try again.")
#         bot.reply_to(message, "Returning to main menu:", reply_markup=create_main_keyboard())

# def handle_improve_linkedin(bot, message):
#     """Handle LinkedIn profile improvement request"""
#     try:
#         user_id = message.from_user.id
#         session_manager.set_state(user_id, 'waiting_for_linkedin_profile')
        
#         bot.reply_to(
#             message,
#             "Let's improve your LinkedIn profile! 🚀\n\n"
#             "First, I'll need your LinkedIn 'li_at' cookie. If you're not sure how to get it, "
#             "check out this guide: https://www.loom.com/share/aa9850210ff24a25afc949f637e01254\n\n"
#             "Please paste your li_at cookie here.\n\n"
#             "You can click 'restart' Button anytime to return to the main menu! 🔄"
#         )
#         bot.register_next_step_handler(message, process_linkedin_cookie, bot)
#     except Exception as e:
#         session_manager.set_state(message.from_user.id, None)
#         logger.error(f"Error in handle_improve_linkedin: {str(e)}")
#         bot.reply_to(message, "Sorry, there was an error. Please try again or click Restart.")

# def process_linkedin_cookie(message, bot):
#     """Process LinkedIn cookie for profile improvement"""
#     if message.text and message.text.lower() == 'restart':
#         handle_restart(message, bot)
#         return
        
#     try:
#         user_id = message.chat.id
#         if session_manager.is_state_locked(user_id):
#             return
            
#         session_manager.store_data(user_id, 'li_at', message.text.strip())
        
#         bot.reply_to(
#             message,
#             "Great! Now, please share your LinkedIn profile URL "
#             "(e.g., https://www.linkedin.com/in/username)\n\n"
#             "You can click 'restart' Button anytime to return to the main menu! 🔄"
#         )
#         bot.register_next_step_handler(message, process_linkedin_url, bot)
#     except Exception as e:
#         logger.error(f"Error in process_linkedin_cookie: {str(e)}")
#         bot.reply_to(message, "Sorry, there was an error. Please try again or click Restart.")

# def process_linkedin_url(message, bot):
#     """Process LinkedIn profile URL"""
#     if message.text and message.text.lower() == 'restart':
#         handle_restart(message, bot)
#         return
        
#     try:
#         user_id = message.chat.id
#         if session_manager.is_state_locked(user_id):
#             return
            
#         profile_url = message.text.strip()
        
#         if not profile_url.startswith('https://www.linkedin.com/in/'):
#             bot.reply_to(
#                 message,
#                 "Please provide a valid LinkedIn profile URL starting with 'https://www.linkedin.com/in/'\n"
#                 "Try again or click 'restart' to return to main menu."
#             )
#             bot.register_next_step_handler(message, process_linkedin_url, bot)
#             return
            
#         bot.reply_to(message, "Processing your LinkedIn profile... Please wait! 🔄")
        
#         li_at = session_manager.get_data(user_id, 'li_at')
#         result = improve_linkedin_profile(profile_url, li_at)
        
#         if result["success"]:
#             bot.reply_to(
#                 message,
#                 f"✅ Success! Here are your profile improvement suggestions:\n\n"
#                 f"{result['message']}\n\n"
#                 "Would you like to improve anything else? Choose an option from the menu below:",
#                 reply_markup=create_main_keyboard()
#             )
#         else:
#             bot.reply_to(
#                 message,
#                 f"❌ Sorry, there was an error: {result['message']}\n"
#                 "Please try again or choose another option:",
#                 reply_markup=create_main_keyboard()
#             )
            
#     except Exception as e:
#         logger.error(f"Error in process_linkedin_url: {str(e)}")
#         session_manager.cleanup_user_session(user_id)
#         bot.reply_to(
#             message,
#             "Sorry, there was an error processing your LinkedIn profile. Please try again.",
#             reply_markup=create_main_keyboard()
#         )

# def handle_apply_internships(bot, message):
#     """Handle internship application request"""
#     try:
#         user_id = message.from_user.id
#         session_manager.set_state(user_id, 'internshala_cookie')
        
#         bot.reply_to(
#             message, 
#             "Fantastic choice! 🌟 Let's help you land an amazing internship opportunity! \n\n"
#             "First, I'll need your Internshala cookie to help you apply. Here's how to get it: \n"
#             "1. Log in to Internshala in your web browser 🌐\n"
#             "2. Open developer tools (F12 or right-click > Inspect) 🔍\n"
#             "3. Click on 'Application' or 'Storage' tab 📑\n"
#             "4. Look for 'Cookies' and find the value for 'PHPSESSID' 🍪\n\n"
#             "Once you have it, just paste it here and we'll get started on your applications! 😊\n\n"
#             "Remember, You can click 'restart' Button anytime to return to the main menu! 🔄"
#         )
#         bot.register_next_step_handler(message, process_phpsessid, bot)
#     except Exception as e:
#         session_manager.set_state(message.from_user.id, None)
#         logger.error(f"Error in handle_apply_internships: {str(e)}")
#         bot.reply_to(message, "Sorry, there was an error. Please try again or click Restart.")

# def process_phpsessid(message, bot):
#     """Process Internshala PHPSESSID cookie"""
#     if message.text and message.text.lower() == 'restart':
#         handle_restart(message, bot)
#         return

#     try:
#         user_id = message.chat.id
#         if session_manager.is_state_locked(user_id):
#             return
            
#         session_manager.set_state(user_id, 'processing_internshala')
#         session_manager.store_data(user_id, 'phpsessid', message.text.strip())
        
#         bot.reply_to(
#             message,
#             "Perfect! Thanks for that! 🎉\n\n"
#             "Now, I can help you apply to various exciting internship roles! 🚀\n"
#             "I can apply for these amazing opportunities:\n"
#             "📊 Data Science\n"
#             "💻 Software Development\n"
#             "🌐 Web Development\n"
#             "📈 Data Analytics\n"
#             "🐍 Python Django\n"
#             "📊 Business Analytics\n\n"
#             "How many applications would you like me to submit for each role? "
#             "(For example, if you choose 5, I'll apply to 5 internships in each category, "
#             "making it 30 total applications!) ✨\n\n"
#             "Please enter a number (I recommend starting with 5! 😊)\n\n"
#             "Remember, You can click 'restart' Button anytime to return to the main menu! 🔄"
#         )
#         bot.register_next_step_handler(message, process_internshala_applications, bot)
#     except Exception as e:
#         session_manager.set_state(message.from_user.id, None)
#         logger.error(f"Error in process_phpsessid: {str(e)}")
#         bot.reply_to(message, "Sorry, there was an error. Please try again or click Restart.")

# # def process_internshala_applications(message, bot):
# #     """Process Internshala applications"""
# #     chat_id = message.chat.id
# #     driver = None
# #     restart_requested = message.text and message.text.lower() == 'restart'

# #     if restart_requested:
# #         session_manager.cleanup_user_session(chat_id)
# #         handle_restart(message, bot)
# #         return

# #     try:
# #         if session_manager.is_state_locked(chat_id):
# #             return

# #         num_applications = int(message.text)
# #         status_message = bot.reply_to(
# #             message,
# #             f"Wonderful choice! 🎯 I'm super excited to help you apply for internships!\n\n"
# #             f"I'll be applying to {num_applications} internships in each category, "
# #             f"for a total of {num_applications * 6} applications! 🚀\n\n"
# #             "Just sit back and relax while I work my magic! ✨\n"
# #             "This might take a little while, but I'll keep you updated on the progress! 😊"
# #         )

# #         def progress_callback(job_role, role_count, total_count):
# #             try:
# #                 role_display = {
# #                     'data-science': 'Data Science 📊',
# #                     'software-development': 'Software Development 💻',
# #                     'web-development': 'Web Development 🌐',
# #                     'data-analytics': 'Data Analytics 📈',
# #                     'python-django': 'Python Django 🐍',
# #                     'business-analytics': 'Business Analytics 📊'
# #                 }.get(job_role, job_role)

# #                 bot.edit_message_text(
# #                     f"🚀 Your Internship Application Progress:\n\n"
# #                     f"Currently applying for: {role_display}\n"
# #                     f"✅ Applications in this category: {role_count}\n"
# #                     f"🎯 Total applications submitted: {total_count}\n\n"
# #                     f"I'm working hard to submit your applications! 💪\n"
# #                     "You can Click 'restart' Button anytime to stop and return to main menu! 😊",
# #                     chat_id=chat_id,
# #                     message_id=status_message.message_id
# #                 )
# #             except Exception as e:
# #                 logger.error(f"Error updating progress: {str(e)}")

# #         driver = setup_driver()
# #         session_manager.store_driver(chat_id, driver, 'internshala')

# #         phpsessid = session_manager.get_data(chat_id, 'phpsessid')
# #         run_internshala_automation(
# #             driver,
# #             phpsessid,
# #             num_applications,
# #             progress_callback
# #         )

# #         if not restart_requested:
# #             bot.send_message(
# #                 chat_id,
# #                 "🎉 Amazing news! I've completed all the applications!\n\n"
# #                 f"✅ Successfully applied to {num_applications * 6} internships across all categories!\n"
# #                 "🌟 You can check all your applications here:\n"
# #                 "https://internshala.com/student/applications\n\n"
# #                 "Good luck with your applications! 🍀\n\n"
# #                 "Is there anything else you'd like me to help you with? 😊",
# #                 reply_markup=create_main_keyboard()
# #             )

# #     except ValueError:
# #         if not restart_requested:
# #             bot.reply_to(
# #                 message, 
# #                 "Oops! 😅 That doesn't seem to be a valid number. "
# #                 "Could you please enter a number like 5? Let's try again! 🎯"
# #             )
# #             bot.register_next_step_handler(message, process_internshala_applications, bot)
# #     except Exception as e:
# #         if not restart_requested:
# #             logger.error(f"Error processing internshala applications: {str(e)}")
# #             bot.reply_to(
# #                 message,
# #                 "Sorry, there was an error processing your request. Please try again or click Restart.",
# #                 reply_markup=create_main_keyboard()
# #             )
# #     finally:
# #         session_manager.cleanup_user_session(chat_id)

# def process_internshala_applications(message, bot):
#     """Process Internshala applications with job tracking"""
#     chat_id = message.chat.id
#     driver = None
#     restart_requested = message.text and message.text.lower() == 'restart'

#     if restart_requested:
#         message_logger.log_incoming_message(message)
#         session_manager.cleanup_user_session(chat_id)
#         handle_restart(message, bot)
#         return

#     try:
#         message_logger.log_incoming_message(message)
#         if session_manager.is_state_locked(chat_id):
#             locked_msg = "Please complete the current operation first."
#             message_logger.log_outgoing_message(message, locked_msg)
#             bot.reply_to(message, locked_msg)
#             return

#         num_applications = int(message.text)
#         start_msg = (
#             f"Wonderful choice! 🎯 I'm super excited to help you apply for internships!\n\n"
#             f"I'll be applying to {num_applications} internships in each category, "
#             f"for a total of {num_applications * 6} applications! 🚀\n\n"
#             "Just sit back and relax while I work my magic! ✨\n"
#             "This might take a little while, but I'll keep you updated on the progress! 😊"
#         )
#         message_logger.log_outgoing_message(message, start_msg)
#         status_message = bot.reply_to(message, start_msg)

#         def progress_callback(job_role, role_count, total_count):
#             try:
#                 role_display = {
#                     'data-science': 'Data Science 📊',
#                     'software-development': 'Software Development 💻',
#                     'web-development': 'Web Development 🌐',
#                     'data-analytics': 'Data Analytics 📈',
#                     'python-django': 'Python Django 🐍',
#                     'business-analytics': 'Business Analytics 📊'
#                 }.get(job_role, job_role)

#                 bot.edit_message_text(
#                     f"🚀 Your Internship Application Progress:\n\n"
#                     f"Currently applying for: {role_display}\n"
#                     f"✅ Applications in this category: {role_count}\n"
#                     f"🎯 Total applications submitted: {total_count}\n\n"
#                     f"I'm working hard to submit your applications! 💪\n"
#                     "You can Click 'restart' Button anytime to stop and return to main menu! 😊",
#                     chat_id=chat_id,
#                     message_id=status_message.message_id
#                 )
#             except Exception as e:
#                 logger.error(f"Error updating progress: {str(e)}")

#         driver = setup_driver()
#         session_manager.store_driver(chat_id, driver, 'internshala')

#         phpsessid = session_manager.get_data(chat_id, 'phpsessid')
        
#         # Pass the user_id and data_manager to run_internshala_automation
#         run_internshala_automation(
#             driver=driver,
#             phpsessid=phpsessid,
#             num_applications=num_applications,
#             progress_callback=progress_callback,
#             user_id=message.from_user.id,  # Add user_id
#             data_manager=data_manager      # Add data_manager
#         )

#         # Check for successful applications in database
#         try:
#             successful_apps = data_manager.get_application_count(
#                 user_id=message.from_user.id,
#                 platform='internshala',
#                 status='success'
#             )
#             actual_count = successful_apps or (num_applications * 6)  # Fallback to expected count
#         except:
#             actual_count = num_applications * 6  # Fallback if query fails

#         if not restart_requested:
#             bot.send_message(
#                 chat_id,
#                 "🎉 Amazing news! I've completed all the applications!\n\n"
#                 f"✅ Successfully applied to {actual_count} internships across all categories!\n"
#                 "🌟 You can check all your applications here:\n"
#                 "https://internshala.com/student/applications\n\n"
#                 "Good luck with your applications! 🍀\n\n"
#                 "Is there anything else you'd like me to help you with? 😊",
#                 reply_markup=create_main_keyboard()
#             )

#     except ValueError:
#         if not restart_requested:
#             bot.reply_to(
#                 message, 
#                 "Oops! 😅 That doesn't seem to be a valid number. "
#                 "Could you please enter a number like 5? Let's try again! 🎯"
#             )
#             bot.register_next_step_handler(message, process_internshala_applications, bot)
#     except Exception as e:
#         if not restart_requested:
#             logger.error(f"Error processing internshala applications: {str(e)}")
#             bot.reply_to(
#                 message,
#                 "Sorry, there was an error processing your request. Please try again or click Restart.",
#                 reply_markup=create_main_keyboard()
#             )
#     finally:
#         if driver:
#             try:
#                 driver.quit()
#             except:
#                 pass
#         session_manager.cleanup_user_session(chat_id)

# def ensure_user_initialized(message):
#     """Initialize user and schedule offer check"""
#     try:
#         message_logger.log_incoming_message(message)
#         user_id = message.from_user.id
        
#         # Check if user exists
#         response = supabase.table('users').select('*').eq('user_id', user_id).execute()
        
#         if not response.data:
#             # Register new user
#             user_data = {
#                 'user_id': user_id,
#                 'username': message.from_user.username,
#                 'first_name': message.from_user.first_name,
#                 'last_name': message.from_user.last_name,
#                 'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'last_active': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             }
#             message_logger.log_outgoing_message(
#                 message, {"action": "register_new_user", "user_data": user_data}
#             )
#             data_manager.register_user(user_data)
#         else:
#             message_logger.log_outgoing_message(
#                 message, {"action": "update_user_activity", "user_id": user_id}
#             )
#             # Update existing user activity
#             data_manager.update_user_activity(user_id)
            
#         # Schedule offer check
#         job_id = f'offer_check_{user_id}'
#         try:
#             _scheduler.add_job(
#                 send_offer_check_message,
#                 'interval',
#                 minutes=5,
#                 args=[_bot, user_id],
#                 id=job_id,
#                 replace_existing=True
#             )
#             logger.info(f"Scheduled offer check for user {user_id}")
#             message_logger.log_outgoing_message(
#                 message, {"action": "schedule_offer_check", "job_id": job_id}
#             )
#         except Exception as e:
#             logger.error(f"Error scheduling offer check: {str(e)}")
#             message_logger.log_error(
#                 user_id,
#                 str(e),
#                 {
#                     "handler": "ensure_user_initialized",
#                     "action": "schedule_offer_check",
#                     "error_type": type(e).__name__,
#                 },
#             )
#     except Exception as e:
#         logger.error(f"Error initializing user: {str(e)}")
#         message_logger.log_error(
#             message.from_user.id,
#             str(e),
#             {"handler": "ensure_user_initialized", "error_type": type(e).__name__},
#         )


# def send_offer_check_message(bot, user_id):
#     """Send periodic offer check message with logging"""
#     if session_manager.is_state_locked(user_id):
#         logger.info(f"User {user_id} still needs to respond to previous offer check")
#         return

#     if session_manager.is_user_busy(user_id):
#         logger.info(f"User {user_id} is busy. Rescheduling offer check.")
#         return

#     check_msg = (
#         "👋 Hi there! Just checking in on your job search journey!\n\n"
#         "Have you received any offer letters recently? We're here to help ensure your success "
#         "and protect your interests every step of the way! 🌟\n\n"
#         "Please respond with <b>Yes</b> or <b>No</b> to continue. This helps us provide better support! Remember, we offer:\n"
#         "• Free offer letter review\n"
#         "• Contract term verification\n"
#         "• Protection from potential scams\n\n"
#         "Your success and safety are our top priorities! 💪"
#     )
#     # Create a message-like object for logging
#     class TelegramMessage:
#         def __init__(self, chat_id, message_id):
#             self.chat = type('Chat', (), {'id': chat_id, 'type': 'private'})()
#             self.message_id = message_id
#             self.from_user = type('User', (), {
#                 'id': chat_id,
#                 'username': None,
#                 'first_name': None,
#                 'last_name': None,
#                 'is_bot': False
#             })()

#     # Send message first to get message_id
#     sent_message = bot.send_message(chat_id=user_id, text=check_msg, parse_mode="HTML")
    
#     # Create message object with actual message_id
#     message_obj = TelegramMessage(user_id, sent_message.message_id)

#     # Log the message using the message object
#     message_logger.log_outgoing_message(message_obj, check_msg)
    
#     session_manager.set_state(user_id, "offer_check")
#     logger.info(f"Set state for user {user_id} to offer_check and waiting for response")

#     # Log state change
#     message_logger.log_outgoing_message(
#         message_obj,
#         {"action": "state_change", "new_state": "offer_check"},
#     )

# def handle_offer_response(bot, message):
#     """Handle responses to offer check message with logging"""
#     message_logger.log_incoming_message(message)
#     user_id = message.chat.id
#     user_response = message.text.strip().lower()

#     if session_manager.get_state(user_id) == "offer_check":
#         if user_response == "yes":
#             instructions_msg = (
#                 "🎉 Fantastic news! Congratulations on your offer!\n\n"
#                 "We'd love to help ensure everything is perfect with your offer letter. "
#                 "Our team provides:\n"
#                 "• Comprehensive contract review\n"
#                 "• Salary and benefits analysis\n"
#                 "• Identification of any concerning terms\n\n"
#                 "Please share your offer letter as a PDF file, and we'll make sure everything is secure and fair! 📄\n\n"
#                 "Note: All bot features will remain locked until you send your offer letter or type 'cancel'"
#             )
#             sent_msg = bot.reply_to(message, instructions_msg, parse_mode="HTML")
#             message_logger.log_outgoing_message(message, instructions_msg)
#             session_manager.set_state(user_id, "awaiting_offer_upload")

#         elif user_response == "no":
#             continue_msg = (
#                 "Keep pushing forward! 💪 The right opportunity is just around the corner.\n\n"
#                 "Remember, we're here to support you with:\n"
#                 "• Job search assistance\n"
#                 "• Resume optimization\n"
#                 "• Interview preparation\n\n"
#                 "I'll check back with you in a few days. Meanwhile, don't hesitate to use our services! 🌟"
#             )
#             sent_msg = bot.reply_to(
#                 message,
#                 continue_msg,
#                 parse_mode="HTML",
#                 reply_markup=create_main_keyboard(),
#             )
#             message_logger.log_outgoing_message(message, continue_msg)
#             session_manager.set_state(user_id, None)

#         else:
#             invalid_response_msg = (
#                 "Please respond with either <b>Yes</b> or <b>No</b> to let us know about your offer letters.\n\n"
#                 "This helps us provide the right support for your situation! 🎯"
#             )
#             sent_msg = bot.reply_to(message, invalid_response_msg, parse_mode="HTML")
#             message_logger.log_outgoing_message(message, invalid_response_msg)


# def handle_offer_upload(bot, message):
#     """Handle offer letter document upload"""
#     user_id = message.chat.id
#     current_state = session_manager.get_state(user_id)
    
#     if current_state == "awaiting_offer_upload" and message.document:
#         try:
#             message_logger.log_incoming_message(message)

#             if message.document.mime_type != "application/pdf":
#                 invalid_type_msg = "Please send your offer letter as a PDF file. Other file types are not supported. 📝"
#                 sent_msg = bot.reply_to(message, invalid_type_msg, parse_mode="HTML")
#                 message_logger.log_outgoing_message(message, invalid_type_msg)
#                 return

#             file_info = bot.get_file(message.document.file_id)
#             file_data = bot.download_file(file_info.file_path)
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             file_name = f"offer_letter_{timestamp}.pdf"

#             if data_manager.upload_offer_letter(user_id, file_data, file_name):
#                 success_msg = (
#                     "✅ Thank you! Your offer letter has been securely received and stored.\n\n"
#                     "Our team will review it within 24 hours to ensure:\n"
#                     "• All terms are fair and standard\n"
#                     "• No concerning clauses are present\n"
#                     "• Your interests are protected\n\n"
#                     "We'll notify you once the review is complete! 🚀"
#                 )
#                 sent_msg = bot.reply_to(message, success_msg, parse_mode="HTML")
#                 message_logger.log_outgoing_message(message, success_msg)
#             else:
#                 error_msg = (
#                     "😟 There was an issue storing your offer letter securely.\n"
#                     "Please try again or contact our support team for assistance.\n"
#                     "We want to ensure your document is handled with the utmost security!"
#                 )
#                 sent_msg = bot.reply_to(message, error_msg, parse_mode="HTML")
#                 message_logger.log_error(
#                     user_id,
#                     "Failed to store offer letter",
#                     {"handler": "handle_offer_upload", "error_type": "StorageError"},
#                 )

#             session_manager.set_state(user_id, None)

#         except Exception as e:
#             logger.error(f"Error handling offer letter: {str(e)}")
#             error_msg = (
#                 "🔄 Something went wrong while processing your offer letter.\n"
#                 "Please try again or contact our support team if the issue persists."
#             )
#             sent_msg = bot.reply_to(message, error_msg, parse_mode="HTML")
#             message_logger.log_error(
#                 user_id,
#                 str(e),
#                 {"handler": "handle_offer_upload", "error_type": type(e).__name__},
#             )
#             session_manager.set_state(user_id, None)
            
#     elif message.document and message.document.mime_type == "application/pdf":
#         wrong_time_msg = (
#             "I see you're trying to send a document! If this is your offer letter, "
#             "please use the offer letter review feature when prompted. "
#             "I want to make sure it's properly tracked and reviewed! 😊"
#         )
#         sent_msg = bot.reply_to(message, wrong_time_msg, parse_mode="HTML")
#         message_logger.log_outgoing_message(message, wrong_time_msg)

# def create_locked_handler(original_handler):
#     """Decorator to lock handlers during offer check"""
#     def wrapped_handler(message):
#         current_state = session_manager.get_state(message.chat.id)
#         if current_state == "offer_check":
#             _bot.reply_to(
#                 message,
#                 "📌 I noticed you have a pending response.\n\n"
#                 "Please respond to the previous question with <b>Yes</b> or <b>No</b> first, "
#                 "so I can better assist you with your job search journey!\n\n"
#                 "Once you respond, you'll be able to use all features again. 😊",
#                 parse_mode='HTML'
#             )
#             return
#         elif current_state == "awaiting_offer_upload":
#             _bot.reply_to(
#                 message,
#                 "📤 I'm waiting for your offer letter.\n\n"
#                 "Please either:\n"
#                 "• Send your offer letter as a PDF\n"
#                 "• Or type 'cancel' to skip this step\n\n"
#                 "This helps us ensure your job search security! 🔐",
#                 parse_mode='HTML'
#             )
#             return
#         original_handler(message)
#     return wrapped_handler





import tempfile
import os
import logging
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from linkedin_jobs import (
    setup_driver,
    login_to_linkedin,
    search_jobs,
    apply_to_jobs,
    get_user_name,
)
from resume_generator import generate_resume
from linkedin_improver import improve_linkedin_profile
from internshala_automation import run_internshala_automation
from data_manager import DataManager
from supabase import create_client
from typing import Optional
from dotenv import load_dotenv
from session_manager import session_manager  # Import the session manager
from message import message_logger

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize DataManager
data_manager = DataManager()

# Initialize Supabase with environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing Supabase configuration. Check your .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bot instance
_bot = None
_scheduler = None


def initialize_bot(bot, scheduler):
    """Initialize bot and scheduler instances"""
    global _bot, _scheduler
    _bot = bot
    _scheduler = scheduler
    logger.info("Bot initialized for handlers")


def create_main_keyboard():
    """Create main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Job Auto Apply'))  # Combined button
    keyboard.add(KeyboardButton('Improve Resume/CV'), KeyboardButton('Improve LinkedIn Profile'))
    keyboard.add(KeyboardButton('Restart'))  # Keeping Restart button
    return keyboard

def create_verification_keyboard():
    """Create keyboard for unverified users"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('✨ Need Help?'), KeyboardButton('🔄 Start Over'))
    return keyboard

def handle_job_auto_apply(bot, message):
    """Handle job auto apply request"""
    try:
        user_id = message.from_user.id
        session_manager.set_state(user_id, 'waiting_for_platform_selection')
        
        # Create custom keyboard with platform buttons
        platform_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        platform_keyboard.add(KeyboardButton('LinkedIn - Full-time Jobs'))  # First button
        platform_keyboard.add(KeyboardButton('Internshala - Internships'))  # Second button
        platform_keyboard.add(KeyboardButton('Restart'))  # Keep restart button
        
        platform_msg = (
            "🚀 Choose your target platform:\n\n"
            "1️⃣ LinkedIn - Full-time Jobs\n"
            "   • Professional roles\n"
            "   • Full-time positions\n"
            "   • Global opportunities\n\n"
            "2️⃣ Internshala - Internships\n"
            "   • Internship positions\n"
            "   • Work from home options\n"
            "   • Student-friendly roles\n\n"
            "Select a platform using the buttons below! 🎯"
        )
        
        bot.reply_to(message, platform_msg, reply_markup=platform_keyboard)
        bot.register_next_step_handler(message, process_platform_selection, bot)
        
    except Exception as e:
        logger.error(f"Error in handle_job_auto_apply: {str(e)}")
        session_manager.set_state(message.from_user.id, None)
        bot.reply_to(
            message, 
            "Sorry, there was an error. Please try again or click Restart.",
            reply_markup=create_main_keyboard()
        )

def process_platform_selection(message, bot):
    """Process platform selection from buttons"""
    if message.text and message.text.lower() == 'restart':
        handle_restart(message, bot)
        return
        
    try:
        selection = message.text.lower()
        if "linkedin" in selection:
            # User clicked LinkedIn button
            handle_apply_jobs(bot, message)
        elif "internshala" in selection:
            # User clicked Internshala button
            handle_apply_internships(bot, message)
        else:
            # Invalid selection - show buttons again
            platform_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            platform_keyboard.add(KeyboardButton('LinkedIn - Full-time Jobs'))
            platform_keyboard.add(KeyboardButton('Internshala - Internships'))
            platform_keyboard.add(KeyboardButton('Restart'))
            
            bot.reply_to(
                message,
                "Please select either LinkedIn or Internshala using the buttons provided.",
                reply_markup=platform_keyboard
            )
            bot.register_next_step_handler(message, process_platform_selection, bot)
            
    except Exception as e:
        logger.error(f"Error in process_platform_selection: {str(e)}")
        bot.reply_to(
            message, 
            "Sorry, there was an error. Please try again or click Restart.",
            reply_markup=create_main_keyboard()
        )

def check_unverified_user(bot, message, user_data):
    """
    Check if user exists in users table without accelerator_user_id and handle verification
    Returns True if verification is needed, False otherwise
    """
    try:
        user_id = message.from_user.id
        # Query users table for this telegram user
        response = data_manager.get_user_by_telegram_id(user_id)
        
        if not response or not response.get("accelerator_user_id"):
            # User needs verification
            verification_msg = (
                "✨ Hi there! I'm Hannah, your AI career guide! ✨\n\n"
                "I noticed you've used our bot before - let's quickly verify your account "
                "so we can start your amazing career journey! 🚀\n\n"
                "🔑 Got your access key? Amazing! Just share it with me!\n\n"
                "🌟 Need an access key? Super easy:\n"
                "• Visit: https://get-a-job.persistventures.com/\n"
                "• Connect your LinkedIn profile\n"
                "• Follow the simple steps\n"
                "• Check your email for your special key\n\n"
                "💫 Already registered? Grab your key here:\n"
                "https://get-a-job.persistventures.com/career-accelerator/login\n\n"
                "🎯 Questions? Click 'Need Help?' below and I'm here for you! 💫"
            )
            bot.reply_to(message, verification_msg, reply_markup=create_verification_keyboard())
            session_manager.set_state(user_id, "waiting_for_access_key")
            return True  # Indicate that verification is needed

        return False  # User is verified, continue with normal processing

    except Exception as e:
        logger.error(f"Error in check_unverified_user: {str(e)}")
        return True  # Assume verification is needed if an error occurs

def verify_user_access(user_id: int) -> tuple[bool, str, dict]:
    """
    Verify user's access and return status
    Returns: (is_verified, message, user_data)
    """
    try:
        # First check if user exists in accelerator_users
        acc_user = data_manager.get_user_by_telegram_id(user_id)

        if not acc_user:
            # Check if user exists in users table
            response = (
                supabase.table("users").select("*").eq("user_id", user_id).execute()
            )

            if response.data and len(response.data) > 0:
                return False, "needs_verification", {}
            else:
                return False, "new_user", {}

        # User exists in accelerator_users, verify access
        access_key = acc_user.get("access_key")
        if not access_key:
            return False, "needs_new_key", {}

        # Verify the access key is still valid
        is_valid, user_data = data_manager.verify_access_key(access_key)
        if not is_valid:
            return False, "expired_key", {}

        return True, "verified", user_data

    except Exception as e:
        logger.error(f"Error in verify_user_access: {str(e)}")
        return False, "error", {}


def process_access_key(message, bot):
    """
    Process the access key provided by the user and verify their account
    """
    try:
        message_logger.log_incoming_message(message)
        
        # Handle restart command
        if message.text and message.text.lower() == "restart":
            handle_restart(message, bot)
            return

        user_id = message.from_user.id
        access_key = message.text.strip()

        # First create/update the user record in users table
        telegram_data = {
            "user_id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "registration_date": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
        }

        # Only update registration_date if it's a new user
        existing_user = (
            supabase.table("users").select("*").eq("user_id", user_id).execute()
        )

        if not existing_user.data:
            telegram_data["registration_date"] = datetime.now().isoformat()

        data_manager.register_user(telegram_data)

        # Then verify the access key
        is_valid, user_data = data_manager.verify_access_key(access_key)

        if not is_valid:
            error_msg = (
                "❌ I couldn't verify your access key. Please check that:\n"
                "1. You've copied the complete key correctly\n"
                "2. You've signed the contract (for new users)\n"
                "3. Your account is fully verified\n\n"
                "Need a new access key?\n"
                "• New users: https://get-a-job.persistventures.com/\n"
                "• Existing users: https://get-a-job.persistventures.com/career-accelerator/login\n\n"
                "Please try again with a valid access key! 🔑"
            )
            message_logger.log_outgoing_message(message, error_msg)
            bot.reply_to(message, error_msg)
            session_manager.set_state(user_id, "waiting_for_access_key")
            bot.register_next_step_handler(message, process_access_key, bot)
            return

        # If valid, link telegram user to accelerator user
        if data_manager.link_telegram_user(access_key, telegram_data):
            keyboard = create_main_keyboard()
            success_msg = (
                f"🎉 Perfect! Your access key has been verified.\n\n"
                f"Welcome to Persist Ventures Career Accelerator, {user_data.get('full_name', 'there')}! "
                f"I'm excited to help you achieve your career goals!\n\n"
                f"Here's what I can help you with:\n"
                f"• Automated job applications on LinkedIn\n"
                f"• AI-powered resume enhancement\n"
                f"• LinkedIn profile optimization\n"
                f"• Internship applications\n"
                f"• Offer letter review & verification\n\n"
                f"What would you like to do first? Choose an option below! 👇"
            )
            message_logger.log_outgoing_message(message, success_msg)
            bot.reply_to(message, success_msg, reply_markup=keyboard)
            session_manager.set_state(user_id, "main_menu")
        else:
            error_msg = (
                "❌ I wasn't able to set up your account properly. "
                "Please try again or contact our support team.\n\n"
                "You can get help at: team@persistventures.com"
            )
            message_logger.log_outgoing_message(message, error_msg)
            bot.reply_to(message, error_msg)
            session_manager.set_state(user_id, "waiting_for_access_key")
            bot.register_next_step_handler(message, process_access_key, bot)

    except Exception as e:
        logger.error(f"Error in process_access_key: {str(e)}")
        error_msg = (
            "Sorry, I encountered an error while processing your access key. "
            "Please try again or contact our support team at team@persistventures.com"
        )
        message_logger.log_error(
            message.from_user.id,
            error_msg,
            {"handler": "process_access_key", "error_type": type(e).__name__},
        )
        bot.reply_to(message, error_msg)
        session_manager.set_state(message.from_user.id, "waiting_for_access_key")
        bot.register_next_step_handler(message, process_access_key, bot)

def handle_start(bot, message):
    """
    Handle the /start command - First entry point for users
    """
    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id

        # Check if user is verified
        accelerator_user = data_manager.get_user_by_telegram_id(user_id)

        if accelerator_user and accelerator_user.get("telegram_user_id"):
            # User is verified, show main menu
            keyboard = create_main_keyboard()
            welcome_back_msg = (
                f"Welcome back to Persist Ventures Career Accelerator! 🎉\n\n"
                f"Hi {accelerator_user.get('full_name', 'there')}! I'm Hannah, "
                f"your AI career assistant. Let's continue your journey to success! 🚀\n\n"
                f"What would you like to do today?"
            )
            message_logger.log_outgoing_message(message, welcome_back_msg)
            bot.reply_to(message, welcome_back_msg, reply_markup=keyboard)
            session_manager.set_state(user_id, "main_menu")
        else:
            # User is not verified, prompt for access key
            welcome_msg = (
                "👋 Hello! I'm Hannah, your AI-powered career guide at Persist Ventures! 🌟\n\n"
                "I'm here to help you find amazing job opportunities and accelerate your career growth! "
                "To get started, I'll need your access key.\n\n"
                "🔑 Here's how to get your access key:\n\n"
                "🆕 For New Users:\n"
                "1. Visit: https://get-a-job.persistventures.com/\n"
                "2. Sign up with your LinkedIn profile\n"
                "3. Complete our AI-powered verification process\n"
                "4. Sign the contract\n"
                "5. Check your email for the access key\n\n"
                "🔄 For Existing Users:\n"
                "1. Login at: https://get-a-job.persistventures.com/career-accelerator/login\n"
                "2. You'll receive an email with your access key\n\n"
                "Once you have your access key, please share it with me to begin! 🚀"
            )
            message_logger.log_outgoing_message(message, welcome_msg)
            bot.reply_to(message, welcome_msg)
            session_manager.set_state(user_id, "waiting_for_access_key")
            bot.register_next_step_handler(message, process_access_key, bot)

    except Exception as e:
        logger.error(f"Error in handle_start: {str(e)}")
        error_msg = (
            "I apologize, but I encountered an error while starting up. "
            "Please try again or contact our support team at team@persistventures.com "
            "if the issue persists."
        )
        message_logger.log_error(
            message.from_user.id,
            error_msg,
            {"handler": "handle_start", "error_type": type(e).__name__},
        )
        bot.reply_to(message, error_msg)


def handle_restart(message, bot):
    chat_id = message.chat.id
    current_state = session_manager.get_state(chat_id)

    logger.info(f"Handling restart for user {chat_id} from state: {current_state}")

    try:
        message_logger.log_incoming_message(message)
        # Don't interrupt offer check states
        if session_manager.is_state_locked(chat_id):
            reply_to_offer_check_msg = (
                "📌 Please respond to the offer check first.\n"
                "This helps us ensure your job search security!\n"
                "Once you respond, you can access all features again."
            )
            message_logger.log_outgoing_message(message, reply_to_offer_check_msg)
            bot.reply_to(message, reply_to_offer_check_msg, parse_mode="HTML")
            return

        # First verify user access
        is_verified, status, user_data = verify_user_access(chat_id)

        # Handle different verification scenarios
        if not is_verified:
            if status == "error":
                error_msg = "❌ Sorry, there was an error verifying your access. Please try again later or contact support."
                message_logger.log_outgoing_message(message, error_msg)
                bot.reply_to(message, error_msg, parse_mode="HTML")
                return

            elif status in ["needs_verification", "new_user"]:
                verification_msg = (
                    "👋 Welcome to Persist Ventures Career Accelerator!\n\n"
                    "🔐 To access all features, please verify your account:\n\n"
                    "1️⃣ If you have an access key, please share it with me now.\n\n"
                    "2️⃣ If you don't have an access key, you can get one by:\n"
                    "   • Visiting: https://get-a-job.persistventures.com/\n"
                    "   • Signing up with your LinkedIn profile\n"
                    "   • Completing the verification process\n"
                    "   • Signing the contract\n"
                    "   • Checking your email for the access key\n\n"
                    "🔄 Already registered? Get your access key at:\n"
                    "https://get-a-job.persistventures.com/career-accelerator/login\n\n"
                    "Please share your access key when ready! 🚀"
                )
                message_logger.log_outgoing_message(message, verification_msg)
                bot.reply_to(message, verification_msg)
                session_manager.set_state(chat_id, "waiting_for_access_key")
                bot.register_next_step_handler(message, process_access_key, bot)
                return

            elif status in ["needs_new_key", "expired_key"]:
                expired_msg = (
                    "🔑 Your access key has expired or is invalid.\n\n"
                    "To continue using our services, please get a new access key:\n"
                    "1. Visit: https://get-a-job.persistventures.com/career-accelerator/login\n"
                    "2. Login with your account\n"
                    "3. You'll receive a new access key via email\n\n"
                    "Once you have your new access key, please share it with me! 🌟"
                )
                message_logger.log_outgoing_message(message, expired_msg)
                bot.reply_to(message, expired_msg)
                session_manager.set_state(chat_id, "waiting_for_access_key")
                bot.register_next_step_handler(message, process_access_key, bot)
                return

        # Clean up session
        session_manager.cleanup_user_session(chat_id)

        # Get user's name for personalized message
        user_name = user_data.get("full_name", "there")

        # Send restart confirmation
        restart_msg = (
            f"🔄 Welcome back, {user_name}!\n\n"
            "I've reset everything and we're ready to start fresh. "
            "All previous operations have been cancelled.\n\n"
            "What would you like to do? 😊"
        )

        message_logger.log_outgoing_message(message, restart_msg)

        bot.reply_to(message, restart_msg, reply_markup=create_main_keyboard())

        logger.info(f"Successfully restarted bot for verified user {chat_id}")

    except Exception as e:
        logger.error(f"Error during restart for user {chat_id}: {str(e)}")
        error_msg = (
            "❌ There was an error restarting the bot, but all processes have been stopped.\n"
            "Please try your operation again."
        )
        message_logger.log_error(message.from_user.id, str(e), {
            'handler': 'handle_restart',
            'error_type': type(e).__name__,
            'state': session_manager.get_state(chat_id)
        })
        bot.reply_to(message, error_msg, reply_markup=create_main_keyboard())


def handle_apply_jobs(bot, message):
    """Handle job application request with message logging"""
    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id
        session_manager.set_state(user_id, "waiting_for_linkedin_cookie")

        apply_jobs_msg = (
            "🎯 Awesome! You're one step closer to your new career opportunity!\n\n"
            "💼 To proceed with your application, I'll need your LinkedIn 'li_at' cookie value.\n\n"
            "❓ Not sure how to find it?\n"
            "📹 Watch this quick guide:\n"
            "https://www.loom.com/share/aa9850210ff24a25afc949f637e01254?sid=245233a2-2140-4839-9a51-bd5d370d3573\n\n"
            "✍️ Provide me the cookies once you have it, and we'll continue from there!\n\n"
            "💡 Tip: Click 'restart' anytime to return to the main menu! 🔄"
        )

        message_logger.log_outgoing_message(message, apply_jobs_msg)
        bot.reply_to(message, apply_jobs_msg)
        bot.register_next_step_handler(message, process_li_at, bot)

    except Exception as e:
        logger.error(f"Error in handle_apply_jobs: {str(e)}")
        error_msg = "Sorry, there was an error. Please try again or click Restart."
        message_logger.log_error(message.from_user.id, str(e), {
            'handler': 'handle_apply_jobs',
            'error_type': type(e).__name__,
            'state': session_manager.get_state(user_id)
        })
        session_manager.set_state(message.from_user.id, None)
        bot.reply_to(message, error_msg)


def process_li_at(message, bot):
    """Process LinkedIn cookie input"""
    if message.text and message.text.lower() == "restart":
        message_logger.log_incoming_message(message)
        handle_restart(message, bot)
        return

    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id
        session_manager.set_state(user_id, "waiting_for_linkedin_cookie")

        li_at = message.text.strip()
        data_manager.update_linkedin_cookie(user_id, li_at)
        message_logger.log_outgoing_message(message, {'action': 'update_linkedin_cookie'})

        driver = setup_driver()
        try:
            session_manager.store_driver(user_id, driver, "linkedin")
            login_success = login_to_linkedin(driver, li_at)

            if login_success:
                user_name = get_user_name(driver)
                session_manager.set_state(user_id, "waiting_for_job_keyword")
                session_manager.store_data(
                    user_id, "li_at", li_at
                )  # Store for later use

                greeting = (
                    f"Hi {user_name}! 👋 Thanks so much for logging in successfully! 🎉\n\n"
                    "I'm excited to help you find the perfect job! ✨\n"
                    "What kind of position are you looking for today? 💼\n"
                    "Just enter a keyword (e.g., 'Python Developer' 👩‍💻) "
                    "and we'll get started on your search! 🚀\n\n"
                    "Remember, you can click 'restart' Button anytime to return to the main menu! 🔄"
                )
                message_logger.log_outgoing_message(message, greeting)
                bot.reply_to(message, greeting)
                bot.register_next_step_handler(
                    message, lambda m: handle_job_search(m, driver, bot)
                )
            else:
                session_manager.cleanup_user_session(user_id)
                error_msg = (
                    "⚠️ Login failed! 🚫\n\n"
                    "Please check your LinkedIn cookie and try again. 🔍\n"
                    "Make sure you've copied the correct 'li_at' value. ✅\n\n"
                    "You can click 'Restart' to try again! 🔄"
                )
                message_logger.log_outgoing_message(message, error_msg)
                bot.reply_to(message, error_msg)
        except Exception as e:
            session_manager.cleanup_user_session(user_id)
            logger.error(f"Error in LinkedIn login: {str(e)}")
            error_msg = (
                f"Oh no! 😟 It looks like there was an issue logging you in.\n\n"
                f"❌ Error: {str(e)}\n\n"
                "Please check your cookie and try again by clicking 'Restart' 🔄"
            )
            message_logger.log_error(user_id, str(e), {
                'handler': 'process_li_at',
                'action': 'linkedin_login',
                'error_type': type(e).__name__
            })
            bot.reply_to(message, error_msg)
    except Exception as e:
        logger.error(f"Error in process_li_at: {str(e)}")
        session_manager.cleanup_user_session(message.from_user.id)
        error_msg = (
            "❌ Sorry, there was an error processing your LinkedIn cookie. 😕\n"
            "Please try again by clicking 'Restart' 🔄"
        )
        message_logger.log_error(user_id, str(e), {
            'handler': 'process_li_at',
            'error_type': type(e).__name__,
            'state': session_manager.get_state(user_id)
        })
        bot.reply_to(message, error_msg)


def handle_job_search(message, driver, bot):
    """Handle job search process"""
    user_id = message.from_user.id

    if message.text and message.text.lower() == "restart":
        message_logger.log_incoming_message(message)
        handle_restart(message, bot)
        session_manager.cleanup_user_session(user_id)
        return

    try:
        message_logger.log_incoming_message(message)
        session_manager.set_state(user_id, "applying_to_jobs")
        session_manager.store_data(user_id, "search_keyword", message.text.strip())

        keyword = message.text.strip()
        searching_jobs_msg = (
            f"Great choice! I'm on it—searching for '{keyword}' jobs with the Easy Apply filter. "
            "This might take a moment, but I'll find the best opportunities for you! 😊 Please hold tight!"
        )
        message_logger.log_outgoing_message(message, searching_jobs_msg)
        bot.reply_to(message, searching_jobs_msg)

        job_listings = search_jobs(driver, keyword)
        if not job_listings:
            session_manager.set_state(user_id, None)
            error_msg = (
                "Oh no! I couldn't find any job listings. 😟 Let's try again—please restart the bot to start the process. "
                "I'm here to help you find the perfect job! 💪"
            )
            message_logger.log_outgoing_message(message, error_msg)
            bot.reply_to(message, error_msg)
            session_manager.set_state(user_id, None)
            return

        jobs_found_msg = (
            f"Great news! 🎉 I found {len(job_listings)} job listings for you. "
            "I'm starting to apply to them right now! 😊 Sit tight, and I'll keep you updated on the progress..."
        )
        message_logger.log_outgoing_message(message, jobs_found_msg)
        bot.reply_to(message, jobs_found_msg)

        applied_count = apply_to_jobs(driver, job_listings, bot, message)

        if applied_count == 0:
            error_msg = (
                "Oh no! 😟 I wasn't able to successfully apply to any of the job listings. "
                "Please restart the bot to start the application process again. "
                "I'm here to help you every step of the way! 💪"
            )
            message_logger.log_outgoing_message(message, error_msg)
            bot.reply_to(message, error_msg)
        else:
            success_msg = (
                f"✅ Great! I successfully applied to {applied_count} jobs for you. 🎉 "
                "If you'd like to apply to more jobs with a different keyword, "
                "please restart the bot to start the process again. I'm here to help! 😊"
            )
            message_logger.log_outgoing_message(message, success_msg)
            bot.reply_to(
                message, success_msg
            )
    except Exception as e:
        logger.error(f"Error in job search/application: {str(e)}")
        error_msg = (
            "Oh no! 😟 Something went wrong during the job search and application process. "
            "Please restart the bot to try again. I'm here to help you every step of the way! 💪"
        )
        message_logger.log_error(user_id, str(e), {
            'handler': 'handle_job_search',
            'error_type': type(e).__name__,
            'state': session_manager.get_state(user_id)
        })
        bot.reply_to(message, error_msg)
    finally:
        session_manager.cleanup_user_session(user_id)
        back_menu_msg = "We're back to the main menu! 😊 Please choose one of the options below to continue:"
        message_logger.log_outgoing_message(message, back_menu_msg)
        # Return to main menu
        bot.reply_to(
            message,
            back_menu_msg,
            reply_markup=create_main_keyboard(),
        )


def handle_improve_resume(bot, message):
    """Handle resume improvement request with logging"""
    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id

        if session_manager.is_state_locked(user_id):
            locked_msg = "Please complete the current operation first."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        session_manager.set_state(user_id, "waiting_for_resume")

        instructions_msg = (
            "🎯 Sure thing!\n\n"
            "📄 Please send me your current resume as a PDF file, and I'll help you create an enhanced version using AI.\n\n"
            "🚀 Let's get started!\n\n"
            "💡 You can click 'restart' Button anytime to return to the main menu! 🔄"
        )
        message_logger.log_outgoing_message(
            message, instructions_msg, {"state": "waiting_for_resume", "type": "text"}
        )
        bot.reply_to(message, instructions_msg)
        bot.register_next_step_handler(message, process_resume, bot)

    except Exception as e:
        error_msg = "Sorry, there was an error. Please try again or click Restart."
        message_logger.log_error(
            message.from_user.id,
            str(e),
            {
                "handler": "handle_improve_resume",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        session_manager.set_state(message.from_user.id, None)
        bot.reply_to(message, error_msg)


def process_resume(message, bot):
    """Process resume PDF upload with comprehensive message logging"""
    if message.text and message.text.lower() == "restart":
        message_logger.log_incoming_message(message)
        handle_restart(message, bot)
        return

    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id

        if session_manager.is_state_locked(user_id):
            locked_msg = "Session is locked. Please complete the current operation."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        session_manager.set_state(user_id, "processing_resume")
        temp_file_path = None

        if message.document and message.document.mime_type == "application/pdf":
            try:
                message_logger.log_incoming_message(message)
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as temp_file:
                    temp_file.write(downloaded_file)
                    temp_file_path = temp_file.name

                received_msg = (
                    "Great! 😊 I've received your resume and I'm processing it now. 🚀"
                )
                message_logger.log_outgoing_message(message, received_msg)
                bot.reply_to(message, received_msg)

                processing_msg = "Processing resume with AI enhancement..."
                message_logger.log_outgoing_message(message, processing_msg)

                with open(temp_file_path, "rb") as resume_file:
                    api_response = generate_resume(resume_file)

                if isinstance(api_response, str) and os.path.exists(api_response):
                    with open(api_response, "rb") as improved_resume:
                        success_msg = "Here's your improved resume! 🎉"
                        message_logger.log_outgoing_message(
                            message,
                            {
                                "text": success_msg,
                                "document": {
                                    "file_path": api_response,
                                    "mime_type": "application/pdf",
                                },
                            },
                            response_type="document",
                        )
                        bot.send_document(
                            message.chat.id, improved_resume, caption=success_msg
                        )
                    os.remove(api_response)
                else:
                    error_message = (
                        str(api_response)[:3997] + "..."
                        if len(str(api_response)) > 4000
                        else str(api_response)
                    )
                    message_logger.log_error(
                        user_id,
                        f"API Error: {error_message}",
                        {"handler": "process_resume", "error_type": "APIError"},
                    )
                    bot.reply_to(message, f"API Error: {error_message}")

            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception as e:
                        logger.error(f"Error deleting temporary file: {str(e)}")
                        message_logger.log_error(
                            user_id,
                            str(e),
                            {"handler": "process_resume", "error_type": "FileError"},
                        )
                session_manager.set_state(user_id, None)

        else:
            invalid_msg = "Please send your resume as a PDF file."
            message_logger.log_outgoing_message(message, invalid_msg)
            bot.reply_to(message, invalid_msg)
            session_manager.set_state(user_id, "waiting_for_resume")
            bot.register_next_step_handler(message, process_resume, bot)
            return

        menu_msg = "Returning to main menu:"
        message_logger.log_outgoing_message(message, menu_msg)
        bot.reply_to(message, menu_msg, reply_markup=create_main_keyboard())

    except Exception as e:
        logger.error(f"Error in process_resume: {str(e)}")
        error_msg = "Error processing resume. Please try again."
        message_logger.log_error(
            user_id,
            str(e),
            {
                "handler": "process_resume",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        session_manager.set_state(message.from_user.id, None)
        bot.reply_to(message, error_msg)
        bot.reply_to(
            message, "Returning to main menu", reply_markup=create_main_keyboard()
        )


def handle_improve_linkedin(bot, message):
    """Handle LinkedIn profile improvement request with logging"""
    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id

        if session_manager.is_state_locked(user_id):
            locked_msg = "Please complete the current operation first."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        session_manager.set_state(user_id, "waiting_for_linkedin_profile")

        instructions_msg = (
            "Let's improve your LinkedIn profile! 🚀\n\n"
            "First, I'll need your LinkedIn 'li_at' cookie. If you're not sure how to get it, "
            "check out this guide: https://www.loom.com/share/aa9850210ff24a25afc949f637e01254\n\n"
            "Please paste your li_at cookie here.\n\n"
            "You can click 'restart' Button anytime to return to the main menu! 🔄"
        )
        message_logger.log_outgoing_message(message, instructions_msg)
        bot.reply_to(message, instructions_msg)
        bot.register_next_step_handler(message, process_linkedin_cookie, bot)

    except Exception as e:
        error_msg = "Sorry, there was an error. Please try again or click Restart."
        message_logger.log_error(
            message.from_user.id,
            str(e),
            {
                "handler": "handle_improve_linkedin",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        session_manager.set_state(message.from_user.id, None)
        logger.error(f"Error in handle_improve_linkedin: {str(e)}")
        bot.reply_to(message, error_msg)


def process_linkedin_cookie(message, bot):
    """Process LinkedIn cookie for profile improvement"""
    if message.text and message.text.lower() == "restart":
        message_logger.log_incoming_message(message)
        handle_restart(message, bot)
        return

    try:
        message_logger.log_incoming_message(message)
        user_id = message.chat.id

        if session_manager.is_state_locked(user_id):
            locked_msg = "Please complete the current operation first."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        cookie_data = message.text.strip()
        session_manager.store_data(user_id, "li_at", cookie_data)

        next_steps_msg = (
            "Great! Now, please share your LinkedIn profile URL "
            "(e.g., https://www.linkedin.com/in/username)\n\n"
            "You can click 'restart' Button anytime to return to the main menu! 🔄"
        )
        message_logger.log_outgoing_message(message, next_steps_msg)
        bot.reply_to(message, next_steps_msg)
        bot.register_next_step_handler(message, process_linkedin_url, bot)

    except Exception as e:
        logger.error(f"Error in process_linkedin_cookie: {str(e)}")
        error_msg = "Sorry, there was an error. Please try again or click Restart."
        message_logger.log_error(
            user_id,
            str(e),
            {
                "handler": "process_linkedin_cookie",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        bot.reply_to(message, error_msg)


def process_linkedin_url(message, bot):
    """Process LinkedIn profile URL with message logging"""
    if message.text and message.text.lower() == "restart":
        message_logger.log_incoming_message(message)
        handle_restart(message, bot)
        return

    try:
        message_logger.log_incoming_message(message)
        user_id = message.chat.id

        if session_manager.is_state_locked(user_id):
            locked_msg = "Please complete the current operation first."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        profile_url = message.text.strip()

        if not profile_url.startswith("https://www.linkedin.com/in/"):
            invalid_url_msg = (
                "Please provide a valid LinkedIn profile URL starting with 'https://www.linkedin.com/in/'\n"
                "Try again or click 'restart' to return to main menu."
            )
            message_logger.log_outgoing_message(message, invalid_url_msg)
            bot.reply_to(message, invalid_url_msg)
            bot.register_next_step_handler(message, process_linkedin_url, bot)
            return

        processing_msg = "Processing your LinkedIn profile... Please wait! 🔄"
        message_logger.log_outgoing_message(message, processing_msg)
        bot.reply_to(message, processing_msg)

        li_at = session_manager.get_data(user_id, "li_at")
        result = improve_linkedin_profile(profile_url, li_at)

        if result["success"]:
            success_msg = (
                f"✅ Success! Here are your profile improvement suggestions:\n\n"
                f"{result['message']}\n\n"
                "Would you like to improve anything else? Choose an option from the menu below:"
            )
            message_logger.log_outgoing_message(message, success_msg)
            bot.reply_to(message, success_msg, reply_markup=create_main_keyboard())
        else:
            error_msg = (
                f"❌ Sorry, there was an error: {result['message']}\n"
                "Please try again or choose another option:"
            )
            message_logger.log_outgoing_message(message, error_msg)
            bot.reply_to(message, error_msg, reply_markup=create_main_keyboard())

    except Exception as e:
        logger.error(f"Error in process_linkedin_url: {str(e)}")
        error_msg = "Sorry, there was an error processing your LinkedIn profile. Please try again."
        message_logger.log_error(
            user_id,
            str(e),
            {
                "handler": "process_linkedin_url",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        session_manager.cleanup_user_session(user_id)
        bot.reply_to(message, error_msg, reply_markup=create_main_keyboard())


def handle_apply_internships(bot, message):
    """Handle internship application request with logging"""
    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id
        session_manager.set_state(user_id, "internshala_cookie")

        instructions_msg = (
            "Fantastic choice! 🌟 Let's help you land an amazing internship opportunity! \n\n"
            "First, I'll need your Internshala cookie to help you apply. Here's how to get it: \n"
            "1. Log in to Internshala in your web browser 🌐\n"
            "2. Open developer tools (F12 or right-click > Inspect) 🔍\n"
            "3. Click on 'Application' or 'Storage' tab 📑\n"
            "4. Look for 'Cookies' and find the value for 'PHPSESSID' 🍪\n\n"
            "Once you have it, just paste it here and we'll get started on your applications! 😊\n\n"
            "Remember, You can click 'restart' Button anytime to return to the main menu! 🔄"
        )
        message_logger.log_outgoing_message(message, instructions_msg)
        bot.reply_to(message, instructions_msg)
        bot.register_next_step_handler(message, process_phpsessid, bot)

    except Exception as e:
        logger.error(f"Error in handle_apply_internships: {str(e)}")
        error_msg = "Sorry, there was an error. Please try again or click Restart."
        message_logger.log_error(
            message.from_user.id,
            str(e),
            {
                "handler": "handle_apply_internships",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        session_manager.set_state(message.from_user.id, None)
        bot.reply_to(message, error_msg)


def process_phpsessid(message, bot):
    """Process Internshala PHPSESSID cookie with logging"""
    if message.text and message.text.lower() == "restart":
        message_logger.log_incoming_message(message)
        handle_restart(message, bot)
        return

    try:
        message_logger.log_incoming_message(message)
        user_id = message.chat.id

        if session_manager.is_state_locked(user_id):
            locked_msg = "Please complete the current operation first."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        session_manager.set_state(user_id, "processing_internshala")
        session_manager.store_data(user_id, "phpsessid", message.text.strip())

        instructions_msg = (
            "Perfect! Thanks for that! 🎉\n\n"
            "Now, I can help you apply to various exciting internship roles! 🚀\n"
            "I can apply for these amazing opportunities:\n"
            "📊 Data Science\n"
            "💻 Software Development\n"
            "🌐 Web Development\n"
            "📈 Data Analytics\n"
            "🐍 Python Django\n"
            "📊 Business Analytics\n\n"
            "How many applications would you like me to submit for each role? "
            "(For example, if you choose 5, I'll apply to 5 internships in each category, "
            "making it 30 total applications!) ✨\n\n"
            "Please enter a number (I recommend starting with 5! 😊)\n\n"
            "Remember, You can click 'restart' Button anytime to return to the main menu! 🔄"
        )
        message_logger.log_outgoing_message(message, instructions_msg)
        bot.reply_to(message, instructions_msg)
        bot.register_next_step_handler(message, process_internshala_applications, bot)

    except Exception as e:
        logger.error(f"Error in process_phpsessid: {str(e)}")
        error_msg = "Sorry, there was an error. Please try again or click Restart."
        message_logger.log_error(
            message.from_user.id,
            str(e),
            {
                "handler": "process_phpsessid",
                "error_type": type(e).__name__,
                "state": session_manager.get_state(user_id),
            },
        )
        session_manager.set_state(message.from_user.id, None)
        bot.reply_to(message, error_msg)


def process_internshala_applications(message, bot):
    """Process Internshala applications with job tracking and logging"""
    chat_id = message.chat.id
    driver = None
    restart_requested = message.text and message.text.lower() == "restart"

    if restart_requested:
        message_logger.log_incoming_message(message)
        session_manager.cleanup_user_session(chat_id)
        handle_restart(message, bot)
        return

    try:
        message_logger.log_incoming_message(message)
        if session_manager.is_state_locked(chat_id):
            locked_msg = "Please complete the current operation first."
            message_logger.log_outgoing_message(message, locked_msg)
            bot.reply_to(message, locked_msg)
            return

        num_applications = int(message.text)
        start_msg = (
            f"Wonderful choice! 🎯 I'm super excited to help you apply for internships!\n\n"
            f"I'll be applying to {num_applications} internships in each category, "
            f"for a total of {num_applications * 6} applications! 🚀\n\n"
            "Just sit back and relax while I work my magic! ✨\n"
            "This might take a little while, but I'll keep you updated on the progress! 😊"
        )
        message_logger.log_outgoing_message(message, start_msg)
        status_message = bot.reply_to(message, start_msg)

        def progress_callback(job_role, role_count, total_count):
            try:
                role_display = {
                    "data-science": "Data Science 📊",
                    "software-development": "Software Development 💻",
                    "web-development": "Web Development 🌐",
                    "data-analytics": "Data Analytics 📈",
                    "python-django": "Python Django 🐍",
                    "business-analytics": "Business Analytics 📊",
                }.get(job_role, job_role)

                progress_msg = (
                    f"🚀 Your Internship Application Progress:\n\n"
                    f"Currently applying for: {role_display}\n"
                    f"✅ Applications in this category: {role_count}\n"
                    f"🎯 Total applications submitted: {total_count}\n\n"
                    f"I'm working hard to submit your applications! 💪\n"
                    "You can Click 'restart' Button anytime to stop and return to main menu! 😊"
                )
                message_logger.log_outgoing_message(message, progress_msg)
                bot.edit_message_text(
                    progress_msg,
                    chat_id=chat_id,
                    message_id=status_message.message_id,
                )
            except Exception as e:
                logger.error(f"Error updating progress: {str(e)}")
                message_logger.log_error(
                    chat_id,
                    str(e),
                    {"handler": "progress_callback", "error_type": type(e).__name__},
                )

        driver = setup_driver()
        session_manager.store_driver(chat_id, driver, "internshala")

        phpsessid = session_manager.get_data(chat_id, "phpsessid")
        run_internshala_automation(
            driver=driver,
            phpsessid=phpsessid,
            num_applications=num_applications,
            progress_callback=progress_callback,
            user_id=message.from_user.id,
            data_manager=data_manager,
        )

        try:
            successful_apps = data_manager.get_application_count(
                user_id=message.from_user.id, platform="internshala", status="success"
            )
            actual_count = successful_apps or (num_applications * 6)
        except Exception as e:
            logger.error(f"Error getting application count: {str(e)}")
            actual_count = num_applications * 6

        if not restart_requested:
            completion_msg = (
                "🎉 Amazing news! I've completed all the applications!\n\n"
                f"✅ Successfully applied to {actual_count} internships across all categories!\n"
                "🌟 You can check all your applications here:\n"
                "https://internshala.com/student/applications\n\n"
                "Good luck with your applications! 🍀\n\n"
                "Is there anything else you'd like me to help you with? 😊"
            )
            message_logger.log_outgoing_message(message, completion_msg)
            bot.send_message(
                chat_id, completion_msg, reply_markup=create_main_keyboard()
            )

    except ValueError:
        if not restart_requested:
            invalid_number_msg = (
                "Oops! 😅 That doesn't seem to be a valid number. "
                "Could you please enter a number like 5? Let's try again! 🎯"
            )
            message_logger.log_outgoing_message(message, invalid_number_msg)
            bot.reply_to(message, invalid_number_msg)
            bot.register_next_step_handler(
                message, process_internshala_applications, bot
            )
    except Exception as e:
        if not restart_requested:
            logger.error(f"Error processing internshala applications: {str(e)}")
            error_msg = "Sorry, there was an error processing your request. Please try again or click Restart."
            message_logger.log_error(
                chat_id,
                str(e),
                {
                    "handler": "process_internshala_applications",
                    "error_type": type(e).__name__,
                    "state": session_manager.get_state(chat_id),
                },
            )
            bot.reply_to(message, error_msg, reply_markup=create_main_keyboard())
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {str(e)}")
        session_manager.cleanup_user_session(chat_id)


def ensure_user_initialized(message):
    """Initialize user and schedule offer check with logging"""
    try:
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id

        # Check if user exists
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()

        if not response.data:
            user_data = {
                "user_id": user_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            message_logger.log_outgoing_message(
                message, {"action": "register_new_user", "user_data": user_data}
            )
            data_manager.register_user(user_data)
        else:
            message_logger.log_outgoing_message(
                message, {"action": "update_user_activity", "user_id": user_id}
            )
            data_manager.update_user_activity(user_id)

        # Schedule offer check
        job_id = f"offer_check_{user_id}"
        try:
            _scheduler.add_job(
                send_offer_check_message,
                "interval",
                minutes=5,
                args=[_bot, user_id],
                id=job_id,
                replace_existing=True,
            )
            logger.info(f"Scheduled offer check for user {user_id}")
            message_logger.log_outgoing_message(
                message, {"action": "schedule_offer_check", "job_id": job_id}
            )
        except Exception as e:
            logger.error(f"Error scheduling offer check: {str(e)}")
            message_logger.log_error(
                user_id,
                str(e),
                {
                    "handler": "ensure_user_initialized",
                    "action": "schedule_offer_check",
                    "error_type": type(e).__name__,
                },
            )

    except Exception as e:
        logger.error(f"Error initializing user: {str(e)}")
        message_logger.log_error(
            message.from_user.id,
            str(e),
            {"handler": "ensure_user_initialized", "error_type": type(e).__name__},
        )


def send_offer_check_message(bot, user_id):
    """Send periodic offer check message with logging"""
    if session_manager.is_state_locked(user_id):
        logger.info(f"User {user_id} still needs to respond to previous offer check")
        return

    if session_manager.is_user_busy(user_id):
        logger.info(f"User {user_id} is busy. Rescheduling offer check.")
        return

    check_msg = (
        "👋 Hi there! Just checking in on your job search journey!\n\n"
        "Have you received any offer letters recently? We're here to help ensure your success "
        "and protect your interests every step of the way! 🌟\n\n"
        "Please respond with <b>Yes</b> or <b>No</b> to continue. This helps us provide better support! Remember, we offer:\n"
        "• Free offer letter review\n"
        "• Contract term verification\n"
        "• Protection from potential scams\n\n"
        "Your success and safety are our top priorities! 💪"
    )
    # Create a message-like object for logging
    class TelegramMessage:
        def __init__(self, chat_id, message_id):
            self.chat = type('Chat', (), {'id': chat_id, 'type': 'private'})()
            self.message_id = message_id
            self.from_user = type('User', (), {
                'id': chat_id,
                'username': None,
                'first_name': None,
                'last_name': None,
                'is_bot': False
            })()

    # Send message first to get message_id
    sent_message = bot.send_message(chat_id=user_id, text=check_msg, parse_mode="HTML")
    
    # Create message object with actual message_id
    message_obj = TelegramMessage(user_id, sent_message.message_id)

    # Log the message using the message object
    message_logger.log_outgoing_message(message_obj, check_msg)
    
    session_manager.set_state(user_id, "offer_check")
    logger.info(f"Set state for user {user_id} to offer_check and waiting for response")

    # Log state change
    message_logger.log_outgoing_message(
        message_obj,
        {"action": "state_change", "new_state": "offer_check"},
    )

def handle_offer_response(bot, message):
    """Handle responses to offer check message with logging"""
    message_logger.log_incoming_message(message)
    user_id = message.chat.id
    user_response = message.text.strip().lower()

    if session_manager.get_state(user_id) == "offer_check":
        if user_response == "yes":
            instructions_msg = (
                "🎉 Fantastic news! Congratulations on your offer!\n\n"
                "We'd love to help ensure everything is perfect with your offer letter. "
                "Our team provides:\n"
                "• Comprehensive contract review\n"
                "• Salary and benefits analysis\n"
                "• Identification of any concerning terms\n\n"
                "Please share your offer letter as a PDF file, and we'll make sure everything is secure and fair! 📄\n\n"
                "Note: All bot features will remain locked until you send your offer letter or type 'cancel'"
            )
            sent_msg = bot.reply_to(message, instructions_msg, parse_mode="HTML")
            message_logger.log_outgoing_message(message, instructions_msg)
            session_manager.set_state(user_id, "awaiting_offer_upload")

        elif user_response == "no":
            continue_msg = (
                "Keep pushing forward! 💪 The right opportunity is just around the corner.\n\n"
                "Remember, we're here to support you with:\n"
                "• Job search assistance\n"
                "• Resume optimization\n"
                "• Interview preparation\n\n"
                "I'll check back with you in a few days. Meanwhile, don't hesitate to use our services! 🌟"
            )
            sent_msg = bot.reply_to(
                message,
                continue_msg,
                parse_mode="HTML",
                reply_markup=create_main_keyboard(),
            )
            message_logger.log_outgoing_message(message, continue_msg)
            session_manager.set_state(user_id, None)

        else:
            invalid_response_msg = (
                "Please respond with either <b>Yes</b> or <b>No</b> to let us know about your offer letters.\n\n"
                "This helps us provide the right support for your situation! 🎯"
            )
            sent_msg = bot.reply_to(message, invalid_response_msg, parse_mode="HTML")
            message_logger.log_outgoing_message(message, invalid_response_msg)

def handle_offer_upload(bot, message):
    """Handle offer letter document upload"""
    user_id = message.chat.id
    current_state = session_manager.get_state(user_id)
    
    if current_state == "awaiting_offer_upload" and message.document:
        try:
            message_logger.log_incoming_message(message)

            if message.document.mime_type != "application/pdf":
                invalid_type_msg = "Please send your offer letter as a PDF file. Other file types are not supported. 📝"
                sent_msg = bot.reply_to(message, invalid_type_msg, parse_mode="HTML")
                message_logger.log_outgoing_message(message, invalid_type_msg)
                return

            file_info = bot.get_file(message.document.file_id)
            file_data = bot.download_file(file_info.file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"offer_letter_{timestamp}.pdf"

            if data_manager.upload_offer_letter(user_id, file_data, file_name):
                success_msg = (
                    "✅ Thank you! Your offer letter has been securely received and stored.\n\n"
                    "Our team will review it within 24 hours to ensure:\n"
                    "• All terms are fair and standard\n"
                    "• No concerning clauses are present\n"
                    "• Your interests are protected\n\n"
                    "We'll notify you once the review is complete! 🚀"
                )
                sent_msg = bot.reply_to(message, success_msg, parse_mode="HTML")
                message_logger.log_outgoing_message(message, success_msg)
            else:
                error_msg = (
                    "😟 There was an issue storing your offer letter securely.\n"
                    "Please try again or contact our support team for assistance.\n"
                    "We want to ensure your document is handled with the utmost security!"
                )
                sent_msg = bot.reply_to(message, error_msg, parse_mode="HTML")
                message_logger.log_error(
                    user_id,
                    "Failed to store offer letter",
                    {"handler": "handle_offer_upload", "error_type": "StorageError"},
                )

            session_manager.set_state(user_id, None)

        except Exception as e:
            logger.error(f"Error handling offer letter: {str(e)}")
            error_msg = (
                "🔄 Something went wrong while processing your offer letter.\n"
                "Please try again or contact our support team if the issue persists."
            )
            sent_msg = bot.reply_to(message, error_msg, parse_mode="HTML")
            message_logger.log_error(
                user_id,
                str(e),
                {"handler": "handle_offer_upload", "error_type": type(e).__name__},
            )
            session_manager.set_state(user_id, None)
            
    elif message.document and message.document.mime_type == "application/pdf":
        wrong_time_msg = (
            "I see you're trying to send a document! If this is your offer letter, "
            "please use the offer letter review feature when prompted. "
            "I want to make sure it's properly tracked and reviewed! 😊"
        )
        sent_msg = bot.reply_to(message, wrong_time_msg, parse_mode="HTML")
        message_logger.log_outgoing_message(message, wrong_time_msg)


def create_locked_handler(original_handler):
    """Decorator to lock handlers during offer check"""

    def wrapped_handler(message):
        current_state = session_manager.get_state(message.chat.id)
        if current_state == "offer_check":
            _bot.reply_to(
                message,
                "📌 I noticed you have a pending response.\n\n"
                "Please respond to the previous question with <b>Yes</b> or <b>No</b> first, "
                "so I can better assist you with your job search journey!\n\n"
                "Once you respond, you'll be able to use all features again. 😊",
                parse_mode="HTML",
            )
            return
        elif current_state == "awaiting_offer_upload":
            _bot.reply_to(
                message,
                "📤 I'm waiting for your offer letter.\n\n"
                "Please either:\n"
                "• Send your offer letter as a PDF\n"
                "• Or type 'cancel' to skip this step\n\n"
                "This helps us ensure your job search security! 🔐",
                parse_mode="HTML",
            )
            return
        original_handler(message)

    return wrapped_handler