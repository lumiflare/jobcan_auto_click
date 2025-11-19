import time
import os
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jobcan_bot.log"),
        logging.StreamHandler()
    ]
)

def get_driver():
    options = webdriver.ChromeOptions()
    
    if os.environ.get('IS_DOCKER'):
        logging.info("Running in Docker mode (Headless)")
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # In Docker (Debian/Ubuntu), chromium is usually at /usr/bin/chromium
        options.binary_location = "/usr/bin/chromium"
        
        # Use system installed chromedriver
        service = Service("/usr/bin/chromedriver")
    else:
        logging.info("Running in Local mode")
        # options.add_argument('--headless') # Run in headless mode if you don't want to see the browser
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login(driver):
    load_dotenv()
    email = os.getenv("JOBCAN_EMAIL")
    password = os.getenv("JOBCAN_PASSWORD")

    if not email or not password:
        logging.error("Email or Password not found in .env file.")
        return False

    try:
        logging.info("Navigating to login page...")
        driver.get("https://id.jobcan.jp/users/sign_in")

        logging.info("Entering credentials...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_email"))).send_keys(email)
        driver.find_element(By.ID, "user_password").send_keys(password)
        
        driver.find_element(By.ID, "login_button").click()
        
        # Wait for the "Attendance Management" link
        logging.info("Waiting for 'Attendance Management' link...")
        try:
            # Wait up to 20 seconds
            wait = WebDriverWait(driver, 20)
            
            # Try to find the element. 
            # We use presence_of_element_located first to ensure it's in DOM, then check visibility.
            attendance_link = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "jbc-app-link"))
            )
            
            # Scroll into view just in case
            driver.execute_script("arguments[0].scrollIntoView(true);", attendance_link)
            time.sleep(1)

            # Log current URL to ensure we are on the right page
            logging.info(f"Current URL: {driver.current_url}")

            # Try standard click, fallback to JS click
            try:
                attendance_link.click()
                logging.info("Clicked 'Attendance Management' link (Standard click).")
            except Exception as click_error:
                logging.warning(f"Standard click failed: {click_error}. Trying JS click...")
                driver.execute_script("arguments[0].click();", attendance_link)
                logging.info("Clicked 'Attendance Management' link (JS click).")
            
            # It opens in a new tab (target="_blank")
            original_window = driver.current_window_handle
            
            # Wait for new window
            wait.until(EC.number_of_windows_to_be(2))
            
            # Switch to the new tab
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
            
            logging.info("Switched to Attendance page.")
            time.sleep(3) # Wait for page load
            
        except Exception as e:
            logging.error(f"Could not find or click 'Attendance Management' link: {e}")
            logging.error(f"Current URL at failure: {driver.current_url}")
            driver.save_screenshot("error_screenshot.png")
            logging.info("Saved screenshot to error_screenshot.png")
            return False

        return True
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return False

def click_attendance_button(button_text_keywords):
    driver = get_driver()
    try:
        if not login(driver):
            return

        logging.info(f"Looking for button with keywords: {button_text_keywords}")
        
        button_found = False
        for keyword in button_text_keywords:
            try:
                # XPath to find an element containing the text, that is clickable
                # Checking for div, a, button, span
                xpath = f"//*[contains(text(), '{keyword}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                
                for element in elements:
                    # Check if visible and clickable
                    if element.is_displayed():
                        logging.info(f"Found element with text '{keyword}': {element.tag_name}, {element.get_attribute('id')}")
                        
                        element.click()
                        logging.info(f"Clicked '{keyword}' button.")
                        button_found = True
                        break
                if button_found:
                    break
            except Exception as e:
                logging.error(f"Error searching for {keyword}: {e}")

        if not button_found:
            logging.warning(f"Could not find any button matching {button_text_keywords}")
            
            # Clock In
            if "P U S H" in button_text_keywords:
                try:
                    driver.find_element(By.ID, "adit-button-push").click()
                    logging.info("Clicked 'adit-button-push' (Clock In) by ID.")
                    button_found = True
                except:
                    pass
            
            # Clock Out
            if "退勤" in button_text_keywords and not button_found:
                try:
                    driver.find_element(By.ID, "adit-button-work-end").click()
                    logging.info("Clicked 'adit-button-work-end' (Clock Out) by ID.")
                    button_found = True
                except:
                    pass

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        time.sleep(5) # Wait a bit to ensure request is sent
        driver.quit()

def job_clock_out():
    logging.info("Starting scheduled Clock Out (Lunch Start)...")
    # Keywords for Clock Out / Break Start
    click_attendance_button(["退勤", "休憩開始"])

def job_clock_in():
    logging.info("Starting scheduled Clock In (Lunch End)...")
    # Keywords for Clock In / Break End
    click_attendance_button(["P U S H", "休憩終了"])

def run_scheduler():
    logging.info("Scheduler started. Waiting for 12:00 and 13:00...")
    
    # Schedule
    schedule.every().day.at("12:00").do(job_clock_out)
    schedule.every().day.at("13:00").do(job_clock_in)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # Check if .env exists
    if not os.path.exists(".env"):
        print("WARNING: .env file not found. Please create one based on .env.example")
    
    # You can uncomment these lines to test immediately
    # job_clock_out()
    # job_clock_in()
    
    run_scheduler()
