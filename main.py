import telebot
import time
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from bot_handlers import (
    handle_start,
    handle_apply_jobs,
    handle_improve_resume,
    handle_apply_internships,
    handle_improve_linkedin,
    handle_restart,
    create_main_keyboard,
    send_offer_check_message,
    handle_offer_response,
    handle_offer_upload,
    handle_job_auto_apply,
    create_locked_handler,
    initialize_bot,
    create_verification_keyboard,
    check_unverified_user,
    ensure_user_initialized,
    message_logger ,
    data_manager,
    logger,
    session_manager  # Import session_manager
)
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration from environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPPORT_GROUP_ID = int(os.getenv('SUPPORT_GROUP_ID', 0))  # Default to 0 if not found
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Validate required environment variables
if not all([TOKEN, SUPPORT_GROUP_ID, SUPABASE_URL, SUPABASE_KEY]):
    logger.error("Missing required environment variables. Please check your .env file.")
    raise ValueError("Missing required environment variables")

# Initialize bot and scheduler
bot = telebot.TeleBot(TOKEN)
scheduler = BackgroundScheduler()
scheduler.start()
initialize_bot(bot, scheduler)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize request counter
request_counter = 0

@bot.message_handler(func=lambda message: message.text == '✨ Need Help?')
def handle_verification_help(message):
    try:
        user_id = message.from_user.id
        current_state = session_manager.get_state(user_id)
        
        if current_state == "waiting_for_access_key":
            help_msg = (
                "✨ Hey there! Let's get you started! ✨\n\n"
                "🌟 New to Persist Ventures?\n"
                "• Click here: https://get-a-job.persistventures.com/\n"
                "• Follow the simple steps\n"
                "• You'll get your access key via email\n\n"
                "🔑 Already registered?\n"
                "Get your key here: https://get-a-job.persistventures.com/career-accelerator/login\n\n"
                "💫 Need extra help?\n"
                "My awesome colleague @Being_titanium is ready to assist!\n"
                f"Your ID: {user_id} (share this when you reach out)\n\n"
                "🎯 Ready to start fresh? Hit 'Start Over' and let's begin! ✨"
            )
            bot.reply_to(message, help_msg, reply_markup=create_verification_keyboard())
        else:
            help_command(message)
    except Exception as e:
        logger.error(f"Error in verification help handler: {str(e)}")
        error_msg = "✨ Oops! Let's try that again! 🌟"
        bot.reply_to(message, error_msg, reply_markup=create_verification_keyboard())

@bot.message_handler(func=lambda message: message.text == '🔄 Start Over')
def handle_verification_restart(message):
    try:
        session_manager.cleanup_user_session(message.from_user.id)
        start_command(message)
    except Exception as e:
        logger.error(f"Error in verification restart handler: {str(e)}")
        error_msg = "✨ Oops! Let's try that again! 🌟"
        bot.reply_to(message, error_msg, reply_markup=create_verification_keyboard())

@bot.message_handler(commands=['start'])
@create_locked_handler
def start_command(message):
    try:
        logger.info("Start command received")
        message_logger.log_incoming_message(message)
        user_id = message.from_user.id
        
        user_data = session_manager.get_data(user_id, "user_data", {})
        
        # Check if user needs verification first
        if check_unverified_user(bot, message, user_data):
            return  # Stop further processing if verification is needed
            
        # If verified, proceed with your normal start handler
        logger.info("Calling handle_start")
        handle_start(bot, message)
        
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        error_msg = "✨ Oops! Let's try that again! 🌟"
        bot.reply_to(message, error_msg, reply_markup=create_verification_keyboard())

@bot.message_handler(commands=['help'])
@create_locked_handler
def help_command(message):
    global request_counter
    request_counter += 1
    
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    first_name = message.from_user.first_name or "No first name"
    
    # Get LinkedIn profile from accelerator_users table
    try:
        response = supabase.table('accelerator_users')\
            .select('linkedin_url')\
            .eq('telegram_user_id', str(user_id))\
            .execute()
            
        linkedin_url = ''
        if response.data and len(response.data) > 0:
            linkedin_url = response.data[0].get('linkedin_url', '')
            
        # Format LinkedIn part of message based on URL availability
        linkedin_part = (
            f'LinkedIn: <a href="{linkedin_url}">View Profile</a>'
            if linkedin_url
            else "LinkedIn: Not linked"
        )
    except Exception as e:
        logger.error(f"Error fetching LinkedIn URL: {str(e)}")
        linkedin_part = "LinkedIn: Not available"
    
    # Help message to user (using Markdown)
    help_message = (
        "Need help? Here's your support information:\n\n"
        f"Your ID: `{user_id}`\n"
        "To get support:\n"
        "1. Contact our support team: @Being\_titanium\n"
        "2. Share your ID shown above\n"
        "3. Describe your issue\n\n"
        "Common commands:\n"
        "/start - Start the bot\n"
        "/help - Message support\n"
        "You can also use the menu buttons below for different features!"
    )
    
    bot.reply_to(message, help_message, parse_mode='Markdown')
    
    # Support group notification (using HTML)
    support_notification = (
        f"🆘 New Help Request #{request_counter}:\n"
        f"User ID: {user_id}\n"
        f"Username: @{username}\n"
        f"First Name: {first_name}\n"
        f'<a href="tg://user?id={user_id}">Telegram Profile</a>\n'
        f"{linkedin_part}"
    )
    
    try:
        bot.send_message(SUPPORT_GROUP_ID, support_notification, parse_mode='HTML')
        logger.info(f"Help request #{request_counter} notification sent for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send help notification to support group: {str(e)}")


@bot.message_handler(func=lambda message: message.text == 'Job Auto Apply')
@create_locked_handler
def job_auto_apply_command(message):
    ensure_user_initialized(message)
    handle_job_auto_apply(bot, message)


@bot.message_handler(func=lambda message: message.text == 'Improve Resume/CV')
@create_locked_handler
def improve_resume_command(message):
    ensure_user_initialized(message)
    handle_improve_resume(bot, message)

@bot.message_handler(func=lambda message: message.text == 'Improve LinkedIn Profile')
@create_locked_handler
def improve_linkedin_command(message):
    ensure_user_initialized(message)
    handle_improve_linkedin(bot, message)    


@bot.message_handler(func=lambda message: message.text == 'Restart' or message.text.lower() == 'restart')
def restart_command(message):
    ensure_user_initialized(message)
    handle_restart(message, bot)

# Message Handlers
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    user_id = message.chat.id
    current_state = session_manager.get_state(user_id)  # Use session_manager
    
    if current_state == "offer_check":
        user_response = message.text.strip().lower()
        if user_response == "yes":
            bot.reply_to(
                message,
                "🎉 Fantastic news! Congratulations on your offer!\n\n"
                "We'd love to help ensure everything is perfect with your offer letter. "
                "Our team provides:\n"
                "• Comprehensive contract review\n"
                "• Salary and benefits analysis\n"
                "• Identification of any concerning terms\n\n"
                "Please share your offer letter, and we'll make sure everything is secure and fair! 📄\n\n"
                "Note: All bot features will remain locked until you send your offer letter or type 'cancel'",
                parse_mode='HTML'
            )
            session_manager.set_state(user_id, "awaiting_offer_upload")  # Use session_manager
        elif user_response == "no":
            bot.reply_to(
                message,
                "Keep pushing forward! 💪 The right opportunity is just around the corner.\n\n"
                "Remember, we're here to support you with:\n"
                "• Job search assistance\n"
                "• Resume optimization\n"
                "• Interview preparation\n\n"
                "I'll check back with you in a few days. Meanwhile, don't hesitate to use our services! 🌟",
                parse_mode='HTML',
                reply_markup=create_main_keyboard()
            )
            session_manager.set_state(user_id, None)  # Use session_manager
        else:
            bot.reply_to(
                message,
                "Please respond with either <b>Yes</b> or <b>No</b> to let us know about your offer letters.\n\n"
                "This helps us provide the right support for your situation! 🎯",
                parse_mode='HTML'
            )
    elif current_state == "awaiting_offer_upload":
        if message.text.lower() == 'cancel':
            session_manager.set_state(user_id, None)  # Use session_manager
            bot.reply_to(
                message,
                "Offer letter upload cancelled. You can now use all features again! 😊",
                reply_markup=create_main_keyboard()
            )
        else:
            bot.reply_to(
                message,
                "📤 I'm still waiting for your offer letter.\n\n"
                "Please send your offer letter as a PDF file, or type 'cancel' if you want to skip this step.\n\n"
                "This helps us ensure your interests are protected! 🛡️",
                parse_mode='HTML'
            )

# Document Handler
@bot.message_handler(content_types=['document'])
def handle_documents(message):
    current_state = session_manager.get_state(message.chat.id)  # Use session_manager
    if current_state == "awaiting_offer_upload":
        try:
            if message.document.mime_type != 'application/pdf':
                bot.reply_to(
                    message,
                    "Please send your offer letter as a PDF file only.\n"
                    "This ensures proper document handling and security! 📄",
                    parse_mode='HTML'
                )
                return

            file_info = bot.get_file(message.document.file_id)
            file_data = bot.download_file(file_info.file_path)
            original_name = message.document.file_name or "offer_letter.pdf"
            
            upload_success = data_manager.upload_offer_letter(
                message.chat.id, 
                file_data, 
                original_name
            )
            
            if upload_success:
                bot.reply_to(
                    message,
                    "✅ Offer letter received and securely stored!\n\n"
                    "Our team will review it within 24 hours to ensure:\n"
                    "• All terms are fair and standard\n"
                    "• No concerning clauses are present\n"
                    "• Your interests are protected\n\n"
                    "We'll notify you once the review is complete! 🚀",
                    parse_mode='HTML',
                    reply_markup=create_main_keyboard()
                )
                session_manager.set_state(message.chat.id, None)  # Use session_manager
                
                # Send notification to support group
                try:
                    support_notification = (
                        f"📋 New Offer Letter Received!\n\n"
                        f"From User ID: {message.chat.id}\n"
                        f"Username: @{message.from_user.username or 'No username'}\n"
                        f"Name: {message.from_user.first_name or 'No name'}\n"
                        f"File Name: {original_name}\n"
                        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"Please review within 24 hours."
                    )
                    bot.send_message(SUPPORT_GROUP_ID, support_notification, parse_mode='HTML')
                except Exception as notify_error:
                    logger.error(f"Failed to send support notification: {str(notify_error)}")
            else:
                bot.reply_to(
                    message,
                    "😟 There was an issue storing your offer letter.\n"
                    "Please try again or contact our support team (@Being_titanium).\n"
                    "You can also type 'cancel' to skip this step.",
                    parse_mode='HTML'
                )
                session_manager.set_state(message.chat.id, "awaiting_offer_upload")  # Use session_manager
        except Exception as e:
            logger.error(f"Error handling offer letter: {str(e)}")
            bot.reply_to(
                message,
                "🔄 Something went wrong while processing your offer letter.\n"
                "Please try again or contact our support team if the issue persists.",
                parse_mode='HTML'
            )
            session_manager.set_state(message.chat.id, "awaiting_offer_upload")  # Use session_manager
    else:
        # Handle document uploads during other states
        if message.document and message.document.mime_type == 'application/pdf':
            if current_state == "offer_check":
                bot.reply_to(
                    message,
                    "I see you're trying to upload an offer letter!\n\n"
                    "Please first respond with <b>Yes</b> to my previous question,\n"
                    "then I'll accept your offer letter for review. 📝",
                    parse_mode='HTML'
                )
            else:
                bot.reply_to(
                    message,
                    "I see you're trying to send a document! If this is your offer letter, "
                    "please wait for the offer letter review prompt. "
                    "This helps us track and review it properly! 😊",
                    parse_mode='HTML'
                )

# Main execution
if __name__ == '__main__':
    logger.info("Starting bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(15)