import os
import time as t
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from typing import Callable


# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# def extract_internshala_details(driver):
#     try:
#         # Wait for modal to load
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
#         )
#         time.sleep(2)
        
#         details = {}
        
#         # Get job title and URL
#         try:
#             # First find the job link which contains both title and correct URL
#             job_link = WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, "a.job-title-href"))
#             )
#             details['job_title'] = job_link.text.strip()
#             details['job_url'] = job_link.get_attribute('href')  # Get the actual job URL
#             logger.info(f"Found job title: {details['job_title']} and URL: {details['job_url']}")
#         except Exception as e:
#             logger.error(f"Failed to get job title/url: {str(e)}")
#             details['job_title'] = 'N/A'
#             details['job_url'] = driver.current_url

#         # Get company name - Updated this part
#         try:
#             company_element = WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.XPATH, 
#                     ".//div[@class='company_and_premium']/p[@class='company-name']"))
#             )
#             company_text = company_element.text.strip()
#             details['company_name'] = ' '.join(company_text.split())  # Clean extra whitespace
#             logger.info(f"Found company name: {details['company_name']}")
#         except Exception as e:
#             logger.error(f"Failed to get company name: {str(e)}")
#             details['company_name'] = 'N/A'

#         # Get applicant count
#         try:
#             applicant_element = driver.find_element(By.CSS_SELECTOR, "[title*='applicant']")
#             applicant_text = applicant_element.text
#             details['applicant_count'] = ''.join(filter(str.isdigit, applicant_text))
#             logger.info(f"Found applicant count: {details['applicant_count']}")
#         except Exception as e:
#             logger.error(f"Failed to get applicant count: {str(e)}")
#             details['applicant_count'] = ''

#         # Get internship ID
#         try:
#             modal = driver.find_element(By.CSS_SELECTOR, '[id^="individual_internship_"]')
#             internship_id = modal.get_attribute('id').split('_')[-1]
#             details['job_id'] = f"internshala_{internship_id}"
#             logger.info(f"Found internship ID: {details['job_id']}")
#         except Exception as e:
#             logger.error(f"Failed to get internship ID: {str(e)}")
#             details['job_id'] = f"internshala_{int(time.time())}"

#         details['job_location'] = 'Work From Home'
        
#         # Log complete details
#         logger.info(f"Extracted complete job details: {details}")
        
#         return details

#     except Exception as e:
#         logger.error(f"Error in extract_internshala_details: {str(e)}")
#         return {
#             'job_id': f"internshala_{int(time.time())}",
#             'job_title': 'N/A',
#             'company_name': 'N/A',
#             'job_location': 'Work From Home',
#             'job_url': driver.current_url,
#             'applicant_count': ''
#         }

def extract_internshala_details(driver):
    try:
        # Wait for modal to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )
        time.sleep(2)
        
        details = {}
        
        # Get job title and URL
        try:
            # First find the job link which contains both title and correct URL
            job_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.job-title-href"))
            )
            details['job_title'] = job_link.text.strip()
            details['job_url'] = job_link.get_attribute('href')  # Get the actual job URL
            logger.info(f"Found job title: {details['job_title']} and URL: {details['job_url']}")
        except Exception as e:
            logger.error(f"Failed to get job title/url: {str(e)}")
            details['job_title'] = 'N/A'
            details['job_url'] = driver.current_url

        # Get company name
        try:
            # First try XPath method
            xpath_selectors = [
                "//div[@class='company_and_premium']//p[@class='company-name']",
                "//div[@class='heading_6 company_name']",
                "//div[contains(@class, 'company_name')]"
            ]
            
            company_found = False
            for xpath in xpath_selectors:
                try:
                    company_element = driver.find_element(By.XPATH, xpath)
                    company_text = company_element.text.strip()
                    if company_text and company_text != "Internshala":
                        details['company_name'] = company_text
                        company_found = True
                        logger.info(f"Found company name from XPath: {details['company_name']}")
                        break
                except:
                    continue

            # If XPath method fails or returns Internshala, try URL method
            if not company_found or details.get('company_name') == "Internshala":
                url = details['job_url']
                if 'at-' in url:
                    company_name = url.split('at-')[-1].split('1')[0]  # Split at timestamp
                    company_name = company_name.replace('-', ' ').title()  # Format company name
                    company_name = ' '.join(word.capitalize() for word in company_name.split())  # Proper case
                    details['company_name'] = company_name.strip()
                    logger.info(f"Found company name from URL: {details['company_name']}")
                else:
                    details['company_name'] = 'N/A'
                    logger.error("Could not extract company name from URL")
            
        except Exception as e:
            logger.error(f"Failed to get company name: {str(e)}")
            details['company_name'] = 'N/A'

        # Get applicant count
        try:
            applicant_element = driver.find_element(By.CSS_SELECTOR, "[title*='applicant']")
            applicant_text = applicant_element.text
            details['applicant_count'] = ''.join(filter(str.isdigit, applicant_text))
            logger.info(f"Found applicant count: {details['applicant_count']}")
        except Exception as e:
            logger.error(f"Failed to get applicant count: {str(e)}")
            details['applicant_count'] = ''

        # Get internship ID
        try:
            modal = driver.find_element(By.CSS_SELECTOR, '[id^="individual_internship_"]')
            internship_id = modal.get_attribute('id').split('_')[-1]
            details['job_id'] = f"internshala_{internship_id}"
            logger.info(f"Found internship ID: {details['job_id']}")
        except Exception as e:
            logger.error(f"Failed to get internship ID: {str(e)}")
            details['job_id'] = f"internshala_{int(time.time())}"

        details['job_location'] = 'Work From Home'
        
        # Log complete details
        logger.info(f"Extracted complete job details: {details}")
        
        return details

    except Exception as e:
        logger.error(f"Error in extract_internshala_details: {str(e)}")
        return {
            'job_id': f"internshala_{int(time.time())}",
            'job_title': 'N/A',
            'company_name': 'N/A',
            'job_location': 'Work From Home',
            'job_url': driver.current_url,
            'applicant_count': ''
        }

def save_application_to_db(driver, user_id, data_manager, job_role, status='success', error_message='', job_details=None):
    try:
        if job_details is None:  # This should never happen now
            logger.error("No job details provided")
            return False

        application_data = {
            'timestamp': datetime.now().isoformat(),
            'job_id': job_details['job_id'],
            'user_id': user_id,
            'job_title': job_details['job_title'],
            'company_name': job_details['company_name'],
            'job_location': job_details['job_location'],
            'job_url': job_details['job_url'],
            'application_status': status,
            'keyword_searched': job_role,
            'error_message': error_message,
            'platform': 'internshala',
            'applicant_count': job_details.get('applicant_count', '')
        }
        
        success = data_manager.record_job_application(application_data)
        if success:
            logger.info(f"Successfully saved application for {job_details['job_title']}")
        return success
        
    except Exception as e:
        logger.error(f"Error saving application to database: {str(e)}")
        return False

# def save_application_to_db(driver, user_id, data_manager, job_role, status='success', error_message=''):
#     """Save internship application to database"""
#     try:
#         job_details = extract_internshala_details(driver)
        
#         application_data = {
#             'timestamp': datetime.now().isoformat(),
#             'job_id': job_details['job_id'],
#             'user_id': user_id,
#             'job_title': job_details['job_title'],
#             'company_name': job_details['company_name'],
#             'job_location': job_details['job_location'],
#             'job_url': job_details['job_url'],
#             'application_status': status,
#             'keyword_searched': job_role,
#             'error_message': error_message,
#             'platform': 'internshala'
#         }
        
#         return data_manager.record_job_application(application_data)
#     except Exception as e:
#         logger.error(f"Error saving application: {str(e)}")
#         return False

def add_cookies(driver, phpsessid):
    try:
        driver.add_cookie({'name': 'PHPSESSID', 'value': phpsessid})
        driver.refresh()
        t.sleep(2)
        return True
    except Exception as e:
        logger.error(f"Error adding cookies: {str(e)}")
        return False

def is_element_visible(driver, by, value):
    try:
        element = driver.find_element(by, value)
        return element.is_displayed()
    except:
        return False

def wait_and_click(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except Exception as e:
        logger.error(f"Error clicking element: {str(e)}")
        return False

def click_apply_now(driver):
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempt {attempt + 1} to click 'Apply now' button")
            
            # Wait for the modal to be present
            modal = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
            )
            logger.info("Modal found")
            
            # Scroll to the bottom of the modal content
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)
            t.sleep(2)
            
            # Try to find the "Apply now" button using multiple methods
            apply_now_button = None
            try:
                apply_now_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "continue_button"))
                )
            except:
                try:
                    apply_now_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id='continue_button']"))
                    )
                except:
                    apply_now_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-large') and contains(text(), 'Apply now')]"))
                    )
            
            if apply_now_button:
                logger.info("'Apply now' button found")
                
                # Try regular click
                apply_now_button.click()
                logger.info("'Apply now' button clicked successfully")
                return True
            else:
                # If button not found, try JavaScript click
                driver.execute_script("document.querySelector('#continue_button').click();")
                logger.info("'Apply now' button clicked using JavaScript")
                return True
        
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to click 'Apply now' button: {str(e)}")
            t.sleep(2)
    
    logger.error("Failed to click 'Apply now' button after maximum attempts")
    return False

def fill_application(driver, job_role):
    try:
        # Check if cover letter is present
        cover_letter_present = is_element_present(driver, By.CSS_SELECTOR, "#cover_letter_holder > div.ql-editor")
        if cover_letter_present:
            wait = WebDriverWait(driver, 30)
            cover_letter = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#cover_letter_holder > div.ql-editor")))
            cover_letter.click()
            cover_letter.send_keys(get_answer_for_role(job_role))
            t.sleep(2)
            logger.info("Cover letter filled successfully")
        else:
            logger.info("No cover letter field found")

        # Check for additional questions
        additional_questions = driver.find_elements(By.XPATH, "//div[contains(@class, 'form-group additional_question')]")
        if additional_questions:
            logger.info(f"Found {len(additional_questions)} additional questions")
            for index, question in enumerate(additional_questions):
                try:
                    textarea = question.find_element(By.TAG_NAME, "textarea")
                    textarea.clear()
                    textarea.send_keys("Please refer to my resume for detailed information on my skills and experience.")
                    logger.info(f"Filled additional question {index + 1}")
                except NoSuchElementException:
                    logger.info(f"No textarea found for question {index + 1}, skipping")
                except Exception as e:
                    logger.error(f"Error filling additional question {index + 1}: {str(e)}")
        else:
            logger.info("No additional questions found")

        # Handle availability
        availability_option = driver.find_element(By.XPATH, "//input[@type='radio' and @value='yes']")
        driver.execute_script("arguments[0].click();", availability_option)
        logger.info("Selected 'Yes, I am available to join immediately' option")

    except Exception as e:
        logger.error(f"Error in fill_application: {str(e)}")

def is_element_present(driver, by, value):
    try:
        driver.find_element(by, value)
        return True
    except NoSuchElementException:
        return False

# def search_and_apply(driver, job_list, num_applications, progress_callback):
#     total_applied = 0
#     for job_role in job_list:
#         applied_count = 0
#         consecutive_failures = 0
#         while applied_count < num_applications and consecutive_failures < 5:
#             try:
#                 driver.get(f'https://internshala.com/internships/work-from-home-{job_role}-internships/')
#                 logger.info(f"Navigated to {job_role} internships page")
#                 t.sleep(5)

#                 jobs = driver.find_elements(By.CLASS_NAME, "internship_meta")
#                 logger.info(f"Found {len(jobs)} job listings")

#                 for index, job in enumerate(jobs[2:], start=3):
#                     if applied_count >= num_applications:
#                         break

#                     try:
#                         logger.info(f"Attempting to apply for job {index} in {job_role}")
                        
#                         driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
#                         t.sleep(1)
                        
#                         job.click()
#                         logger.info("Job details opened")
#                         t.sleep(3)
                        
#                         if not click_apply_now(driver):
#                             logger.warning("Failed to click Apply now button. Skipping this job.")
                            
#                             consecutive_failures += 1
#                             continue

#                         fill_application(driver, job_role)

#                         submit_button = WebDriverWait(driver, 60).until(
#                             EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
#                         )
#                         driver.execute_script("arguments[0].click();", submit_button)
#                         logger.info("Submit button clicked")
                        
#                         success_message = WebDriverWait(driver, 20).until(
#                             EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Application submitted')]"))
#                         )
#                         logger.info("Application submitted successfully")
                        
#                         applied_count += 1
#                         total_applied += 1
#                         consecutive_failures = 0
#                         logger.info(f"Applied to {applied_count} jobs in {job_role}")
#                         if progress_callback:
#                             progress_callback(job_role, applied_count, total_applied)

#                         # Close modal or refresh page
#                         try:
#                             close_button = WebDriverWait(driver, 10).until(
#                                 EC.element_to_be_clickable((By.XPATH, "//button[@class='close']"))
#                             )
#                             close_button.click()
#                             logger.info("Closed success modal")
#                         except:
#                             driver.refresh()
#                             logger.info("Refreshed page after application")
#                         t.sleep(5)
#                         break

#                     except Exception as e:
#                         logger.error(f"Error while applying to job: {str(e)}")
#                         consecutive_failures += 1
#                         driver.refresh()
#                         t.sleep(5)

#                 logger.info("Waiting 1 minute before proceeding to the next job.")
#                 t.sleep(60)

#             except Exception as e:
#                 logger.error(f"Error in main application loop: {str(e)}")
#                 consecutive_failures += 1
#                 driver.refresh()
#                 t.sleep(5)

#         if consecutive_failures >= 5:
#             logger.warning(f"Encountered 5 consecutive failures for {job_role}. Moving to next job role.")
#         else:
#             logger.info(f"Completed {applied_count} applications for {job_role}")

# def search_and_apply(driver, job_list, num_applications, progress_callback, user_id, data_manager):
#     total_applied = 0
#     for job_role in job_list:
#         applied_count = 0
#         consecutive_failures = 0
#         while applied_count < num_applications and consecutive_failures < 5:
#             try:
#                 driver.get(f'https://internshala.com/internships/work-from-home-{job_role}-internships/')
#                 logger.info(f"Navigated to {job_role} internships page")
#                 time.sleep(5)

#                 jobs = driver.find_elements(By.CLASS_NAME, "internship_meta")
#                 logger.info(f"Found {len(jobs)} job listings")

#                 for index, job in enumerate(jobs[2:], start=3):
#                     if applied_count >= num_applications:
#                         break

#                     try:
#                         logger.info(f"Attempting to apply for job {index} in {job_role}")
                        
#                         driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
#                         time.sleep(1)
                        
#                         job.click()
#                         logger.info("Job details opened")
#                         time.sleep(3)
                        
#                         job_details = extract_internshala_details(driver)

#                         if not click_apply_now(driver):
#                             logger.warning("Failed to click Apply now button. Skipping this job.")
#                             save_application_to_db(
#                                 driver, 
#                                 user_id,
#                                 data_manager, 
#                                 job_role, 
#                                 status='failed',
#                                 error_message='Failed to click apply button',
#                                 job_details=job_details
#                             )
#                             consecutive_failures += 1
#                             continue

#                         fill_application(driver, job_role)

#                         submit_button = WebDriverWait(driver, 60).until(
#                             EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
#                         )
#                         driver.execute_script("arguments[0].click();", submit_button)
#                         logger.info("Submit button clicked")
                        
#                         success_message = WebDriverWait(driver, 20).until(
#                             EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Application submitted')]"))
#                         )
#                         logger.info("Application submitted successfully")
                        
#                         # Save successful application
#                         save_application_to_db(
#                             driver,
#                             user_id,
#                             data_manager,
#                             job_role,
#                             status='success'
#                         )
                        
#                         applied_count += 1
#                         total_applied += 1
#                         consecutive_failures = 0
#                         logger.info(f"Applied to {applied_count} jobs in {job_role}")
#                         if progress_callback:
#                             progress_callback(job_role, applied_count, total_applied)

#                         # Close modal or refresh page
#                         try:
#                             close_button = WebDriverWait(driver, 10).until(
#                                 EC.element_to_be_clickable((By.XPATH, "//button[@class='close']"))
#                             )
#                             close_button.click()
#                             logger.info("Closed success modal")
#                         except:
#                             driver.refresh()
#                             logger.info("Refreshed page after application")
#                         time.sleep(5)
#                         break

#                     except Exception as e:
#                         logger.error(f"Error while applying to job: {str(e)}")
#                         consecutive_failures += 1
#                         driver.refresh()
#                         time.sleep(5)

#                 logger.info("Waiting 1 minute before proceeding to the next job.")
#                 time.sleep(60)

#             except Exception as e:
#                 logger.error(f"Error in main application loop: {str(e)}")
#                 consecutive_failures += 1
#                 driver.refresh()
#                 time.sleep(5)

#         if consecutive_failures >= 5:
#             logger.warning(f"Encountered 5 consecutive failures for {job_role}. Moving to next job role.")
#         else:
#             logger.info(f"Completed {applied_count} applications for {job_role}")

def search_and_apply(driver, job_list, num_applications, progress_callback, user_id, data_manager):
    total_applied = 0
    for job_role in job_list:
        applied_count = 0
        consecutive_failures = 0
        while applied_count < num_applications and consecutive_failures < 5:
            try:
                driver.get(f'https://internshala.com/internships/work-from-home-{job_role}-internships/')
                logger.info(f"Navigated to {job_role} internships page")
                time.sleep(5)

                jobs = driver.find_elements(By.CLASS_NAME, "internship_meta")
                logger.info(f"Found {len(jobs)} job listings")

                for index, job in enumerate(jobs[2:], start=3):
                    if applied_count >= num_applications:
                        break

                    try:
                        logger.info(f"Attempting to apply for job {index} in {job_role}")
                        
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
                        time.sleep(1)
                        
                        job.click()
                        logger.info("Job details opened")
                        time.sleep(3)
                        
                        # Extract details ONCE before applying
                        job_details = extract_internshala_details(driver)
                        logger.info(f"Extracted job details: {job_details}")

                        if not click_apply_now(driver):
                            save_application_to_db(
                                driver, 
                                user_id,
                                data_manager, 
                                job_role,
                                status='failed',
                                error_message='Failed to click apply button',
                                job_details=job_details  # Pass the extracted details
                            )
                            consecutive_failures += 1
                            continue

                        fill_application(driver, job_role)

                        submit_button = WebDriverWait(driver, 60).until(
                            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
                        )
                        driver.execute_script("arguments[0].click();", submit_button)
                        
                        success_message = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Application submitted')]"))
                        )
                        logger.info("Application submitted successfully")
                        
                        # Save successful application with previously extracted details
                        save_application_to_db(
                            driver,
                            user_id,
                            data_manager,
                            job_role,
                            job_details=job_details,  # Pass the extracted details
                            status='success'
                        )
                        
                        applied_count += 1
                        total_applied += 1
                        consecutive_failures = 0
                        logger.info(f"Applied to {applied_count} jobs in {job_role}")
                        if progress_callback:
                            progress_callback(job_role, applied_count, total_applied)

                        # Close modal or refresh page
                        try:
                            close_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[@class='close']"))
                            )
                            close_button.click()
                            logger.info("Closed success modal")
                        except:
                            driver.refresh()
                            logger.info("Refreshed page after application")
                        time.sleep(5)
                        break

                    except Exception as e:
                        logger.error(f"Error while applying to job: {str(e)}")
                        consecutive_failures += 1
                        driver.refresh()
                        time.sleep(5)

                logger.info("Waiting 1 minute before proceeding to the next job.")
                time.sleep(60)

            except Exception as e:
                logger.error(f"Error in main application loop: {str(e)}")
                consecutive_failures += 1
                driver.refresh()
                time.sleep(5)

        if consecutive_failures >= 5:
            logger.warning(f"Encountered 5 consecutive failures for {job_role}. Moving to next job role.")
        else:
            logger.info(f"Completed {applied_count} applications for {job_role}")

def get_answer_for_role(job_role):
    base_answer = "I am an enthusiastic and dedicated individual, ready to take on challenges and learn new things. "
    role_specific = {
        'data-science': "My strong background in statistics and machine learning makes me an ideal candidate for this data science role.",
        'software-development': "My experience in developing robust and scalable software solutions aligns perfectly with this opportunity.",
        'web-development': "My proficiency in front-end and back-end technologies positions me well for this web development internship.",
        'python-django': "As an aspiring Python-Django developer with hands-on experience building web applications, I am well-suited for this role.",
        'data-analytics': "My strong analytical skills and proficiency in data visualization tools make me an excellent candidate for this data analytics internship.",
        'business-analytics': "My ability to translate data into actionable insights makes me ideal for this business analytics role.",
    }
    return base_answer + role_specific.get(job_role, "My skills and passion make me a great fit for this role.")

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

def run_internshala_automation(driver, phpsessid, num_applications, progress_callback, user_id, data_manager):
    """
    Run Internshala automation using provided driver instance.
    Mirrors LinkedIn implementation pattern.
    """
    try:
        driver.get('https://internshala.com/')
        driver.maximize_window()
        
        if not add_cookies(driver, phpsessid):
            return "Failed to log in"

        job_list = ['data-science', 'software-development', 'web-development', 
                   'data-analytics', 'python-django', 'business-analytics']

        search_and_apply(driver, job_list, num_applications, progress_callback, user_id, data_manager)
    except Exception as e:
        logger.error(f"Error in automation: {str(e)}")
        raise


if __name__ == "__main__":
    phpsessid = input("Enter PHPSESSID: ")
    num_applications = int(input("Enter number of applications per job role: "))

    def console_progress_callback(job_role, role_count, total_count):
        print(f"Current role: {job_role}, Applied: {role_count}, Total: {total_count}")

    run_internshala_automation(phpsessid, num_applications, console_progress_callback)
