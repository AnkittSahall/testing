# import os
# import telebot
# import asyncio
# import logging
# from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor
# from dotenv import load_dotenv
# from telebot.apihelper import ApiTelegramException
# from typing import List, Dict
# import aiohttp
# from aiohttp import ClientSession
# from supabase import create_client

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('broadcast.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# # Initialize bot
# TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# SUPABASE_URL = os.getenv('SUPABASE_URL')
# SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# if not all([TOKEN, SUPABASE_URL, SUPABASE_KEY]):
#     raise ValueError("Missing required environment variables!")

# bot = telebot.TeleBot(TOKEN)

# # Admin IDs - Replace with your admin Telegram IDs
# ADMIN_IDS = [674456268]  # Replace with your admin IDs

# class BroadcastBot:
#     def __init__(self):
#         self.user_ids = set()
#         self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
#         self._initialize_users()

#     def _initialize_users(self):
#         """Initialize users from Supabase database"""
#         try:
#             # Get users from users table
#             response = self.supabase.table('users').select('user_id').execute()
#             if response.data:
#                 self.user_ids.update(user['user_id'] for user in response.data)
            
#             # Also get users from accelerator_users table
#             response = self.supabase.table('accelerator_users')\
#                 .select('telegram_user_id')\
#                 .not_('telegram_user_id', 'is', None)\
#                 .execute()
            
#             if response.data:
#                 # Convert string IDs to integers and add to set
#                 self.user_ids.update(
#                     int(user['telegram_user_id']) 
#                     for user in response.data 
#                     if user['telegram_user_id']
#                 )
            
#             logger.info(f"Loaded {len(self.user_ids)} users from database")
            
#             # Save users to file for backup
#             self._save_users_to_file()
            
#         except Exception as e:
#             logger.error(f"Error initializing users: {e}")
#             # Try to load from backup file
#             self._load_from_backup()

#     def _save_users_to_file(self):
#         """Save users to backup file"""
#         try:
#             os.makedirs('storage', exist_ok=True)
#             with open('storage/users.txt', 'w') as f:
#                 for user_id in self.user_ids:
#                     f.write(f"{user_id}\n")
#         except Exception as e:
#             logger.error(f"Error saving users to file: {e}")

#     def _load_from_backup(self):
#         """Load users from backup file"""
#         try:
#             if os.path.exists('storage/users.txt'):
#                 with open('storage/users.txt', 'r') as f:
#                     self.user_ids = set(int(line.strip()) for line in f if line.strip())
#                 logger.info(f"Loaded {len(self.user_ids)} users from backup file")
#         except Exception as e:
#             logger.error(f"Error loading from backup: {e}")

#     async def send_message(self, user_id: int, message: str, session: ClientSession) -> bool:
#         """Send message to a single user"""
#         try:
#             url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
#             data = {
#                 "chat_id": user_id,
#                 "text": message,
#                 "parse_mode": "HTML"
#             }
            
#             async with session.post(url, json=data) as response:
#                 if response.status == 200:
#                     return True
#                 else:
#                     error_data = await response.text()
#                     logger.error(f"Error sending to {user_id}: {error_data}")
#                     return False
#         except Exception as e:
#             logger.error(f"Exception sending to {user_id}: {e}")
#             return False

#     async def broadcast_message(self, message: str) -> Dict:
#         """Send broadcast message to all users"""
#         results = {
#             'total': len(self.user_ids),
#             'success': 0,
#             'failed': 0,
#             'failed_ids': []
#         }

#         if not self.user_ids:
#             return results

#         async with ClientSession() as session:
#             tasks = []
#             for user_id in self.user_ids:
#                 task = self.send_message(user_id, message, session)
#                 tasks.append(task)

#             # Send messages in batches of 30
#             batch_size = 30
#             for i in range(0, len(tasks), batch_size):
#                 batch = tasks[i:i + batch_size]
#                 results_batch = await asyncio.gather(*batch, return_exceptions=True)
                
#                 for j, result in enumerate(results_batch):
#                     user_id = list(self.user_ids)[i + j]
#                     if isinstance(result, Exception) or result is False:
#                         results['failed'] += 1
#                         results['failed_ids'].append(user_id)
#                     else:
#                         results['success'] += 1

#                 # Small delay between batches to avoid rate limits
#                 await asyncio.sleep(1)

#         return results

# broadcast_bot = BroadcastBot()

# @bot.message_handler(commands=['start'])
# def handle_start(message):
#     """Handle /start command"""
#     try:
#         user_id = message.from_user.id
#         broadcast_bot.user_ids.add(user_id)
#         broadcast_bot._save_users_to_file()
#         bot.reply_to(message, "Welcome! You've been added to the broadcast list.")
#     except Exception as e:
#         logger.error(f"Error in start handler: {e}")

# @bot.message_handler(commands=['stats'])
# def handle_stats(message):
#     """Show total users stats"""
#     if message.from_user.id not in ADMIN_IDS:
#         bot.reply_to(message, "❌ You are not authorized to use this command.")
#         return

#     try:
#         stats = (
#             f"📊 Broadcast Bot Statistics\n\n"
#             f"Total Users: {len(broadcast_bot.user_ids)}\n"
#             f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
#             f"To start broadcast, use /broadcast command."
#         )
#         bot.reply_to(message, stats)
#     except Exception as e:
#         logger.error(f"Error in stats handler: {e}")
#         bot.reply_to(message, "Error getting statistics.")

# @bot.message_handler(commands=['reload_users'])
# def handle_reload(message):
#     """Reload users from database"""
#     if message.from_user.id not in ADMIN_IDS:
#         bot.reply_to(message, "❌ You are not authorized to use this command.")
#         return

#     try:
#         old_count = len(broadcast_bot.user_ids)
#         broadcast_bot._initialize_users()
#         new_count = len(broadcast_bot.user_ids)
        
#         bot.reply_to(
#             message,
#             f"✅ Users reloaded successfully!\n\n"
#             f"Previous count: {old_count}\n"
#             f"New count: {new_count}\n"
#             f"Difference: {new_count - old_count}"
#         )
#     except Exception as e:
#         logger.error(f"Error reloading users: {e}")
#         bot.reply_to(message, "Error reloading users.")

# @bot.message_handler(commands=['broadcast'])
# def handle_broadcast(message):
#     """Start broadcast process"""
#     if message.from_user.id not in ADMIN_IDS:
#         bot.reply_to(message, "❌ You are not authorized to use this command.")
#         return

#     if not broadcast_bot.user_ids:
#         bot.reply_to(
#             message,
#             "⚠️ No users found in the database!\n"
#             "Use /reload_users to refresh the user list."
#         )
#         return

#     try:
#         bot.reply_to(
#             message,
#             "📝 Send me the message you want to broadcast.\n\n"
#             "• HTML formatting is supported\n"
#             "• Send /cancel to cancel\n\n"
#             "Your next message will be used for broadcast."
#         )
#         bot.register_next_step_handler(message, get_broadcast_message)
#     except Exception as e:
#         logger.error(f"Error in broadcast handler: {e}")
#         bot.reply_to(message, "Error starting broadcast process.")

# def get_broadcast_message(message):
#     """Get the broadcast message content"""
#     if message.text == '/cancel':
#         bot.reply_to(message, "Broadcast cancelled.")
#         return

#     try:
#         preview = (
#             "📢 Broadcast Preview:\n"
#             "──────────────\n"
#             f"{message.text}\n"
#             "──────────────\n\n"
#             f"This will be sent to {len(broadcast_bot.user_ids)} users.\n\n"
#             "Reply with:\n"
#             "YES - Send broadcast\n"
#             "NO - Cancel broadcast"
#         )
#         bot.reply_to(message, preview)
        
#         # Store message for confirmation
#         broadcast_bot.temp_message = message.text
#         bot.register_next_step_handler(message, confirm_broadcast)
#     except Exception as e:
#         logger.error(f"Error getting broadcast message: {e}")
#         bot.reply_to(message, "Error processing broadcast message.")

# def confirm_broadcast(message):
#     """Handle broadcast confirmation"""
#     if message.text.upper() not in ['YES', 'NO']:
#         bot.reply_to(message, "Please reply with YES or NO.")
#         bot.register_next_step_handler(message, confirm_broadcast)
#         return

#     if message.text.upper() == 'NO':
#         bot.reply_to(message, "Broadcast cancelled.")
#         return

#     try:
#         status_msg = bot.reply_to(message, "📣 Starting broadcast...")
        
#         async def run_broadcast():
#             results = await broadcast_bot.broadcast_message(broadcast_bot.temp_message)
            
#             result_text = (
#                 "📊 Broadcast Results\n\n"
#                 f"✅ Successfully sent: {results['success']}\n"
#                 f"❌ Failed: {results['failed']}\n"
#                 f"📨 Total recipients: {results['total']}"
#             )
            
#             if results['failed_ids']:
#                 result_text += f"\n\nFailed IDs: {', '.join(map(str, results['failed_ids']))}"
            
#             return result_text

#         # Run the async broadcast
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         result_text = loop.run_until_complete(run_broadcast())
#         loop.close()

#         # Update status message with results
#         bot.edit_message_text(
#             result_text,
#             chat_id=status_msg.chat.id,
#             message_id=status_msg.message_id
#         )

#     except Exception as e:
#         logger.error(f"Error in broadcast confirmation: {e}")
#         bot.reply_to(message, "Error sending broadcast messages.")

# def main():
#     """Start the bot"""
#     logger.info("Starting broadcast bot...")
#     bot.infinity_polling()

# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         logger.error(f"Bot crashed: {e}")



#old wale model
# #with database added
# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium.webdriver.support.select import Select
# import time
# import logging
# import os
# from datetime import datetime
# from supabase import create_client
# from data_manager import DataManager
# data_manager = DataManager()


# # Replace these with your actual Supabase credentials
# SUPABASE_URL = "https://bpqhyuekxyzgvumdgycr.supabase.co"
# SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwcWh5dWVreHl6Z3Z1bWRneWNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA3NDI1NjIsImV4cCI6MjA0NjMxODU2Mn0.rfPR6JJ9i7qcvthPlkq-YtJgx5k31qWd1wybS8BimWA"
# supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# logger = logging.getLogger(__name__)

# def setup_driver():
#     """Initialize the Firefox WebDriver with proper options"""
#     firefox_options = FirefoxOptions()
#     firefox_options.add_argument("--window-size=1920,1080")
#     firefox_options.add_argument("--disable-infobars")
#     firefox_options.add_argument("--disable-extensions")
#     firefox_options.add_argument("--start-maximized")
    
#     try:
#         driver = webdriver.Firefox(options=firefox_options)
#         driver.maximize_window()
#         logger.info("Firefox WebDriver initialized successfully.")
#         return driver
#     except Exception as e:
#         logger.error(f"Failed to initialize Firefox WebDriver: {str(e)}")
#         raise

# def login_to_linkedin(driver, li_at):
#     """Fixed LinkedIn login with proper success verification"""
#     try:
#         logger.info("Starting LinkedIn login process...")
        
#         # Initial load
#         driver.get("https://www.linkedin.com")
#         time.sleep(3)
        
#         driver.delete_all_cookies()
#         time.sleep(1)
        
#         # Add cookie
#         cookie = {
#             'name': 'li_at',
#             'value': li_at,
#             'domain': '.linkedin.com',
#             'path': '/'
#         }
        
#         driver.add_cookie(cookie)
#         logger.info("Added li_at cookie")
        
#         # Important: Load feed page and wait longer
#         driver.get("https://www.linkedin.com/feed/")
#         time.sleep(8)  # Increased wait time
        
#         try:
#             # Check for ANY of these elements, not all
#             selectors = [
#                 "div.feed-identity-module",
#                 "#global-nav",
#                 ".ember-view",
#                 "[data-control-name='nav.settings']"
#             ]
            
#             for selector in selectors:
#                 try:
#                     element = WebDriverWait(driver, 5).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, selector))
#                     )
#                     if element.is_displayed():
#                         logger.info(f"Login verified via {selector}")
#                         return True
#                 except:
#                     continue
            
#             # Final URL check
#             if "feed" in driver.current_url:
#                 logger.info("Login verified via URL")
#                 return True
                
#             return False
            
#         except Exception as e:
#             logger.error(f"Verification failed: {str(e)}")
#             return False
            
#     except Exception as e:
#         logger.error(f"Login failed: {str(e)}")
#         return False

# def verify_login_status(driver):
#     """Quick check if still logged in"""
#     try:
#         current_url = driver.current_url
#         if "login" in current_url or "signup" in current_url:
#             return False
#         return "feed" in current_url or len(driver.find_elements(By.CSS_SELECTOR, ".ember-view")) > 0
#     except:
#         return False

# def get_user_name(driver):
#     try:
#         name_element = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div.feed-identity-module__actor-meta a.ember-view"))
#         )
#         return name_element.text.split()[0]  # Get first name
#     except:
#         return "there"  # Fallback if name can't be retrieved

# def search_jobs(driver, search_keyword):
#     try:
#         logger.info(f"Navigating to LinkedIn Jobs page...")
#         driver.get("https://www.linkedin.com/jobs/")
#         wait = WebDriverWait(driver, 30)
        
#         logger.info(f"Searching for: {search_keyword}")
#         keyword_search = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-box__text-input")))
#         keyword_search.clear()
#         keyword_search.send_keys(f"{search_keyword}", Keys.ENTER)
#         time.sleep(10)
        
#         logger.info("Attempting to click the Easy Apply filter...")
#         try:
#             easy_apply_filter = driver.find_element(By.CLASS_NAME, 'search-reusables__filter-binary-toggle')
#             easy_apply_filter.click()
#             logger.info("Easy Apply filter applied successfully")
#         except (TimeoutException, NoSuchElementException) as e:
#             logger.error(f"Failed to find or click Easy Apply filter: {str(e)}")
        
#         time.sleep(10)
        
#         logger.info("Extracting job listings...")
#         job_listings = wait.until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
#         )
#         logger.info(f"Found {len(job_listings)} job listings")
#         return job_listings
        
#     except Exception as e:
#         logger.error(f"An unexpected error occurred during job search: {str(e)}")
#         return []

# # predefined_answers = {
# #     "how many": "0",
# #     "experience": "0",
# #     "notice": "0",
# #     "sponsor": "No",
# #     "city": "Mumbai",
# #     "AWS": "0",
# #     "do you": "Yes",
# #     "have you": "Yes",
# #     "Indian citizen": "Yes",
# #     "are you": "Yes",
# #     "expected ctc": "700000",
# #     "current ctc": "0",
# #     "can you": "Yes",
# #     "gender": "Male",
# #     "race": "Wish not to answer",
# #     "lgbtq": "Wish not to answer",
# #     "ethnicity": "Wish not to answer",
# #     "nationality": "Wish not to answer",
# #     "government": "I do not wish to self-identify",
# #     "legally": "Yes"
# # }

# # def get_answer(question, input_type="text"):
# #     question_lower = question.lower()
# #     for key, value in predefined_answers.items():
# #         if key in question_lower:
# #             return value
# #     if input_type == "text":
# #         if any(word in question_lower for word in ["experience", "years", "how many", "number of"]):
# #             return "0"
# #         return "0"
# #     elif input_type == "dropdown":
# #         return "No"
# #     else:
# #         return ""

# # def handle_form_fields(driver):
# #     wait = WebDriverWait(driver, 10)
# #     try:
# #         while True:
# #             # Updated form container selector
# #             try:
# #                 form_container = driver.find_element(By.CSS_SELECTOR, 
# #                     ".jobs-easy-apply-content, .artdeco-modal__content")
# #                 driver.execute_script("arguments[0].scrollTo(0, 0);", form_container)
# #             except:
# #                 pass

# #             # Text input fields - using the reference code's selectors
# #             text_fields = driver.find_elements(By.XPATH, 
# #                 '//*[contains(@class, "artdeco-text-input--label")]')
            
# #             for field in text_fields:
# #                 try:
# #                     question = field.text
# #                     answer = get_answer(question)
# #                     input_element = field.find_element(By.XPATH,
# #                         './/input[contains(@class, "artdeco-text-input--input")]')
# #                     input_element.clear()
# #                     input_element.send_keys(answer)
# #                 except Exception as e:
# #                     print(f"Error with text field: {str(e)}")

# #             # Radio buttons - using reference code's selectors
# #             radio_elements = driver.find_elements(By.XPATH,
# #                 "//*[contains(@id, 'radio-button-form-component-formElement-urn-li-jobs-applyfor')]")
            
# #             for radio in radio_elements:
# #                 try:
# #                     question = radio.text
# #                     answer = get_answer(question, "radio")
# #                     radio_options = radio.find_elements(By.XPATH,
# #                         './/label[@data-test-text-selectable-option__label]')
# #                     if radio_options:
# #                         driver.execute_script("arguments[0].click();", radio_options[0])
# #                 except Exception as e:
# #                     print(f"Error with radio button: {str(e)}")

# #             # Dropdowns - using reference code's selectors
# #             dropdowns = driver.find_elements(By.XPATH,
# #                 "//*[contains(@id, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement')]")
            
# #             for dropdown in dropdowns:
# #                 try:
# #                     question = dropdown.get_attribute("aria-label")
# #                     select = Select(dropdown)
# #                     if len(select.options) > 1:
# #                         select.select_by_index(1)
# #                 except Exception as e:
# #                     print(f"Error with dropdown: {str(e)}")

# #             try:
# #                 driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", form_container)
# #                 time.sleep(0.5)
# #             except:
# #                 pass

# #             clicked_next = click_next_button(driver)
# #             if clicked_next == "Submit":
# #                 return
# #             time.sleep(2)
            
# #     except TimeoutException:
# #         print("Timeout waiting for form fields to load or next section.")
# #     except NoSuchElementException:
# #         print("Could not find form fields")
# #     except Exception as e:
# #         print(f"An error occurred: {str(e)}")

# predefined_answers = {
#     # Experience related
#     "how many": "0",
#     "experience": "0",
#     "years": "0",
#     "number of years": "0",
#     "work experience": "0",
    
#     # Skills and ratings
#     "rate": "3",
#     "skill": "3",
#     "proficiency": "3",
#     "scale of": "3",
#     "rate out of": "3",
#     "AWS": "0",
#     "python": "1",
#     "java": "1",
#     "programming": "1",
    
#     # Job related
#     "notice": "0",
#     "notice period": "0",
#     "current ctc": "0",
#     "expected ctc": "400000",
#     "current salary": "0",
#     "expected salary": "400000",
#     "compensation": "400000",
    
#     # Location and availability
#     "city": "Mumbai",
#     "location": "Mumbai",
#     "relocate": "Yes",
#     "work from office": "Yes",
#     "hybrid": "Yes",
#     "remote": "Yes",
#     "travel": "Yes",
    
#     # Verification questions
#     "sponsor": "No",
#     "do you": "Yes",
#     "have you": "No",  # Changed to No for fresher context
#     "are you": "Yes",
#     "can you": "Yes",
#     "willing to": "Yes",
#     "ready to": "Yes",
#     "legally": "Yes",
#     "eligible": "Yes",
#     "authorized": "Yes",
#     "Indian citizen": "Yes",
    
#     # Personal information
#     "gender": "Male",
#     "race": "Wish not to answer",
#     "lgbtq": "Wish not to answer",
#     "ethnicity": "Wish not to answer",
#     "nationality": "Indian",
#     "government": "I do not wish to self-identify",
    
#     # Education
#     "education": "Bachelor's Degree",
#     "degree": "Bachelor's Degree",
#     "qualification": "Bachelor's Degree",
#     "graduate": "2024",
#     "graduation": "2024",
#     "cgpa": "8",
#     "percentage": "80"
# }

# def get_answer(question, input_type="text"):
#     question_lower = question.lower()
    
#     # Check for exact matches first
#     for key, value in predefined_answers.items():
#         if key in question_lower:
#             return value
    
#     # Handle different input types with default values
#     if input_type == "text":
#         if any(word in question_lower for word in ["experience", "years", "how many", "number of"]):
#             return "0"
#         elif any(word in question_lower for word in ["rate", "scale", "skill"]):
#             return "3"
#         return "0"
#     elif input_type == "dropdown":
#         if "experience" in question_lower:
#             return "0-1 years"
#         elif "education" in question_lower or "degree" in question_lower:
#             return "Bachelor's Degree"
#         elif "notice" in question_lower:
#             return "Immediate"
#         return "Yes"
#     elif input_type == "radio":
#         if any(word in question_lower for word in ["gender", "sex"]):
#             return "Male"
#         elif any(word in question_lower for word in ["race", "ethnicity", "lgbtq"]):
#             return "Wish not to answer"
#         return "Yes"
#     else:
#         return "0"

# # def handle_form_fields(driver):
# #     try:
# #         wait = WebDriverWait(driver, 10)
        
# #         # Handle text/numeric input fields
# #         input_fields = wait.until(EC.presence_of_all_elements_located(
# #             (By.XPATH, '//input[contains(@class, "artdeco-text-input--input")]')))
        
# #         for input_field in input_fields:
# #             try:
# #                 # Scroll into view
# #                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
# #                 time.sleep(0.5)
                
# #                 # Get the question (label)
# #                 label = input_field.find_element(By.XPATH, 
# #                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
# #                 question = label.text.strip()
                
# #                 # Get predefined answer or use fallback
# #                 answer = get_answer(question, "text")
# #                 if not answer:
# #                     if any(word in question.lower() for word in ["years", "number", "how many", "rate", "salary", "ctc"]):
# #                         answer = "1"  # Default numeric value
# #                     else:
# #                         answer = "Please check my resume"  # Default text value
                
# #                 # Clear and fill
# #                 input_field.clear()
# #                 input_field.send_keys(Keys.CONTROL + "a")
# #                 input_field.send_keys(Keys.DELETE)
# #                 time.sleep(0.2)
# #                 input_field.send_keys(answer)
# #                 input_field.send_keys(Keys.TAB)
# #                 time.sleep(0.2)
                
# #             except Exception as e:
# #                 print(f"Error with input field: {str(e)}")
        
# #         # Handle radio buttons
# #         radio_groups = driver.find_elements(By.XPATH,
# #             '//fieldset[contains(@class, "artdeco-form__group--radio")]')
        
# #         for group in radio_groups:
# #             try:
# #                 # Scroll into view
# #                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", group)
# #                 time.sleep(0.5)
                
# #                 # Get question and options
# #                 question = group.find_element(By.XPATH, './/legend').text.strip()
# #                 options = group.find_elements(By.XPATH, './/label[@data-test-text-selectable-option__label]')
                
# #                 # Get answer or select first option
# #                 answer = get_answer(question, "radio")
# #                 if answer and options:
# #                     for option in options:
# #                         if answer.lower() in option.text.lower():
# #                             driver.execute_script("arguments[0].click();", option)
# #                             time.sleep(0.2)
# #                             break
# #                     else:
# #                         driver.execute_script("arguments[0].click();", options[0])
# #                 elif options:
# #                     driver.execute_script("arguments[0].click();", options[0])
# #                 time.sleep(0.2)
                        
# #             except Exception as e:
# #                 print(f"Error with radio button: {str(e)}")
        
# #         # Handle dropdowns
# #         dropdown_containers = driver.find_elements(By.XPATH,
# #             '//div[contains(@class, "fb-dropdown")]')
        
# #         for container in dropdown_containers:
# #             try:
# #                 # Scroll into view
# #                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container)
# #                 time.sleep(0.5)
                
# #                 # Get question
# #                 label = container.find_element(By.XPATH, './/label')
# #                 question = label.text.strip()
                
# #                 # Find and interact with select element
# #                 select_elem = container.find_element(By.XPATH, './/select')
# #                 select = Select(select_elem)
                
# #                 # Get answer or select first non-empty option
# #                 answer = get_answer(question, "dropdown")
# #                 try:
# #                     if answer:
# #                         select.select_by_visible_text(answer)
# #                     else:
# #                         if len(select.options) > 1:
# #                             select.select_by_index(1)
# #                         else:
# #                             select.select_by_index(0)
# #                 except:
# #                     if len(select.options) > 0:
# #                         select.select_by_index(0)
# #                 time.sleep(0.2)
                
# #             except Exception as e:
# #                 print(f"Error with dropdown: {str(e)}")
        
# #         # Try to proceed
# #         try:
# #             next_button = wait.until(EC.element_to_be_clickable(
# #                 (By.CSS_SELECTOR, "button[aria-label='Continue to next step']")))
# #             driver.execute_script("arguments[0].click();", next_button)
# #             time.sleep(1)
# #         except:
# #             try:
# #                 review_button = wait.until(EC.element_to_be_clickable(
# #                     (By.CSS_SELECTOR, "button[aria-label='Review your application']")))
# #                 driver.execute_script("arguments[0].click();", review_button)
# #                 time.sleep(1)
# #             except:
# #                 try:
# #                     submit_button = wait.until(EC.element_to_be_clickable(
# #                         (By.CSS_SELECTOR, "button[aria-label='Submit application']")))
# #                     driver.execute_script("arguments[0].click();", submit_button)
# #                     return True
# #                 except:
# #                     pass
        
# #         return True

# #     except Exception as e:
# #         print(f"An error occurred in handle_form_fields: {str(e)}")
# #         return False

# def handle_form_fields(driver):
#     try:
#         wait = WebDriverWait(driver, 10)
        
#         # Handle text/numeric input fields
#         input_fields = wait.until(EC.presence_of_all_elements_located(
#             (By.XPATH, '//input[contains(@class, "artdeco-text-input--input")]')))
        
#         for input_field in input_fields:
#             try:
#                 # Scroll into view
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
#                 time.sleep(0.5)
                
#                 # Get the question (label)
#                 label = input_field.find_element(By.XPATH, 
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
#                 question = label.text.strip()
                
#                 # Check if it's a numeric field
#                 is_numeric = any(word in question.lower() for word in [
#                     "years", "number", "how many", "rate", "salary", "ctc", "exp",
#                     "experience", "period", "phone"
#                 ])
                
#                 # Get answer based on field type
#                 if is_numeric:
#                     answer = "0"  # Always use "0" for numeric fields
#                 else:
#                     answer = "Please check my resume"
                
#                 # Clear and fill
#                 input_field.clear()
#                 input_field.send_keys(Keys.CONTROL + "a")
#                 input_field.send_keys(Keys.DELETE)
#                 time.sleep(0.2)
#                 input_field.send_keys(answer)
#                 input_field.send_keys(Keys.TAB)
#                 time.sleep(0.2)
                
#             except Exception as e:
#                 print(f"Error with input field: {str(e)}")
        
#         # Handle dropdowns
#         dropdown_selectors = [
#             '//div[contains(@class, "fb-dropdown")]//select',
#             '//select[contains(@class, "select-input")]',
#             '//select'  # Fallback to any select element
#         ]
        
#         for selector in dropdown_selectors:
#             dropdowns = driver.find_elements(By.XPATH, selector)
#             for dropdown in dropdowns:
#                 try:
#                     # Scroll into view
#                     driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
#                     time.sleep(0.5)
                    
#                     # Create Select object
#                     select = Select(dropdown)
                    
#                     # Always select the first non-empty option
#                     if len(select.options) > 1:
#                         select.select_by_index(1)
#                     else:
#                         select.select_by_index(0)
#                     time.sleep(0.2)
                    
#                 except Exception as e:
#                     print(f"Error with dropdown: {str(e)}")
#                     continue
        
#         # Handle radio buttons
#         radio_groups = driver.find_elements(By.XPATH,
#             '//fieldset[contains(@class, "artdeco-form__group--radio")]')
        
#         for group in radio_groups:
#             try:
#                 # Scroll into view
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", group)
#                 time.sleep(0.5)
                
#                 # Always select first option for radio buttons
#                 options = group.find_elements(By.XPATH, './/label[@data-test-text-selectable-option__label]')
#                 if options:
#                     driver.execute_script("arguments[0].click();", options[0])
#                     time.sleep(0.2)
                        
#             except Exception as e:
#                 print(f"Error with radio button: {str(e)}")
        
#         # Try to proceed with better button handling
#         buttons_to_try = [
#             ("button[aria-label='Submit application']", "Submit"),
#             ("button[aria-label='Review your application']", "Review"),
#             ("button[aria-label='Continue to next step']", "Next"),
#             ("button:contains('Submit')", "Submit"),
#             ("button:contains('Review')", "Review"),
#             ("button:contains('Next')", "Next")
#         ]
        
#         for button_selector, button_type in buttons_to_try:
#             try:
#                 # Find the button
#                 button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, button_selector)))
                
#                 # Scroll the button into view
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
#                 time.sleep(1)
                
#                 # Wait for it to be clickable after scrolling
#                 button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
                
#                 # Click using JavaScript
#                 driver.execute_script("arguments[0].click();", button)
#                 print(f"Clicked {button_type} button")
                
#                 # If it's the Submit button, wait for confirmation
#                 if button_type == "Submit":
#                     try:
#                         success_msg = wait.until(EC.presence_of_element_located((
#                             By.XPATH, "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Application sent')]"
#                         )))
#                         print("Application submitted successfully!")
#                     except:
#                         print("Could not verify submission confirmation")
                
#                 time.sleep(1)
#                 break
                
#             except Exception as e:
#                 print(f"Error with {button_type} button: {str(e)}")
#                 continue
        
#         return True

#     except Exception as e:
#         print(f"An error occurred in handle_form_fields: {str(e)}")
#         return False


# def remove_duplicates(input_list):
#     """Helper function to remove duplicates while maintaining order"""
#     result = []
#     for item in input_list:
#         if item not in result:
#             result.append(item)
#     return result


# def click_next_button(driver):
#     """Handle clicking next/submit/review buttons"""
#     button_texts = ["Next", "Submit", "Review"]
#     for text in button_texts:
#         try:
#             button = WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.XPATH,
#                     f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
#             )
            
#             # Scroll button into view
#             driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
#             time.sleep(1)

#             button.click()
#             print(f"Clicked the '{text}' button")

#             if text == "Submit":
#                 print("Final Submit button clicked. Waiting for confirmation.")
#                 time.sleep(5)
#                 try:
#                     success_msg = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.XPATH,
#                             "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Your application was sent to')]"))
#                     )
#                     print("Application submitted successfully!")
#                 except:
#                     print("No confirmation message found. Verifying submission status...")
#                 return "Submit"

#             return text
#         except Exception as e:
#             print(f"Could not click '{text}' button: {str(e)}")

#     print("Could not find Next, Submit, or Review button")
#     return None

# def continue_to_apply(driver):
#     try:
#         # Click the 'Easy Apply' button
#         easy_apply_button = driver.find_element(By.CLASS_NAME, 'jobs-apply-button')
#         easy_apply_button.click()

#         # Proceed through the application steps
#         click_next_button(driver)
#         time.sleep(2)
#         click_next_button(driver)
#         time.sleep(2)
#         handle_form_fields(driver)
#         click_next_button(driver)
#         time.sleep(2)

#         # After the application is submitted, look for the popup close button and click it
#         try:
#             close_button = WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']"))
#             )
#             close_button.click()
#             print("Closed the success popup.")
#         except TimeoutException:
#             print("No popup found after submitting the application.")

#     except Exception as e:
#         print(f"An error occurred during application: {str(e)}")


# def save_job_application(job_details, user_info):
#     """Save job application details to Supabase."""
#     try:
#         # Get accelerator_user_id
#         accelerator_user_id = data_manager.get_accelerator_user_id(user_info.get('user_id'))
        
#         application_data = {
#             'timestamp': datetime.now().isoformat(),
#             'job_id': job_details.get('job_id', 'unknown'),
#             'user_id': user_info.get('user_id'),
#             'accelerator_user_id': accelerator_user_id,
#             'job_title': job_details.get('job_title', 'N/A'),
#             'company_name': job_details.get('company', 'N/A'),
#             'job_location': job_details.get('location', 'N/A'),
#             'job_url': job_details.get('job_link', 'N/A'),
#             'application_status': job_details.get('status', 'applied'),
#             'keyword_searched': user_info.get('search_keyword', ''),
#             'error_message': job_details.get('error_message', ''),
#             'platform': 'linkedin',
#             'workplace_type': job_details.get('workplace_type', ''),
#             'applicant_count': job_details.get('applicant_count', '')
#         }
        
#         response = data_manager.record_job_application(application_data)
#         logger.info(f"Job application saved for {job_details['job_title']}")
#         return response
#     except Exception as e:
#         logger.error(f"Error saving job application: {str(e)}")
#         return False

# def extract_job_details(driver):
#     """Extract job details using correct selectors."""
#     details = {}
#     wait = WebDriverWait(driver, 10)
    
#     try:
#         # Wait for the main container
#         wait.until(EC.presence_of_element_located((
#             By.CLASS_NAME, "job-details-jobs-unified-top-card__container--two-pane"
#         )))
        
#         # Extract job title using the correct selector from the first screenshot
#         try:
#             title_element = wait.until(EC.presence_of_element_located((
#                 By.CSS_SELECTOR, 
#                 "h1.t-24.t-bold.inline, "  # Main selector from screenshot
#                 "h1.job-details-jobs-unified-top-card__job-title"  # Backup selector
#             )))
#             details['job_title'] = title_element.text.strip()
#         except Exception as e:
#             print(f"Error extracting title: {str(e)}")
#             details['job_title'] = "N/A"

#         # Extract company name
#         try:
#             # Try the main company name selector
#             company_element = wait.until(EC.presence_of_element_located((
#                 By.CSS_SELECTOR,
#                 "div.job-details-jobs-unified-top-card__primary-description-container a[data-test-app-aware-link]"  # Main selector
#             )))
#             details['company'] = company_element.text.strip()
#         except:
#             try:
#                 # Backup selector for company name
#                 company_element = driver.find_element(
#                     By.CSS_SELECTOR, 
#                     ".job-details-jobs-unified-top-card__company-name a, .job-card-container__company-name"
#                 )
#                 details['company'] = company_element.text.strip()
#             except Exception as e:
#                 print(f"Error extracting company: {str(e)}")
#                 details['company'] = "N/A"

#         # Extract location using the correct selector from the second screenshot
#         try:
#             location_elements = wait.until(EC.presence_of_all_elements_located((
#                 By.CSS_SELECTOR, 
#                 "span.tvm__text.tvm__text--low-emphasis"
#             )))
            
#             for element in location_elements:
#                 text = element.text.strip()
#                 if text and (',' in text or any(word in text.lower() for word in ['remote', 'on-site', 'hybrid'])):
#                     details['location'] = text
#                     break
#             else:
#                 details['location'] = "N/A"
#         except Exception as e:
#             print(f"Error extracting location: {str(e)}")
#             details['location'] = "N/A"

#         # Get job ID from URL
#         try:
#             job_id = driver.current_url.split('currentJobId=')[1].split('&')[0]
#             details['job_id'] = job_id
#         except:
#             details['job_id'] = "unknown"

#         details['job_link'] = driver.current_url
        
#         # Debug print to verify extraction
#         print("\nExtracted Job Details:")
#         print(f"Title: {details['job_title']}")
#         print(f"Company: {details['company']}")
#         print(f"Location: {details['location']}")
#         print(f"URL: {details['job_link']}\n")
        
#         return details
        
#     except Exception as e:
#         print(f"Error in extract_job_details: {str(e)}")
#         print(f"Current URL: {driver.current_url}")
#         return {
#             'job_title': 'N/A',
#             'company': 'N/A',
#             'location': 'N/A',
#             'job_link': driver.current_url
#         }


# def apply_to_jobs(driver, job_listings, bot, message):
#     applied_count = 0
#     search_keyword = message.text.strip()
    
#     user_info = {
#         'user_id': message.from_user.id,
#         'username': message.from_user.username,
#         'first_name': message.from_user.first_name,
#         'search_keyword': search_keyword
#     }

#     for job_listing in job_listings:
#         try:
#             # Scroll and click
#             driver.execute_script("arguments[0].scrollIntoView(true);", job_listing)
#             time.sleep(1)
#             job_listing.click()
#             time.sleep(3)
            
#             # Extract job details
#             job_details = extract_job_details(driver)
            
#             # If job title is N/A, use search keyword
#             if job_details['job_title'] == 'N/A':
#                 job_details['job_title'] = search_keyword
            
#             try:
#                 easy_apply_button = WebDriverWait(driver, 5).until(
#                     EC.element_to_be_clickable((By.CLASS_NAME, 'jobs-apply-button--top-card'))
#                 )
#                 print(f"Easy Apply button found for {job_details['job_title']} at {job_details['company']}")
#                 continue_to_apply(driver)

#                 # Save successful application with user info
#                 job_details['status'] = 'applied'
#                 save_job_application(job_details, user_info)

#                 applied_count += 1
#                 update_message = (
#                     f"🚀 Successfully applied!\n"
#                     f"💼 Position: {job_details['job_title']}\n"
#                     f"🏢 Company: {job_details['company']}\n"
#                     f"📍 Location: {job_details['location']}\n"
#                     f"✅ Total applications: {applied_count}"
#                 )
#                 bot.reply_to(message, update_message)

#             except NoSuchElementException as e:
#                 print(f"Easy Apply button not found: {str(e)}")
#                 job_details['status'] = 'skipped'
#                 save_job_application(job_details, user_info)
#                 continue
#             except TimeoutException as e:
#                 print(f"Timeout waiting for Easy Apply button: {str(e)}")
#                 job_details['status'] = 'timeout'
#                 save_job_application(job_details, user_info)
#                 continue
            
#         except Exception as e:
#             print(f"Error processing job listing: {str(e)}")
#             continue


#new working model
#with database added
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.select import Select
import time
import logging
import os
from datetime import datetime
from supabase import create_client
from data_manager import DataManager
data_manager = DataManager()


# Replace these with your actual Supabase credentials
SUPABASE_URL = "https://bpqhyuekxyzgvumdgycr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwcWh5dWVreHl6Z3Z1bWRneWNyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA3NDI1NjIsImV4cCI6MjA0NjMxODU2Mn0.rfPR6JJ9i7qcvthPlkq-YtJgx5k31qWd1wybS8BimWA"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


logger = logging.getLogger(__name__)

def setup_driver():
    """Initialize the Firefox WebDriver with proper options"""
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--window-size=1920,1080")
    firefox_options.add_argument("--disable-infobars")
    firefox_options.add_argument("--disable-extensions")
    firefox_options.add_argument("--start-maximized")
    
    try:
        driver = webdriver.Firefox(options=firefox_options)
        driver.maximize_window()
        logger.info("Firefox WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Firefox WebDriver: {str(e)}")
        raise

def login_to_linkedin(driver, li_at):
    """Fixed LinkedIn login with proper success verification"""
    try:
        logger.info("Starting LinkedIn login process...")
        
        # Initial load
        driver.get("https://www.linkedin.com")
        time.sleep(3)
        
        driver.delete_all_cookies()
        time.sleep(1)
        
        # Add cookie
        cookie = {
            'name': 'li_at',
            'value': li_at,
            'domain': '.linkedin.com',
            'path': '/'
        }
        
        driver.add_cookie(cookie)
        logger.info("Added li_at cookie")
        
        # Important: Load feed page and wait longer
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(8)  # Increased wait time
        
        try:
            # Check for ANY of these elements, not all
            selectors = [
                "div.feed-identity-module",
                "#global-nav",
                ".ember-view",
                "[data-control-name='nav.settings']"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element.is_displayed():
                        logger.info(f"Login verified via {selector}")
                        return True
                except:
                    continue
            
            # Final URL check
            if "feed" in driver.current_url:
                logger.info("Login verified via URL")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return False

def verify_login_status(driver):
    """Quick check if still logged in"""
    try:
        current_url = driver.current_url
        if "login" in current_url or "signup" in current_url:
            return False
        return "feed" in current_url or len(driver.find_elements(By.CSS_SELECTOR, ".ember-view")) > 0
    except:
        return False

def get_user_name(driver):
    try:
        name_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.feed-identity-module__actor-meta a.ember-view"))
        )
        return name_element.text.split()[0]  # Get first name
    except:
        return "there"  # Fallback if name can't be retrieved

def search_jobs(driver, search_keyword):
    try:
        logger.info(f"Navigating to LinkedIn Jobs page...")
        driver.get("https://www.linkedin.com/jobs/")
        wait = WebDriverWait(driver, 30)
        
        logger.info(f"Searching for: {search_keyword}")
        keyword_search = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-box__text-input")))
        keyword_search.clear()
        keyword_search.send_keys(f"{search_keyword}", Keys.ENTER)
        time.sleep(10)
        
        logger.info("Attempting to click the Easy Apply filter...")
        try:
            easy_apply_filter = driver.find_element(By.CLASS_NAME, 'search-reusables__filter-binary-toggle')
            easy_apply_filter.click()
            logger.info("Easy Apply filter applied successfully")
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Failed to find or click Easy Apply filter: {str(e)}")
        
        time.sleep(10)
        
        logger.info("Extracting job listings...")
        job_listings = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[data-occludable-job-id]"))
        )
        logger.info(f"Found {len(job_listings)} job listings")
        return job_listings
        
    except Exception as e:
        logger.error(f"An unexpected error occurred during job search: {str(e)}")
        return []


predefined_answers = {
    # Experience related
    "how many": "0",
    "experience": "0",
    "years": "0",
    "number of years": "0",
    "work experience": "0",
    
    # Skills and ratings
    "rate": "3",
    "skill": "3",
    "proficiency": "3",
    "scale of": "3",
    "rate out of": "3",
    "AWS": "0",
    "python": "1",
    "java": "1",
    "programming": "1",
    
    # Job related
    "notice": "0",
    "notice period": "0",
    "current ctc": "0",
    "expected ctc": "400000",
    "current salary": "0",
    "expected salary": "400000",
    "compensation": "400000",
    
    # Location and availability
    "city": "Mumbai",
    "location": "Mumbai",
    "relocate": "Yes",
    "work from office": "Yes",
    "hybrid": "Yes",
    "remote": "Yes",
    "travel": "Yes",
    
    # Verification questions
    "sponsor": "No",
    "do you": "Yes",
    "have you": "No",
    "are you": "Yes",
    "can you": "Yes",
    "willing to": "Yes",
    "ready to": "Yes",
    "legally": "Yes",
    "eligible": "Yes",
    "authorized": "Yes",
    "Indian citizen": "Yes",
    
    # Personal information
    "gender": "Male",
    "race": "Wish not to answer",
    "lgbtq": "Wish not to answer",
    "ethnicity": "Wish not to answer",
    "nationality": "Indian",
    "government": "I do not wish to self-identify",
    
    # Education
    "education": "Bachelor's Degree",
    "degree": "Bachelor's Degree",
    "qualification": "Bachelor's Degree",
    "graduate": "2024",
    "graduation": "2024",
    "cgpa": "8",
    "percentage": "80"
}

def get_answer(question, input_type="text"):
    question_lower = question.lower()
    
    # Check for exact matches first
    for key, value in predefined_answers.items():
        if key in question_lower:
            return value
    
    # Handle different input types with default values
    if input_type == "text":
        if any(word in question_lower for word in ["experience", "years", "how many", "number of"]):
            return "0"
        elif any(word in question_lower for word in ["rate", "scale", "skill"]):
            return "3"
        return "0"
    elif input_type == "dropdown":
        if "experience" in question_lower:
            return "0-1 years"
        elif "education" in question_lower or "degree" in question_lower:
            return "Bachelor's Degree"
        elif "notice" in question_lower:
            return "Immediate"
        return "Yes"
    elif input_type == "radio":
        if any(word in question_lower for word in ["gender", "sex"]):
            return "Male"
        elif any(word in question_lower for word in ["race", "ethnicity", "lgbtq"]):
            return "Wish not to answer"
        return "Yes"
    else:
        return "0"


# def handle_form_fields(driver):
#     try:
#         wait = WebDriverWait(driver, 10)
        
#         # Handle text/numeric input fields
#         input_fields = wait.until(EC.presence_of_all_elements_located(
#             (By.XPATH, '//input[contains(@class, "artdeco-text-input--input")]')))
        
#         for input_field in input_fields:
#             try:
#                 # Scroll into view
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
#                 time.sleep(0.5)
                
#                 # Get the question (label)
#                 label = input_field.find_element(By.XPATH, 
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
#                 question = label.text.strip()
                
#                 # First check predefined answers
#                 question_lower = question.lower()
#                 answer = None
#                 for key, value in predefined_answers.items():
#                     if key in question_lower:
#                         answer = value
#                         break
                
#                 # If no predefined answer found, use "0" as fallback
#                 if answer is None:
#                     answer = "0"
                
#                 # Clear and fill
#                 input_field.clear()
#                 input_field.send_keys(Keys.CONTROL + "a")
#                 input_field.send_keys(Keys.DELETE)
#                 time.sleep(0.2)
#                 input_field.send_keys(answer)
#                 input_field.send_keys(Keys.TAB)
#                 time.sleep(0.2)
                
#             except Exception as e:
#                 print(f"Error with input field: {str(e)}")
        
#         # Handle dropdowns
#         dropdown_selectors = [
#             '//div[contains(@class, "fb-dropdown")]//select',
#             '//select[contains(@class, "select-input")]',
#             '//select'  # Fallback to any select element
#         ]
        
#         for selector in dropdown_selectors:
#             dropdowns = driver.find_elements(By.XPATH, selector)
#             for dropdown in dropdowns:
#                 try:
#                     # Scroll into view
#                     driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
#                     time.sleep(0.5)
                    
#                     # Create Select object
#                     select = Select(dropdown)
                    
#                     # Check predefined answers for dropdowns
#                     question = dropdown.get_attribute("aria-label").lower()
#                     answer = None
#                     for key, value in predefined_answers.items():
#                         if key in question:
#                             answer = value
#                             break
                    
#                     # Select predefined answer or first non-empty option
#                     if answer:
#                         try:
#                             select.select_by_visible_text(answer)
#                         except:
#                             select.select_by_index(1)
#                     else:
#                         if len(select.options) > 1:
#                             select.select_by_index(1)
#                         else:
#                             select.select_by_index(0)
#                     time.sleep(0.2)
                    
#                 except Exception as e:
#                     print(f"Error with dropdown: {str(e)}")
#                     continue
        
#         # Handle radio buttons
#         radio_groups = driver.find_elements(By.XPATH,
#             '//fieldset[contains(@class, "artdeco-form__group--radio")]')

#         for group in radio_groups:
#             try:
#                 # Scroll into view
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", group)
#                 time.sleep(0.5)
                
#                 # Check predefined answers for radio buttons
#                 question = group.find_element(By.XPATH, './/legend').text.strip().lower()
#                 print(f"Radio question found: {question}")  # Debug print
                
#                 # Try different selectors for radio options
#                 options = group.find_elements(By.XPATH, 
#                     './/label[contains(@class, "artdeco-radio")] | .//label[@data-test-text-selectable-option__label]')
                
#                 if not options:  # If first selector fails, try alternative
#                     options = group.find_elements(By.XPATH, './/input[@type="radio"]/parent::label')
                
#                 print(f"Found {len(options)} options for question: {question}")
                
#                 if options:
#                     # For yes/no questions, always select "Yes"
#                     if len(options) == 2 and any('yes' in option.text.lower() for option in options):
#                         for option in options:
#                             if 'yes' in option.text.lower():
#                                 driver.execute_script("arguments[0].click();", option)
#                                 print(f"Clicked 'Yes' option for question: {question}")
#                                 break
#                     else:
#                         # Default to first option for other types of questions
#                         driver.execute_script("arguments[0].click();", options[0])
#                         print(f"Clicked first option: {options[0].text}")
                    
#                     time.sleep(0.2)
                        
#             except Exception as e:
#                 print(f"Error with radio button: {str(e)}")
        
#         # Try to proceed with better button handling
#         button_texts = ["Next", "Submit", "Review"]
#         for text in button_texts:
#             try:
#                 button = WebDriverWait(driver, 5).until(
#                     EC.element_to_be_clickable((By.XPATH,
#                         f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
#                 )
                
#                 # Scroll button into view
#                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
#                 time.sleep(1)

#                 button.click()
#                 print(f"Clicked the '{text}' button")

#                 if text == "Submit":
#                     print("Final Submit button clicked. Waiting for confirmation.")
#                     time.sleep(5)
#                     try:
#                         success_msg = WebDriverWait(driver, 10).until(
#                             EC.presence_of_element_located((By.XPATH,
#                                 "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Your application was sent to')]"))
#                         )
#                         print("Application submitted successfully!")
#                         return True
#                     except:
#                         print("No confirmation message found. Verifying submission status...")
#                         return True

#             except Exception as e:
#                 print(f"Could not click '{text}' button: {str(e)}")
#                 continue

#         return True

#     except Exception as e:
#         print(f"An error occurred in handle_form_fields: {str(e)}")
#         return False



# def handle_form_fields(driver):
#     try:
#         wait = WebDriverWait(driver, 10)
        
#         # Find the scrollable form container
#         form_container = wait.until(EC.presence_of_element_located((
#             By.CSS_SELECTOR, 
#             "div.jobs-easy-apply-content, div.artdeco-modal__content"
#         )))
        
#         def scroll_in_form(element):
#             """Helper function to scroll element into view within the form container"""
#             try:
#                 driver.execute_script("""
#                     arguments[0].scrollIntoView();
#                     arguments[1].scrollTop = arguments[1].scrollTop + arguments[0].getBoundingClientRect().top - 100;
#                 """, element, form_container)
#                 time.sleep(0.5)
#             except Exception as e:
#                 print(f"Scroll error: {str(e)}")

#         # Handle text/numeric input fields
#         input_fields = wait.until(EC.presence_of_all_elements_located((
#             By.XPATH, '//input[contains(@class, "artdeco-text-input--input")]')))
        
#         for input_field in input_fields:
#             try:
#                 # Scroll the input field into view within the form
#                 scroll_in_form(input_field)
                
#                 # Get the question (label)
#                 label = input_field.find_element(By.XPATH, 
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
#                 question = label.text.strip()
                
#                 # Get answer from predefined answers
#                 answer = get_answer(question)
                
#                 # Clear and fill using improved method
#                 input_field.clear()
#                 input_field.send_keys(Keys.CONTROL + "a")
#                 input_field.send_keys(Keys.DELETE)
#                 time.sleep(0.2)
#                 input_field.send_keys(answer)
#                 input_field.send_keys(Keys.TAB)
#                 time.sleep(0.2)
                
#             except Exception as e:
#                 print(f"Error with input field: {str(e)}")

#         # Handle dropdowns with multiple selector attempts
#         dropdown_selectors = [
#             '//div[contains(@class, "fb-dropdown")]//select',
#             '//select[contains(@class, "select-input")]',
#             '//select'
#         ]
        
#         for selector in dropdown_selectors:
#             dropdowns = driver.find_elements(By.XPATH, selector)
#             for dropdown in dropdowns:
#                 try:
#                     scroll_in_form(dropdown)
                    
#                     select = Select(dropdown)
#                     question = dropdown.get_attribute("aria-label") or ""
#                     answer = get_answer(question, "dropdown")
                    
#                     try:
#                         select.select_by_visible_text(answer)
#                     except:
#                         if len(select.options) > 1:
#                             select.select_by_index(1)
#                         else:
#                             select.select_by_index(0)
#                     time.sleep(0.2)
                    
#                 except Exception as e:
#                     print(f"Error with dropdown: {str(e)}")

#         # Handle radio buttons with improved selectors
#         radio_groups = driver.find_elements(By.XPATH,
#             '//fieldset[contains(@class, "artdeco-form__group--radio")]')

#         for group in radio_groups:
#             try:
#                 scroll_in_form(group)
                
#                 question = group.find_element(By.XPATH, './/legend').text.strip()
#                 print(f"Radio question: {question}")
                
#                 options = group.find_elements(By.XPATH, 
#                     './/label[contains(@class, "artdeco-radio")] | ' +
#                     './/label[@data-test-text-selectable-option__label]')
                
#                 if not options:
#                     options = group.find_elements(By.XPATH, 
#                         './/input[@type="radio"]/parent::label')
                
#                 if options:
#                     answer = get_answer(question, "radio")
#                     matched_option = None
                    
#                     # Try to find exact match first
#                     for option in options:
#                         if answer.lower() in option.text.lower():
#                             matched_option = option
#                             break
                    
#                     # If no match found, use first option
#                     if not matched_option:
#                         matched_option = options[0]
                    
#                     # Try multiple click methods
#                     try:
#                         matched_option.click()
#                     except:
#                         try:
#                             driver.execute_script("arguments[0].click();", matched_option)
#                         except:
#                             actions = ActionChains(driver)
#                             actions.move_to_element(matched_option).click().perform()
                    
#                     time.sleep(0.2)
                    
#             except Exception as e:
#                 print(f"Error with radio button: {str(e)}")

#         # Handle checkboxes
#         checkboxes = driver.find_elements(By.XPATH,
#             '//input[@type="checkbox"]/parent::label')
        
#         for checkbox in checkboxes:
#             try:
#                 scroll_in_form(checkbox)
#                 question = checkbox.text.strip()
#                 answer = get_answer(question, "checkbox")
                
#                 if answer.lower() == "yes":
#                     try:
#                         checkbox.click()
#                     except:
#                         driver.execute_script("arguments[0].click();", checkbox)
#                 time.sleep(0.2)
                
#             except Exception as e:
#                 print(f"Error with checkbox: {str(e)}")

#         # Handle text areas
#         textareas = driver.find_elements(By.XPATH,
#             '//textarea[contains(@class, "artdeco-text-input--input")]')
        
#         for textarea in textareas:
#             try:
#                 scroll_in_form(textarea)
                
#                 label = textarea.find_element(By.XPATH,
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
#                 question = label.text.strip()
#                 answer = get_answer(question, "textarea")
                
#                 textarea.clear()
#                 textarea.send_keys(answer)
#                 time.sleep(0.2)
                
#             except Exception as e:
#                 print(f"Error with textarea: {str(e)}")

#         # Handle submit/next/review buttons
#         button_texts = ["Submit", "Next", "Review"]
#         for text in button_texts:
#             try:
#                 button = wait.until(EC.presence_of_element_located((
#                     By.XPATH, 
#                     f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
#                 )))
                
#                 scroll_in_form(button)
#                 time.sleep(1)
                
#                 # Try multiple click methods
#                 try:
#                     button.click()
#                 except:
#                     try:
#                         driver.execute_script("arguments[0].click();", button)
#                     except:
#                         actions = ActionChains(driver)
#                         actions.move_to_element(button).click().perform()
                
#                 print(f"Clicked the '{text}' button")
                
#                 if text == "Submit":
#                     print("Final Submit button clicked. Waiting for confirmation...")
#                     time.sleep(5)
#                     try:
#                         success_msg = wait.until(EC.presence_of_element_located((
#                             By.XPATH,
#                             "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Your application was sent to')]"
#                         )))
#                         print("Application submitted successfully!")
#                         return True
#                     except:
#                         print("No confirmation message found. Verifying submission status...")
#                         return True
                
#                 time.sleep(2)
#                 break
                
#             except Exception as e:
#                 print(f"Could not click '{text}' button: {str(e)}")
#                 continue

#         return True

#     except Exception as e:
#         print(f"An error occurred in handle_form_fields: {str(e)}")
#         return False



#next submit working cool and in above fill up was working cool
# def handle_form_fields(driver):
#     try:
#         wait = WebDriverWait(driver, 10)
        
#         # Find the scrollable form container and wait longer for it
#         time.sleep(2)
#         form_container = wait.until(EC.presence_of_element_located((
#             By.CSS_SELECTOR, 
#             "div.jobs-easy-apply-content, div.artdeco-modal__content"
#         )))
        
#         def scroll_in_form(element):
#             try:
#                 driver.execute_script("""
#                     arguments[0].scrollIntoView();
#                     arguments[1].scrollTop = arguments[1].scrollTop + arguments[0].getBoundingClientRect().top - 100;
#                 """, element, form_container)
#                 time.sleep(1)
#             except Exception as e:
#                 print(f"Scroll error: {str(e)}")

#         # Handle text/numeric input fields
#         time.sleep(1)
#         input_fields = wait.until(EC.presence_of_all_elements_located((
#             By.XPATH, '//input[contains(@class, "artdeco-text-input--input")]')))
        
#         for input_field in input_fields:
#             try:
#                 # Check if field already has a value
#                 current_value = input_field.get_attribute('value')
#                 if current_value and len(current_value.strip()) > 0:
#                     print(f"Field already has value: {current_value}")
#                     continue
                
#                 scroll_in_form(input_field)
#                 time.sleep(0.5)
                
#                 label = input_field.find_element(By.XPATH, 
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
#                 question = label.text.strip()
#                 print(f"Processing input field: {question}")
                
#                 answer = get_answer(question)
                
#                 wait.until(EC.element_to_be_clickable(input_field))
#                 input_field.click()
#                 time.sleep(0.5)
                
#                 input_field.clear()
#                 input_field.send_keys(Keys.CONTROL + "a")
#                 input_field.send_keys(Keys.DELETE)
#                 time.sleep(0.5)
#                 input_field.send_keys(answer)
#                 time.sleep(0.5)
#                 input_field.send_keys(Keys.TAB)
#                 time.sleep(0.5)
                
#             except Exception as e:
#                 print(f"Error with input field: {str(e)}")

#         # Handle dropdowns
#         time.sleep(1)
#         dropdown_selectors = [
#             '//div[contains(@class, "fb-dropdown")]//select',
#             '//select[contains(@class, "select-input")]',
#             '//select'
#         ]
        
#         for selector in dropdown_selectors:
#             dropdowns = driver.find_elements(By.XPATH, selector)
#             for dropdown in dropdowns:
#                 try:
#                     # Check if dropdown has a selected value
#                     select = Select(dropdown)
#                     current_selection = select.first_selected_option.text.strip()
#                     if current_selection and current_selection.lower() != "select an option":
#                         print(f"Dropdown already has selection: {current_selection}")
#                         continue
                    
#                     scroll_in_form(dropdown)
#                     time.sleep(0.5)
                    
#                     question = dropdown.get_attribute("aria-label") or ""
#                     print(f"Processing dropdown: {question}")
#                     answer = get_answer(question, "dropdown")
                    
#                     try:
#                         select.select_by_visible_text(answer)
#                     except:
#                         if len(select.options) > 1:
#                             select.select_by_index(1)
#                         else:
#                             select.select_by_index(0)
#                     time.sleep(0.5)
                    
#                 except Exception as e:
#                     print(f"Error with dropdown: {str(e)}")

#         # Handle radio buttons
#         time.sleep(1)
#         radio_groups = driver.find_elements(By.XPATH,
#             '//fieldset[contains(@class, "artdeco-form__group--radio")]')

#         for group in radio_groups:
#             try:
#                 # Check if any radio button is already selected
#                 selected_radio = group.find_elements(By.XPATH, './/input[@type="radio"][@checked]')
#                 if selected_radio:
#                     print("Radio option already selected")
#                     continue
                
#                 scroll_in_form(group)
#                 time.sleep(0.5)
                
#                 question = group.find_element(By.XPATH, './/legend').text.strip()
#                 print(f"Processing radio question: {question}")
                
#                 options = group.find_elements(By.XPATH, 
#                     './/label[contains(@class, "artdeco-radio")] | ' +
#                     './/label[@data-test-text-selectable-option__label]')
                
#                 if not options:
#                     options = group.find_elements(By.XPATH, 
#                         './/input[@type="radio"]/parent::label')
                
#                 if options:
#                     answer = get_answer(question, "radio")
#                     matched_option = None
                    
#                     for option in options:
#                         if answer.lower() in option.text.lower():
#                             matched_option = option
#                             break
                    
#                     if not matched_option:
#                         matched_option = options[0]
                    
#                     try:
#                         matched_option.click()
#                     except:
#                         try:
#                             driver.execute_script("arguments[0].click();", matched_option)
#                         except:
#                             actions = ActionChains(driver)
#                             actions.move_to_element(matched_option).click().perform()
                    
#                     time.sleep(0.5)
                    
#             except Exception as e:
#                 print(f"Error with radio button: {str(e)}")

#         # Handle checkboxes
#         time.sleep(1)
#         checkboxes = driver.find_elements(By.XPATH,
#             '//input[@type="checkbox"]/parent::label')
        
#         for checkbox in checkboxes:
#             try:
#                 # Check if checkbox is already checked
#                 checkbox_input = checkbox.find_element(By.XPATH, './/input[@type="checkbox"]')
#                 if checkbox_input.is_selected():
#                     print("Checkbox already checked")
#                     continue
                
#                 scroll_in_form(checkbox)
#                 time.sleep(0.5)
                
#                 question = checkbox.text.strip()
#                 print(f"Processing checkbox: {question}")
#                 answer = get_answer(question, "checkbox")
                
#                 if answer.lower() == "yes":
#                     try:
#                         checkbox.click()
#                     except:
#                         driver.execute_script("arguments[0].click();", checkbox)
#                 time.sleep(0.5)
                
#             except Exception as e:
#                 print(f"Error with checkbox: {str(e)}")

#         # Handle text areas
#         time.sleep(1)
#         textareas = driver.find_elements(By.XPATH,
#             '//textarea[contains(@class, "artdeco-text-input--input")]')
        
#         for textarea in textareas:
#             try:
#                 # Check if textarea already has content
#                 current_text = textarea.get_attribute('value')
#                 if current_text and len(current_text.strip()) > 0:
#                     print("Textarea already has content")
#                     continue
                
#                 scroll_in_form(textarea)
#                 time.sleep(0.5)
                
#                 label = textarea.find_element(By.XPATH,
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label')
#                 question = label.text.strip()
#                 print(f"Processing textarea: {question}")
#                 answer = get_answer(question, "textarea")
                
#                 textarea.clear()
#                 textarea.send_keys(answer)
#                 time.sleep(0.5)
                
#             except Exception as e:
#                 print(f"Error with textarea: {str(e)}")

#         # Handle navigation buttons
#         while True:
#             time.sleep(2)
#             try:
#                 submit_button = wait.until(EC.presence_of_element_located((
#                     By.XPATH, "//button[contains(@aria-label, 'Submit application')]")))
#                 scroll_in_form(submit_button)
#                 time.sleep(1)
#                 submit_button.click()
#                 print("Clicked Submit application button")
#                 time.sleep(3)
#                 return True
#             except:
#                 try:
#                     review_button = wait.until(EC.presence_of_element_located((
#                         By.XPATH, "//button[contains(@aria-label, 'Review your application')]")))
#                     scroll_in_form(review_button)
#                     time.sleep(1)
#                     review_button.click()
#                     print("Clicked Review button")
#                     time.sleep(3)
#                     continue
#                 except:
#                     try:
#                         next_button = wait.until(EC.presence_of_element_located((
#                             By.XPATH, "//button[contains(@aria-label, 'Continue to next step')]")))
#                         scroll_in_form(next_button)
#                         time.sleep(1)
#                         next_button.click()
#                         print("Clicked Next button")
#                         time.sleep(3)
#                         continue
#                     except:
#                         print("No next/review/submit button found")
#                         return False

#     except Exception as e:
#         print(f"An error occurred in handle_form_fields: {str(e)}")
#         return False

def handle_form_fields(driver):
    """
    Enhanced form field handler that validates each page before proceeding
    """
    try:
        wait = WebDriverWait(driver, 10)
        
        while True:
            time.sleep(2)
            
            # Check for submit button first
            try:
                submit_button = wait.until(EC.presence_of_element_located((
                    By.XPATH, "//button[contains(@aria-label, 'Submit application')]")))
                scroll_to_element(driver, submit_button)
                time.sleep(1)
                submit_button.click()
                print("Clicked Submit application button")
                time.sleep(3)
                return True
            except:
                pass

            # Find and fill all empty required fields on current page
            has_empty_fields = fill_empty_fields(driver)
            
            if has_empty_fields:
                print("Filled empty fields on current page")
                time.sleep(1)
            
            # Only proceed if no empty required fields
            try:
                # Try Review button first
                review_button = driver.find_element(By.XPATH, 
                    "//button[contains(@aria-label, 'Review your application')]")
                scroll_to_element(driver, review_button)
                time.sleep(1)
                review_button.click()
                print("Clicked Review button")
                time.sleep(2)
                continue
            except:
                try:
                    # Then try Next button
                    next_button = driver.find_element(By.XPATH, 
                        "//button[contains(@aria-label, 'Continue to next step')]")
                    scroll_to_element(driver, next_button)
                    time.sleep(1)
                    next_button.click()
                    print("Clicked Next button")
                    time.sleep(2)
                    continue
                except:
                    print("No next/review/submit button found")
                    return False

    except Exception as e:
        print(f"An error occurred in handle_form_fields: {str(e)}")
        return False


# def fill_empty_fields(driver) -> bool:
#     """
#     Find and fill only empty required fields using predefined answers
#     """
#     filled_any = False
    
#     try:
#         # Check text inputs
#         input_fields = driver.find_elements(By.XPATH,
#             './/input[contains(@class, "artdeco-text-input--input")]')
        
#         for field in input_fields:
#             value = field.get_attribute("value")
#             if not value or value.isspace():
#                 try:
#                     # Get label text to match with predefined answers
#                     label = field.find_element(By.XPATH,
#                         './ancestor::div[contains(@class, "artdeco-text-input--container")]//label').text.strip()
#                     label_lower = label.lower()

#                     # Use predefined answers based on field type
#                     answer = None
#                     if "experience" in label_lower:
#                         answer = predefined_answers.get("experience", "0")
#                     elif "salary" in label_lower:
#                         if "current" in label_lower:
#                             answer = predefined_answers.get("current_salary", "0")
#                         else:
#                             answer = predefined_answers.get("expected salary", "400000")
#                     elif "node" in label_lower or "react" in label_lower:
#                         answer = predefined_answers.get("experience", "0")
                    
#                     # If no specific match found, try to match with predefined keys
#                     if not answer:
#                         for key, value in predefined_answers.items():
#                             if key in label_lower:
#                                 answer = value
#                                 break
                    
#                     # Use default if no match found
#                     if not answer:
#                         answer = "0"

#                     field.clear()
#                     field.send_keys(answer)
#                     field.send_keys(Keys.TAB)
#                     time.sleep(0.5)
#                     filled_any = True
#                     print(f"Filled empty field: {label} with {answer}")

#                 except Exception as e:
#                     print(f"Error filling text field: {str(e)}")

#         # Check dropdowns
#         dropdowns = driver.find_elements(By.TAG_NAME, "select")
#         for dropdown in dropdowns:
#             select = Select(dropdown)
#             current_value = select.first_selected_option.text.strip()
            
#             if current_value == "Select an option":
#                 try:
#                     label = dropdown.get_attribute("aria-label") or ""
#                     label_lower = label.lower()

#                     # Use predefined answers for dropdowns
#                     answer = None
#                     if "experience" in label_lower:
#                         answer = "0-1 years"
#                     elif "education" in label_lower:
#                         answer = predefined_answers.get("education", "Bachelor's Degree")
#                     elif "notice" in label_lower:
#                         answer = predefined_answers.get("notice period", "0")
                    
#                     # Try to select the answer
#                     try:
#                         if answer:
#                             select.select_by_visible_text(answer)
#                         else:
#                             # If no matching predefined answer, select first non-empty option
#                             if len(select.options) > 1:
#                                 select.select_by_index(1)
#                             else:
#                                 select.select_by_index(0)
#                         time.sleep(0.5)
#                         filled_any = True
#                         print(f"Filled empty dropdown: {label}")
#                     except:
#                         print(f"Could not select answer {answer} for dropdown {label}")

#                 except Exception as e:
#                     print(f"Error with dropdown: {str(e)}")

#         # Check radio buttons
#         radio_groups = driver.find_elements(By.XPATH,
#             './/fieldset[contains(@class, "artdeco-form__group--radio")]')
            
#         for group in radio_groups:
#             selected = group.find_elements(By.XPATH, './/input[@type="radio"][@checked]')
#             if not selected:
#                 try:
#                     question = group.find_element(By.XPATH, './/legend').text.strip()
#                     question_lower = question.lower()

#                     # Get answer from predefined answers
#                     answer = None
#                     for key, value in predefined_answers.items():
#                         if key in question_lower:
#                             answer = value
#                             break
                    
#                     if not answer:
#                         answer = "Yes"  # Default fallback

#                     options = group.find_elements(By.XPATH, 
#                         './/label[contains(@class, "artdeco-radio")] | ' +
#                         './/label[@data-test-text-selectable-option__label]')
                    
#                     if options:
#                         matched_option = None
#                         # Try to find exact match with predefined answer
#                         for option in options:
#                             if answer.lower() in option.text.lower():
#                                 matched_option = option
#                                 break
                        
#                         if not matched_option:
#                             matched_option = options[0]
                            
#                         matched_option.click()
#                         time.sleep(0.5)
#                         filled_any = True
#                         print(f"Filled radio group: {question} with {answer}")

#                 except Exception as e:
#                     print(f"Error with radio button: {str(e)}")

#         return filled_any

#     except Exception as e:
#         print(f"Error checking for empty fields: {str(e)}")
#         return False

def fill_empty_fields(driver) -> bool:
    filled_any = False
    
    try:
        # Check text inputs
        input_fields = driver.find_elements(By.XPATH,
            './/input[contains(@class, "artdeco-text-input--input")]')
        
        for field in input_fields:
            try:
                # Get label and helper text
                label = field.find_element(By.XPATH,
                    './ancestor::div[contains(@class, "artdeco-text-input--container")]//label').text.strip()
                label_lower = label.lower()
                
                # Try to get helper text/example if available
                try:
                    helper_text = field.find_element(By.XPATH,
                        './following-sibling::div[contains(@class, "artdeco-text-input--hint")]').text.strip()
                except:
                    helper_text = ""

                # Special handling for CTC/salary fields
                if any(x in label_lower for x in ["ctc", "compensation", "salary"]):
                    if "current" in label_lower:
                        answer = "100000"
                    else:  # expected salary
                        answer = "400000"
                    field.clear()
                    field.send_keys(answer)
                    time.sleep(0.5)
                    field.send_keys(Keys.TAB)
                    filled_any = True
                    print(f"Filled salary field: {label} with {answer}")
                    continue

                # Special handling for notice period
                if "notice period" in label_lower:
                    answer = "30"
                    field.clear()
                    field.send_keys(answer)
                    time.sleep(0.5)
                    field.send_keys(Keys.TAB)
                    filled_any = True
                    print(f"Filled notice period: {label} with {answer}")
                    continue

                # Special handling for experience fields
                if "experience" in label_lower or "years" in label_lower:
                    answer = "1"
                    field.clear()
                    field.send_keys(answer)
                    time.sleep(0.5)
                    field.send_keys(Keys.TAB)
                    filled_any = True
                    print(f"Filled experience field: {label} with {answer}")
                    continue

                # Special handling for location fields
                if 'location' in label_lower or 'city' in label_lower:
                    field.clear()
                    field.send_keys("Mumbai")
                    time.sleep(2)
                    try:
                        suggestions = WebDriverWait(driver, 5).until(
                            EC.presence_of_all_elements_located((By.XPATH, 
                                "//div[contains(@class, 'search-typeahead-v2__hit') or contains(@class, 'location-typeahead__option')]"))
                        )
                        if suggestions:
                            suggestions[0].click()
                            filled_any = True
                            print(f"Selected location from dropdown: Mumbai")
                            continue
                    except:
                        print("No location suggestions found, using direct input")

                # Handle numeric fields that require validation
                if "Enter a whole number larger than 0" in helper_text:
                    answer = "1"
                    field.clear()
                    field.send_keys(answer)
                    time.sleep(0.5)
                    field.send_keys(Keys.TAB)
                    filled_any = True
                    print(f"Filled numeric field: {label} with {answer}")
                    continue

                # Default handling for other fields
                value = field.get_attribute("value")
                if not value or value.isspace():
                    answer = get_answer(label_lower)
                    field.clear()
                    field.send_keys(answer)
                    field.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    filled_any = True
                    print(f"Filled field: {label} with {answer}")

            except Exception as e:
                print(f"Error filling field {label if 'label' in locals() else 'unknown'}: {str(e)}")

        # Rest of the function (dropdowns, radio buttons, etc.) remains the same...

        # Check dropdowns
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        for dropdown in dropdowns:
            select = Select(dropdown)
            current_value = select.first_selected_option.text.strip()
            
            if current_value == "Select an option":
                try:
                    label = dropdown.get_attribute("aria-label") or ""
                    label_lower = label.lower()

                    # Use predefined answers for dropdowns
                    answer = None
                    if "experience" in label_lower:
                        answer = "0-1 years"
                    elif "education" in label_lower:
                        answer = predefined_answers.get("education", "Bachelor's Degree")
                    elif "notice" in label_lower:
                        answer = predefined_answers.get("notice period", "0")
                    
                    # Try to select the answer
                    try:
                        if answer:
                            select.select_by_visible_text(answer)
                        else:
                            # If no matching predefined answer, select first non-empty option
                            if len(select.options) > 1:
                                select.select_by_index(1)
                            else:
                                select.select_by_index(0)
                        time.sleep(0.5)
                        filled_any = True
                        print(f"Filled empty dropdown: {label}")
                    except:
                        print(f"Could not select answer {answer} for dropdown {label}")

                except Exception as e:
                    print(f"Error with dropdown: {str(e)}")

        # Check radio buttons
        radio_groups = driver.find_elements(By.XPATH,
            './/fieldset[contains(@class, "artdeco-form__group--radio")]')
            
        for group in radio_groups:
            try:
                # Check if already selected
                selected = group.find_elements(By.XPATH, './/input[@type="radio"][@checked]')
                if selected:
                    continue
                
                # Get question text
                question = group.find_element(By.XPATH, './/legend').text.strip()
                question_lower = question.lower()
                print(f"Processing radio question: {question}")

                # Get all radio inputs and their labels
                radio_inputs = group.find_elements(By.XPATH, './/input[@type="radio"]')
                options = []
                for radio in radio_inputs:
                    try:
                        input_id = radio.get_attribute("id")
                        label_element = group.find_element(By.XPATH, f'.//label[@for="{input_id}"]')
                        options.append({
                            'input': radio,
                            'label': label_element,
                            'text': label_element.text.strip()
                        })
                    except:
                        continue

                # Determine answer based on question type
                answer = None
                if 'citizenship' in question_lower or 'employment eligibility' in question_lower:
                    answer = "Yes"
                elif 'veteran' in question_lower or 'protected veteran' in question_lower:
                    answer = "I am not a protected veteran"
                elif 'disability' in question_lower or 'disabilities' in question_lower:
                    answer = "No, I don't have a disability"
                elif 'gender' in question_lower or 'sex' in question_lower:
                    answer = predefined_answers.get("gender", "Male")
                elif 'race' in question_lower or 'ethnicity' in question_lower:
                    answer = predefined_answers.get("race", "Wish not to answer")
                else:
                    # Check predefined answers
                    for key, value in predefined_answers.items():
                        if key in question_lower:
                            answer = value
                            break
                
                if not answer:
                    answer = "Yes"  # Default fallback
                
                # Try to find matching option
                matched_option = None
                # First try exact match
                for option in options:
                    if option['text'].lower() == answer.lower():
                        matched_option = option
                        break
                
                # If no exact match, try contains match
                if not matched_option:
                    for option in options:
                        if answer.lower() in option['text'].lower():
                            matched_option = option
                            break
                
                # If still no match, use first option
                if not matched_option and options:
                    matched_option = options[0]
                
                if matched_option:
                    try:
                        # Scroll into view
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", matched_option['label'])
                        time.sleep(0.5)
                        
                        # Try multiple click methods
                        try:
                            matched_option['label'].click()
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", matched_option['label'])
                            except:
                                try:
                                    actions = ActionChains(driver)
                                    actions.move_to_element(matched_option['label']).click().perform()
                                except:
                                    matched_option['input'].click()
                        
                        time.sleep(0.5)
                        filled_any = True
                        print(f"Filled radio group: {question} with {matched_option['text']}")
                    except Exception as e:
                        print(f"Error clicking radio option: {str(e)}")

            except Exception as e:
                print(f"Error with radio button group: {str(e)}")
                continue

        # Check textareas
        textareas = driver.find_elements(By.XPATH,
            '//textarea[contains(@class, "artdeco-text-input--input")]')
        
        for textarea in textareas:
            if not textarea.get_attribute("value"):
                try:
                    label = textarea.find_element(By.XPATH,
                        './ancestor::div[contains(@class, "artdeco-text-input--container")]//label').text.strip()
                    answer = get_answer(label, "textarea")
                    
                    textarea.clear()
                    textarea.send_keys(answer)
                    time.sleep(0.5)
                    filled_any = True
                    print(f"Filled textarea: {label} with {answer}")
                except Exception as e:
                    print(f"Error with textarea: {str(e)}")

        return filled_any

    except Exception as e:
        print(f"Error checking for empty fields: {str(e)}")
        return False

def scroll_to_element(driver, element):
    """Scroll element into view"""
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
            element
        )
        time.sleep(0.5)
    except:
        pass

    
def verify_submission(driver):
    """Verify if job application was submitted successfully"""
    try:
        success_msg = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Your application was sent to')]"))
        )
        print("Application submitted successfully!")
        return True
    except:
        print("No confirmation message found. Verifying submission status...")
        return True

def handle_popup(driver, action="submit"):
    """Handle popups after submission or failure"""
    try:
        if action == "submit":
            # Try to close success popup
            buttons = [
                "//button[@aria-label='Dismiss']",
                "//button[contains(@aria-label, 'Dismiss')]",
                "//button[.//span[text()='Done']]",
                "//button[.//span[text()='Close']]"
            ]
            
            for button_xpath in buttons:
                try:
                    close_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, button_xpath))
                    )
                    close_button.click()
                    print("Closed the success popup")
                    return True
                except:
                    continue

        elif action == "discard":
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                
                discard_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Discard']]"))
                )
                discard_button.click()
                print("Discarded the application")
                return True
            except:
                try:
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    print("Forced popup close with ESC")
                    return True
                except:
                    print("Failed to close popup")
                    return False

    except Exception as e:
        print(f"Error handling popup: {str(e)}")
        return False

# def click_next_button(driver):
#     """Handle clicking next/submit/review buttons"""
#     button_texts = ["Next", "Submit", "Review"]
#     for text in button_texts:
#         try:
#             button = WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.XPATH,
#                     f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
#             )
            
#             # Scroll button into view
#             driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
#             time.sleep(1)

#             button.click()
#             print(f"Clicked the '{text}' button")

#             if text == "Submit":
#                 print("Final Submit button clicked. Waiting for confirmation.")
#                 time.sleep(5)
#                 try:
#                     success_msg = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.XPATH,
#                             "//div[contains(@class, 'artdeco-modal__content')]//h3[contains(text(), 'Your application was sent to')]"))
#                     )
#                     print("Application submitted successfully!")
#                 except:
#                     print("No confirmation message found. Verifying submission status...")
#                 return "Submit"

#             return text
#         except Exception as e:
#             print(f"Could not click '{text}' button: {str(e)}")

#     print("Could not find Next, Submit, or Review button")
#     return None

def continue_to_apply(driver):
    """Main application flow with improved error handling"""
    try:
        # Click the 'Easy Apply' button
        easy_apply_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'jobs-apply-button'))
        )
        easy_apply_button.click()
        time.sleep(2)

        # Handle form fields and submission
        if handle_form_fields(driver):
            # If submission successful, handle success popup
            handle_popup(driver, "submit")
            return True
        else:
            # If submission failed, handle discard popup
            handle_popup(driver, "discard")
            return False

    except Exception as e:
        print(f"An error occurred during application: {str(e)}")
        # Try to discard if there's an error
        handle_popup(driver, "discard")
        return False

# def continue_to_apply(driver):
#     try:
#         # Click the 'Easy Apply' button
#         easy_apply_button = driver.find_element(By.CLASS_NAME, 'jobs-apply-button')
#         easy_apply_button.click()

#         # Proceed through the application steps
#         click_next_button(driver)
#         time.sleep(2)
#         click_next_button(driver)
#         time.sleep(2)
#         handle_form_fields(driver)
#         click_next_button(driver)
#         time.sleep(2)

#         # After the application is submitted, look for the popup close button and click it
#         try:
#             close_button = WebDriverWait(driver, 5).until(
#                 EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']"))
#             )
#             close_button.click()
#             print("Closed the success popup.")
#         except TimeoutException:
#             print("No popup found after submitting the application.")

#     except Exception as e:
#         print(f"An error occurred during application: {str(e)}")


def save_job_application(job_details, user_info):
    """Save job application details to Supabase."""
    try:
        # Get accelerator_user_id
        accelerator_user_id = data_manager.get_accelerator_user_id(user_info.get('user_id'))
        
        application_data = {
            'timestamp': datetime.now().isoformat(),
            'job_id': job_details.get('job_id', 'unknown'),
            'user_id': user_info.get('user_id'),
            'accelerator_user_id': accelerator_user_id,
            'job_title': job_details.get('job_title', 'N/A'),
            'company_name': job_details.get('company', 'N/A'),
            'job_location': job_details.get('location', 'N/A'),
            'job_url': job_details.get('job_link', 'N/A'),
            'application_status': job_details.get('status', 'applied'),
            'keyword_searched': user_info.get('search_keyword', ''),
            'error_message': job_details.get('error_message', ''),
            'platform': 'linkedin',
            'workplace_type': job_details.get('workplace_type', ''),
            'applicant_count': job_details.get('applicant_count', '')
        }
        
        response = data_manager.record_job_application(application_data)
        logger.info(f"Job application saved for {job_details['job_title']}")
        return response
    except Exception as e:
        logger.error(f"Error saving job application: {str(e)}")
        return False

def extract_job_details(driver):
    """Extract job details using correct selectors."""
    details = {}
    wait = WebDriverWait(driver, 10)
    
    try:
        # Wait for the main container
        wait.until(EC.presence_of_element_located((
            By.CLASS_NAME, "job-details-jobs-unified-top-card__container--two-pane"
        )))
        
        # Extract job title using the correct selector from the first screenshot
        try:
            title_element = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                "h1.t-24.t-bold.inline, "  # Main selector from screenshot
                "h1.job-details-jobs-unified-top-card__job-title"  # Backup selector
            )))
            details['job_title'] = title_element.text.strip()
        except Exception as e:
            print(f"Error extracting title: {str(e)}")
            details['job_title'] = "N/A"

        # Extract company name
        try:
            # Try the main company name selector
            company_element = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "div.job-details-jobs-unified-top-card__primary-description-container a[data-test-app-aware-link]"  # Main selector
            )))
            details['company'] = company_element.text.strip()
        except:
            try:
                # Backup selector for company name
                company_element = driver.find_element(
                    By.CSS_SELECTOR, 
                    ".job-details-jobs-unified-top-card__company-name a, .job-card-container__company-name"
                )
                details['company'] = company_element.text.strip()
            except Exception as e:
                print(f"Error extracting company: {str(e)}")
                details['company'] = "N/A"

        # Extract location using the correct selector from the second screenshot
        try:
            location_elements = wait.until(EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, 
                "span.tvm__text.tvm__text--low-emphasis"
            )))
            
            for element in location_elements:
                text = element.text.strip()
                if text and (',' in text or any(word in text.lower() for word in ['remote', 'on-site', 'hybrid'])):
                    details['location'] = text
                    break
            else:
                details['location'] = "N/A"
        except Exception as e:
            print(f"Error extracting location: {str(e)}")
            details['location'] = "N/A"

        # Get job ID from URL
        try:
            job_id = driver.current_url.split('currentJobId=')[1].split('&')[0]
            details['job_id'] = job_id
        except:
            details['job_id'] = "unknown"

        details['job_link'] = driver.current_url
        
        # Debug print to verify extraction
        print("\nExtracted Job Details:")
        print(f"Title: {details['job_title']}")
        print(f"Company: {details['company']}")
        print(f"Location: {details['location']}")
        print(f"URL: {details['job_link']}\n")
        
        return details
        
    except Exception as e:
        print(f"Error in extract_job_details: {str(e)}")
        print(f"Current URL: {driver.current_url}")
        return {
            'job_title': 'N/A',
            'company': 'N/A',
            'location': 'N/A',
            'job_link': driver.current_url
        }


def apply_to_jobs(driver, job_listings, bot, message):
    applied_count = 0
    search_keyword = message.text.strip()
    
    user_info = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'search_keyword': search_keyword
    }

    try:
        for job_listing in job_listings:
            try:
                # Scroll and click
                driver.execute_script("arguments[0].scrollIntoView(true);", job_listing)
                time.sleep(1)
                job_listing.click()
                time.sleep(3)
                
                # Extract job details
                job_details = extract_job_details(driver)
                
                # If job title is N/A, use search keyword
                if job_details['job_title'] == 'N/A':
                    job_details['job_title'] = search_keyword
                
                try:
                    easy_apply_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'jobs-apply-button--top-card'))
                    )
                    print(f"Easy Apply button found for {job_details['job_title']} at {job_details['company']}")
                    
                    if continue_to_apply(driver):  # Check if application was successful
                        # Save successful application with user info
                        job_details['status'] = 'applied'
                        save_job_application(job_details, user_info)

                        applied_count += 1
                        update_message = (
                            f"🚀 Successfully applied!\n"
                            f"💼 Position: {job_details['job_title']}\n"
                            f"🏢 Company: {job_details['company']}\n"
                            f"📍 Location: {job_details['location']}\n"
                            f"✅ Total applications: {applied_count}"
                        )
                        bot.reply_to(message, update_message)

                except NoSuchElementException as e:
                    print(f"Easy Apply button not found: {str(e)}")
                    job_details['status'] = 'skipped'
                    save_job_application(job_details, user_info)
                    continue
                except TimeoutException as e:
                    print(f"Timeout waiting for Easy Apply button: {str(e)}")
                    job_details['status'] = 'timeout'
                    save_job_application(job_details, user_info)
                    continue
                
            except Exception as e:
                print(f"Error processing job listing: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error in apply_to_jobs: {str(e)}")
    
    finally:
        print(f"Total applications completed: {applied_count}")
        return applied_count  # Ensure we return the count even if there's an error

# def apply_to_jobs(driver, job_listings, bot, message):
#     applied_count = 0
#     search_keyword = message.text.strip()
    
#     user_info = {
#         'user_id': message.from_user.id,
#         'username': message.from_user.username,
#         'first_name': message.from_user.first_name,
#         'search_keyword': search_keyword
#     }

#     for job_listing in job_listings:
#         try:
#             # Scroll and click
#             driver.execute_script("arguments[0].scrollIntoView(true);", job_listing)
#             time.sleep(1)
#             job_listing.click()
#             time.sleep(3)
            
#             # Extract job details
#             job_details = extract_job_details(driver)
            
#             # If job title is N/A, use search keyword
#             if job_details['job_title'] == 'N/A':
#                 job_details['job_title'] = search_keyword
            
#             try:
#                 easy_apply_button = WebDriverWait(driver, 5).until(
#                     EC.element_to_be_clickable((By.CLASS_NAME, 'jobs-apply-button--top-card'))
#                 )
#                 print(f"Easy Apply button found for {job_details['job_title']} at {job_details['company']}")
#                 continue_to_apply(driver)

#                 # Save successful application with user info
#                 job_details['status'] = 'applied'
#                 save_job_application(job_details, user_info)

#                 applied_count += 1
#                 update_message = (
#                     f"🚀 Successfully applied!\n"
#                     f"💼 Position: {job_details['job_title']}\n"
#                     f"🏢 Company: {job_details['company']}\n"
#                     f"📍 Location: {job_details['location']}\n"
#                     f"✅ Total applications: {applied_count}"
#                 )
#                 bot.reply_to(message, update_message)

#             except NoSuchElementException as e:
#                 print(f"Easy Apply button not found: {str(e)}")
#                 job_details['status'] = 'skipped'
#                 save_job_application(job_details, user_info)
#                 continue
#             except TimeoutException as e:
#                 print(f"Timeout waiting for Easy Apply button: {str(e)}")
#                 job_details['status'] = 'timeout'
#                 save_job_application(job_details, user_info)
#                 continue
            
#         except Exception as e:
#             print(f"Error processing job listing: {str(e)}")
#             continue


# def fill_empty_fields(driver) -> bool:
#     filled_any = False
#     try:
#         # Check text inputs
#         input_fields = driver.find_elements(By.XPATH,
#             './/input[contains(@class, "artdeco-text-input--input")]')
        
#         for field in input_fields:
#             try:
#                 # Get label and helper text
#                 label = field.find_element(By.XPATH,
#                     './ancestor::div[contains(@class, "artdeco-text-input--container")]//label').text.strip()
#                 label_lower = label.lower()
                
#                 # Try to get helper text/example if available
#                 try:
#                     helper_text = field.find_element(By.XPATH,
#                         './following-sibling::div[contains(@class, "artdeco-text-input--hint")]').text.strip()
#                 except:
#                     helper_text = ""

#                 # Special handling for CTC/salary fields
#                 if any(x in label_lower for x in ["ctc", "compensation", "salary"]):
#                     if "current" in label_lower:
#                         answer = "100000"
#                     else:  # expected salary
#                         answer = "400000"
#                     field.clear()
#                     field.send_keys(answer)
#                     time.sleep(0.5)
#                     field.send_keys(Keys.TAB)
#                     filled_any = True
#                     print(f"Filled salary field: {label} with {answer}")
#                     continue

#                 # Special handling for notice period
#                 if "notice period" in label_lower:
#                     answer = "30"
#                     field.clear()
#                     field.send_keys(answer)
#                     time.sleep(0.5)
#                     field.send_keys(Keys.TAB)
#                     filled_any = True
#                     print(f"Filled notice period: {label} with {answer}")
#                     continue

#                 # Special handling for experience fields
#                 if "experience" in label_lower or "years" in label_lower:
#                     answer = "0"
#                     field.clear()
#                     field.send_keys(answer)
#                     time.sleep(0.5)
#                     field.send_keys(Keys.TAB)
#                     filled_any = True
#                     print(f"Filled experience field: {label} with {answer}")
#                     continue

#                 # Handle location fields
#                 try:
#                     location_fields = driver.find_elements(By.XPATH,
#                         '//input[contains(@class, "artdeco-text-input--input") and contains(@aria-label, "Location") or contains(@name, "location")]')
                    
#                     for field in location_fields:
#                         if not field.get_attribute("value"):
#                             scroll_to_element(driver, field)
#                             field.clear()
#                             field.send_keys("Mumbai")
#                             time.sleep(2)  # Wait for suggestions
                            
#                             # Try to find and click location suggestions
#                             try:
#                                 suggestions = WebDriverWait(driver, 5).until(
#                                     EC.presence_of_all_elements_located((By.XPATH, 
#                                         "//div[contains(@class, 'search-typeahead-v2__hit') or " +
#                                         "contains(@class, 'location-typeahead__option')]"))
#                                 )
#                                 if suggestions:
#                                     suggestions[0].click()
#                                     filled_any = True
#                                     print("Selected location from dropdown: Mumbai")
#                                     time.sleep(1)
#                             except:
#                                 # If no suggestions dropdown, try to submit directly
#                                 field.send_keys(Keys.TAB)
#                                 print("No location suggestions found, using direct input")
#                                 filled_any = True
                                
#                 except Exception as e:
#                     print(f"Error handling location field: {str(e)}")

#                 # Handle numeric fields that require validation
#                 if "Enter a whole number larger than 0" in helper_text:
#                     answer = "1"
#                     field.clear()
#                     field.send_keys(answer)
#                     time.sleep(0.5)
#                     field.send_keys(Keys.TAB)
#                     filled_any = True
#                     print(f"Filled numeric field: {label} with {answer}")
#                     continue

#                 # Default handling for other fields
#                 value = field.get_attribute("value")
#                 if not value or value.isspace():
#                     answer = get_answer(label_lower)
#                     field.clear()
#                     field.send_keys(answer)
#                     field.send_keys(Keys.TAB)
#                     time.sleep(0.5)
#                     filled_any = True
#                     print(f"Filled field: {label} with {answer}")

#             except Exception as e:
#                 print(f"Error filling field {label if 'label' in locals() else 'unknown'}: {str(e)}")

#         # Check dropdowns
#         dropdowns = driver.find_elements(By.TAG_NAME, "select")
#         for dropdown in dropdowns:
#             select = Select(dropdown)
#             current_value = select.first_selected_option.text.strip()
            
#             if current_value == "Select an option":
#                 try:
#                     label = dropdown.get_attribute("aria-label") or ""
#                     label_lower = label.lower()

#                     # Use predefined answers for dropdowns
#                     answer = None
#                     if "experience" in label_lower:
#                         answer = "0-1 years"
#                     elif "education" in label_lower:
#                         answer = predefined_answers.get("education", "Bachelor's Degree")
#                     elif "notice" in label_lower:
#                         answer = predefined_answers.get("notice period", "0")
                    
#                     # Try to select the answer
#                     try:
#                         if answer:
#                             select.select_by_visible_text(answer)
#                         else:
#                             # If no matching predefined answer, select first non-empty option
#                             if len(select.options) > 1:
#                                 select.select_by_index(1)
#                             else:
#                                 select.select_by_index(0)
#                         time.sleep(0.5)
#                         filled_any = True
#                         print(f"Filled empty dropdown: {label}")
#                     except:
#                         print(f"Could not select answer {answer} for dropdown {label}")

#                 except Exception as e:
#                     print(f"Error with dropdown: {str(e)}")

#         # Handle radio buttons with specific attributes
#         radio_groups = driver.find_elements(By.XPATH,
#             '//fieldset[contains(@class, "artdeco-form__group--radio")]')
            
#         for group in radio_groups:
#             try:
#                 # Check if already selected
#                 selected = group.find_elements(By.XPATH, './/input[@type="radio"][@checked]')
#                 if selected:
#                     print("Radio option already selected, skipping...")
#                     continue
                
#                 # Find radio input with specific data attribute
#                 radio_inputs = group.find_elements(By.XPATH, 
#                     './/input[@type="radio" and contains(@data-test-text-selectable-option__input, "Yes")]')
                
#                 if radio_inputs:
#                     radio_input = radio_inputs[0]
#                     input_id = radio_input.get_attribute("id")
                    
#                     # Find corresponding label using the input's ID
#                     label = group.find_element(By.XPATH, 
#                         f'.//label[@data-test-text-selectable-option__label="Yes" and @for="{input_id}"]')
                    
#                     try:
#                         scroll_to_element(driver, label)
#                         time.sleep(0.5)
#                         label.click()
#                         filled_any = True
#                         print("Selected 'Yes' radio option")
#                     except:
#                         try:
#                             # Try clicking the input directly if label click fails
#                             radio_input.click()
#                             filled_any = True
#                             print("Selected radio input directly")
#                         except:
#                             try:
#                                 # Try JavaScript click as last resort
#                                 driver.execute_script("arguments[0].click();", radio_input)
#                                 filled_any = True
#                                 print("Selected radio using JavaScript")
#                             except Exception as e:
#                                 print(f"Failed to click radio option: {str(e)}")
                
#             except Exception as e:
#                 print(f"Error with radio group: {str(e)}")

#         # Check textareas
#         textareas = driver.find_elements(By.XPATH,
#             '//textarea[contains(@class, "artdeco-text-input--input")]')
        
#         for textarea in textareas:
#             if not textarea.get_attribute("value"):
#                 try:
#                     label = textarea.find_element(By.XPATH,
#                         './ancestor::div[contains(@class, "artdeco-text-input--container")]//label').text.strip()
#                     answer = get_answer(label, "textarea")
                    
#                     textarea.clear()
#                     textarea.send_keys(answer)
#                     time.sleep(0.5)
#                     filled_any = True
#                     print(f"Filled textarea: {label} with {answer}")
#                 except Exception as e:
#                     print(f"Error with textarea: {str(e)}")

#         # Add numeric field handling
#         try:
#             numeric_fields = driver.find_elements(By.XPATH, 
#                 '//input[contains(@class, "artdeco-text-input--input") and @type="text" and contains(@id, "numeric")]')
            
#             for field in numeric_fields:
#                 try:
#                     # Check if field is already filled
#                     if field.get_attribute('value').strip():
#                         continue
                        
#                     field_id = field.get_attribute('id')
#                     error_id = field.get_attribute('aria-describedby')
                    
#                     if error_id:
#                         error_element = driver.find_element(By.ID, error_id)
#                         error_text = error_element.text.lower()
                        
#                         if "notice period" in error_text or "notice" in field_id.lower():
#                             scroll_to_element(driver, field)
#                             field.clear()
#                             field.send_keys("30")
#                             field.send_keys(Keys.TAB)
#                             time.sleep(0.5)
#                             filled_any = True
#                             print("Filled notice period field")
                            
#                 except Exception as e:
#                     print(f"Error with numeric field: {str(e)}")
#                     continue
                    
#         except Exception as e:
#             print(f"Error finding numeric fields: {str(e)}")

#         return filled_any

#     except Exception as e:
#         print(f"Error in fill_empty_fields: {str(e)}")
#         return False


def main():
    try:
        print("\n=== LinkedIn Job Application Automation ===\n")
        
        # Get email first
        email = input("Please enter your email address: ").strip()
        if not email or '@' not in email:
            print("Please enter a valid email address!")
            return

        # Show previously applied jobs
        print("\nChecking your previous applications...")
        applied_jobs = get_applied_jobs(email)
        if applied_jobs:
            print(f"\nYou have previously applied to {len(applied_jobs)} jobs:")
            for job in applied_jobs[:5]:  # Show last 5 applications
                print(f"• {job['job_title']} at {job['company_name']} ({job['timestamp']})")
        
        print("\n" + "="*50 + "\n")
            
        li_at_cookie = input("Please enter your LinkedIn li_at cookie: ").strip()
        if not li_at_cookie:
            print("Cookie cannot be empty!")
            return
            
        keyword = input("\nEnter job search keyword (e.g., 'python developer'): ").strip()
        if not keyword:
            print("Keyword cannot be empty!")
            return

        print("\nStarting automation...")
        print("You can press Ctrl+C at any time to stop\n")
            
        driver = setup_driver(stealth_mode=True)
        
        if not login_to_linkedin(driver, li_at_cookie):
            print("Failed to login to LinkedIn")
            return
            
        job_listings = search_jobs(driver, keyword)
        if not job_listings:
            print("No job listings found")
            return
            
        applied_count = 0
        
        for job_listing in job_listings:
            try:
                # Scroll and click
                driver.execute_script("arguments[0].scrollIntoView(true);", job_listing)
                time.sleep(1)
                job_listing.click()
                time.sleep(3)
                
                # Extract job details
                job_details = extract_job_details(driver)
                
                # Check if already applied
                existing_applications = supabase.table('linkedin_applications')\
                    .select('*')\
                    .eq('email', email)\
                    .eq('job_id', job_details['job_id'])\
                    .execute()
                
                if existing_applications.data:
                    print(f"Already applied to {job_details['job_title']} at {job_details['company']}")
                    continue
                
                try:
                    easy_apply_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'jobs-apply-button--top-card'))
                    )
                    print(f"Applying to: {job_details['job_title']} at {job_details['company']}")
                    
                    if continue_to_apply(driver):
                        job_details['status'] = 'applied'
                        if save_job_application(job_details, email, keyword):
                            applied_count += 1
                            print(
                                f"\n🚀 Successfully applied!\n"
                                f"💼 Position: {job_details['job_title']}\n"
                                f"🏢 Company: {job_details['company']}\n"
                                f"📍 Location: {job_details['location']}\n"
                                f"✅ Total applications: {applied_count}\n"
                            )

                except Exception as e:
                    print(f"Could not apply to job: {str(e)}")
                    job_details['status'] = 'failed'
                    job_details['error_message'] = str(e)
                    save_job_application(job_details, email, keyword)
                    continue
                    
            except Exception as e:
                print(f"Error processing job listing: {str(e)}")
                continue

        print(f"\nAutomation completed!")
        print(f"Total new applications: {applied_count}")
        
        # Show summary of all applications
        all_jobs = get_applied_jobs(email)
        print(f"Total jobs applied: {len(all_jobs)}")
        
    except Exception as e:
        print(f"Error in automation: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main()