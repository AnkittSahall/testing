#with database added
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
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


def setup_driver(stealth_mode=True, run_in_background=False, safe_mode=True):
    """Initialize the WebDriver with proper options"""
    try:
        # Choose driver type based on stealth mode
        options = uc.ChromeOptions() if stealth_mode else Options()
        
        # Add headless mode if running in background
        if run_in_background:
            options.add_argument("--headless")
        
        # Basic options
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")
        
        # Add AWS specific options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Initialize appropriate driver
        if stealth_mode:
            logger.info("Initializing Undetectable ChromeDriver...")
            driver = uc.Chrome(options=options)
        else:
            logger.info("Initializing regular ChromeDriver...")
            driver = webdriver.Chrome(options=options)
            
        driver.maximize_window()
        
        # Set up common utilities
        wait = WebDriverWait(driver, 30)
        actions = ActionChains(driver)
        
        logger.info("WebDriver initialized successfully.")
        return driver
        
    except Exception as e:
        error_msg = (
            "Failed to initialize driver. Possible reasons:\n"
            "1. Chrome is already running\n"
            "2. Chrome or ChromeDriver is outdated\n"
            "3. If using stealth_mode, try reinstalling undetected-chromedriver\n"
            f"\nError details: {str(e)}"
        )
        logger.error(error_msg)
        raise Exception(error_msg)

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

def fill_empty_fields(driver) -> bool:
    filled_any = False
    try:
        actions = ActionChains(driver)

        # Handle radio buttons first
        radio_groups = driver.find_elements(By.XPATH,
            '//fieldset[contains(@class, "artdeco-form__group--radio") or contains(@data-test-form-builder-radio-button-form-component, "true")]')
            
        for group in radio_groups:
            try:
                # Check if already selected
                selected = group.find_elements(By.XPATH, './/input[@type="radio"][@checked]')
                if selected:
                    print("Radio option already selected, skipping...")
                    continue
                
                if handle_radio_button(driver, group):
                    filled_any = True
                    print("Radio button handled successfully")
                
            except Exception as e:
                print(f"Error with radio group: {str(e)}")

        # Handle location fields
        location_fields = driver.find_elements(By.XPATH,
            '//input[@role="combobox" and contains(@id, "location-GEO-LOCATION")]')
        
        for field in location_fields:
            if not field.get_attribute("value"):
                if handle_location_field(driver, field):
                    filled_any = True
                    print("Location field handled successfully")

        # Check text inputs
        input_fields = driver.find_elements(By.XPATH,
            './/input[contains(@class, "artdeco-text-input--input")]')
        
        for field in input_fields:
            try:
                # Check if field already has a value
                if field.get_attribute("value").strip():
                    print("Input field already filled, skipping...")
                    continue

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
                    answer = "0"
                    field.clear()
                    field.send_keys(answer)
                    time.sleep(0.5)
                    field.send_keys(Keys.TAB)
                    filled_any = True
                    print(f"Filled experience field: {label} with {answer}")
                    continue

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

        # Check textareas
        textareas = driver.find_elements(By.XPATH,
            '//textarea[contains(@class, "artdeco-text-input--input") or contains(@class, "fb-dash-form-element__error-field")]')

        for textarea in textareas:
            if not textarea.get_attribute("value"):
                try:
                    # Try multiple ways to get the label text
                    label = ""
                    try:
                        # Try getting label from aria-label first
                        label = textarea.get_attribute("aria-label")
                    except:
                        try:
                            # Fallback to finding label element
                            label = textarea.find_element(By.XPATH,
                                './ancestor::div[contains(@class, "artdeco-text-input--container")]//label').text.strip()
                        except:
                            pass
                    
                    if not label:
                        # If still no label, try getting from error message
                        error_id = textarea.get_attribute('aria-describedby')
                        if error_id:
                            try:
                                error_element = driver.find_element(By.ID, error_id)
                                label = error_element.text.strip()
                            except:
                                pass

                    # Get appropriate answer
                    if "experience" in label.lower():
                        answer = "1"
                    else:
                        answer = get_answer(label, "textarea")
                    
                    # Scroll and ensure visibility
                    scroll_to_element(driver, textarea)
                    time.sleep(1)
                    
                    # Clear and fill
                    textarea.clear()
                    textarea.send_keys(answer)
                    time.sleep(0.5)
                    textarea.send_keys(Keys.TAB)  # Trigger validation
                    filled_any = True
                    print(f"Filled textarea: {label} with {answer}")
                    
                except Exception as e:
                    print(f"Error with textarea: {str(e)}")

        # Add numeric field handling with improved selectors
        numeric_fields = driver.find_elements(By.XPATH, 
            '//input[contains(@class, "fb-dash-form-element__error-field") and contains(@id, "numeric")]')
        
        if not numeric_fields:
            # Fallback to original selector if no error fields found
            numeric_fields = driver.find_elements(By.XPATH, 
                '//input[contains(@class, "artdeco-text-input--input") and @type="text" and contains(@id, "numeric")]')
        
        for field in numeric_fields:
            try:
                # Check if field is already filled
                if field.get_attribute('value').strip():
                    continue
                    
                # Get the error message if any
                error_id = field.get_attribute('aria-describedby')
                error_text = ""
                
                if error_id:
                    try:
                        error_element = driver.find_element(By.ID, error_id)
                        error_text = error_element.text.lower()
                    except:
                        pass

                # Scroll and ensure field is visible
                scroll_to_element(driver, field)
                time.sleep(1)
                
                # Clear and fill the field
                field.clear()
                
                # Determine appropriate value based on error text or field ID
                if "enter a whole number larger than 0" in error_text:
                    field.send_keys("1")
                elif any(x in field.get_attribute('id').lower() for x in ["ctc", "salary", "compensation"]):
                    field.send_keys("100000")
                elif "notice" in field.get_attribute('id').lower():
                    field.send_keys("30")
                else:
                    field.send_keys("1")  # Default value for numeric fields
                    
                field.send_keys(Keys.TAB)
                time.sleep(0.5)
                filled_any = True
                print(f"Filled numeric field with ID: {field.get_attribute('id')}")
                    
            except Exception as e:
                print(f"Error with numeric field: {str(e)}")
                continue

        return filled_any

    except Exception as e:
        print(f"Error in fill_empty_fields: {str(e)}")
        return False

def handle_radio_button(driver, group):
    try:
        # Get question text
        question = group.find_element(By.XPATH, 
            './/span[contains(@class, "fb-dash-form-element__label") or contains(@class, "artdeco-text-input--label")]').text.strip()
        print(f"Found radio question: {question}")
        
        question_lower = question.lower()
        
        # Map questions to answers
        predefined_answer = None
        if any(word in question_lower for word in ["commuting", "relocate", "location", "travel"]):
            predefined_answer = "Yes"
        elif "immediate" in question_lower or "start" in question_lower:
            predefined_answer = "Yes"
        elif any(word in question_lower for word in ["authorized", "authorised", "legally", "eligible", "work"]):
            predefined_answer = "Yes"
        elif any(word in question_lower for word in ["sponsor", "sponsorship", "visa"]):
            predefined_answer = "No"
        elif "citizenship" in question_lower:
            predefined_answer = "Yes"
            
        try:
            # Try to find radio input with predefined answer or default to Yes
            radio = None
            if predefined_answer:
                try:
                    radio = group.find_element(By.XPATH, 
                        f'.//input[@type="radio" and (@value="{predefined_answer}" or @data-test-text-selectable-option__input="{predefined_answer}")]')
                except:
                    pass
                    
            if not radio:
                # Default to first Yes option
                radio = group.find_element(By.XPATH, 
                    './/input[@type="radio" and (@value="Yes" or @data-test-text-selectable-option__input="Yes")]')
            
            # Try multiple click methods
            scroll_to_element(driver, radio)
            time.sleep(1)
            
            try:
                radio.click()
            except:
                try:
                    driver.execute_script("arguments[0].click();", radio)
                except:
                    # Try clicking the label
                    label = group.find_element(By.XPATH,
                        f'.//label[@data-test-text-selectable-option__label="{predefined_answer or "Yes"}"]')
                    label.click()
            
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Failed to click radio button: {str(e)}")
            # Try clicking first option as last resort
            try:
                first_radio = group.find_element(By.XPATH, './/input[@type="radio"]')
                driver.execute_script("arguments[0].click();", first_radio)
                return True
            except:
                return False
            
    except Exception as e:
        print(f"Error handling radio button: {str(e)}")
        return False

def handle_location_field(driver, field):
    try:
        # Find location input using multiple possible selectors
        location_input = None
        selectors = [
            '//input[@role="combobox" and contains(@id, "location-GEO-LOCATION")]',
            '//input[contains(@class, "artdeco-text-input--input") and contains(@aria-label, "Location")]',
            '//input[contains(@name, "location")]'
        ]
        
        for selector in selectors:
            try:
                location_input = driver.find_element(By.XPATH, selector)
                if location_input.is_displayed():
                    break
            except:
                continue
                
        if not location_input:
            print("Location input field not found")
            return False
            
        scroll_to_element(driver, location_input)
        location_input.clear()
        time.sleep(1)
        location_input.send_keys("mumbai")
        time.sleep(2)  # Wait for dropdown
        
        # Try multiple methods to select first option
        try:
            # Method 1: Try to click the first suggestion
            suggestions = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH, 
                    "//div[contains(@class, 'search-typeahead-v2__hit') or " +
                    "contains(@class, 'location-typeahead__option')]"))
            )
            if suggestions:
                suggestions[0].click()
                time.sleep(1)
                return True
        except:
            try:
                # Method 2: Use keyboard navigation
                location_input.send_keys(Keys.ARROW_DOWN)
                time.sleep(1)
                location_input.send_keys(Keys.RETURN)
                time.sleep(1)
                return True
            except:
                print("Failed to select location suggestion")
                return False
            
    except Exception as e:
        print(f"Error handling location field: {str(e)}")
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
        return False

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
# sirji
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