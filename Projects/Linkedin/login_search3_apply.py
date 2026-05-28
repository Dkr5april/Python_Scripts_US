import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. Configuration ---
EMAIL = "koteswararao.davuluri@gmail.com"
PASSWORD = "MyPassword@nid"
MAX_APPLICATIONS_PER_DAY = 50
TIMEFRAME_CODE = "r1296000" # Last 15 Days

# --- 2. Helper Functions ---
def get_all_active_keywords():
    keyword_list = []
    if not os.path.exists("keywords.txt"):
        return ['"SAP Basis"']
    with open("keywords.txt", "r") as f:
        for line in f:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith("#"):
                keyword_list.append(clean_line)
    return keyword_list

# --- 3. Login Module ---
def linkedin_login():
    chrome_options = Options()
    chrome_options.add_argument("--force-device-scale-factor=0.8") # 80% Zoom
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.get("https://www.linkedin.com/login")
        driver.maximize_window()
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        wait.until(EC.presence_of_element_located((By.ID, "global-nav")))
        print("LOGIN: Success!")
        return driver
    except Exception as e:
        print(f"LOGIN: Failed -> {e}")
        return None

# --- 4. NEW: The "Easy Apply" Interaction Module ---
def handle_easy_apply_popup(driver):
    """Handles the screens inside the Easy Apply pop-up."""
    try:
        # 1. Click the 'Easy Apply' button in the right-side job details pane
        apply_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
        apply_btn.click()
        time.sleep(2)

        # 2. Iterate through the steps (Next, Review, Submit)
        for _ in range(10): # Try up to 10 screens
            # Check if we are at the final "Submit" stage
            submit_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
            if submit_btn:
                submit_btn[0].click()
                print(">>> SUCCESS: Application Submitted!")
                time.sleep(3)
                # Dismiss the 'Success' pop-up if it exists
                dismiss = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if dismiss: dismiss[0].click()
                return True

            # Fill in numeric questions (usually 'Years of Experience')
            inputs = driver.find_elements(By.XPATH, "//input[contains(@type, 'text')]")
            for inp in inputs:
                if inp.get_attribute("value") == "":
                    inp.send_keys("19") # Enters your experience
            
            # Click 'Next' or 'Review'
            next_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue to next step') or contains(@aria-label, 'Review your application')]")
            if next_btn:
                next_btn[0].click()
                time.sleep(2)
            else:
                # If no 'Next' button but not 'Submit', it might be a required question we can't answer
                print(">>> STUCK: Manual intervention or complex question found.")
                # We close the pop-up to move to the next job
                close_popup = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if close_popup: close_popup[0].click()
                break
        return False
    except Exception as e:
        print(f"POPUP ERROR: {e}")
        return False

# --- 5. Search & Selection Module ---
def search_and_process(driver, keyword):
    wait = WebDriverWait(driver, 15)
    applied_count = 0
    time_filter = f"&f_TPR={TIMEFRAME_CODE}" if TIMEFRAME_CODE else ""
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=United%20States&f_AL=true{time_filter}"
    
    print(f"\n--- STARTING SEARCH: {keyword} ---")
    driver.get(search_url)
    time.sleep(5)

    try:
        sidebar = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results-list")))
        for _ in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
            time.sleep(1.5)

        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        
        for index, card in enumerate(job_cards):
            if applied_count >= MAX_APPLICATIONS_PER_DAY: break
            
            # Skip if text says 'Applied'
            if "applied" in card.text.lower():
                print(f"Job {index+1}: Already applied. Skipping.")
                continue

            try:
                driver.execute_script("arguments[0].scrollIntoView();", card)
                card.click()
                time.sleep(2)

                # Check for Easy Apply
                apply_check = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
                if apply_check:
                    print(f"Job {index+1}: Attempting to apply...")
                    if handle_easy_apply_popup(driver):
                        applied_count += 1
                else:
                    print(f"Job {index+1}: Already applied or manual application.")
            except:
                continue
    except Exception as e:
        print(f"SEARCH ERROR: {e}")
    return applied_count

# --- 6. Main Run ---
if __name__ == "__main__":
    browser = linkedin_login()
    if browser:
        keywords = get_all_active_keywords()
        total_applied = 0
        
        for k in keywords:
            if total_applied >= MAX_APPLICATIONS_PER_DAY: break
            total_applied += search_and_process(browser, k)
        
        print(f"\nFINISHED. Total applied today: {total_applied}")
        input("Session Complete. Press Enter in this window to close Chrome...")
        browser.quit()