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

# Daily Limit for safety
MAX_APPLICATIONS_PER_DAY = 50

# Choose Timeframe: "r86400" (24h), "r604800" (7d), "r1296000" (15d), "r2592000" (1m)
TIMEFRAME_CODE = "r86400" 

# --- 2. Helper Functions ---
def get_all_active_keywords():
    """Reads keywords.txt and returns a list of active search terms."""
    keyword_list = []
    if not os.path.exists("keywords.txt"):
        print("ALERT: keywords.txt not found. Using default 'SAP Basis'.")
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
    # Set Zoom Level to 80%
    chrome_options.add_argument("--force-device-scale-factor=0.8")
    
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
        print("LOGIN MODULE: Success!")
        return driver
    except Exception as e:
        print(f"LOGIN MODULE: Failed -> {e}")
        return None

# --- 4. Popup Application Module ---
def handle_easy_apply_popup(driver):
    """Handles the multi-step Easy Apply pop-up."""
    try:
        # Click initial Easy Apply button in the right pane
        apply_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
        apply_button.click()
        time.sleep(2)

        # Loop through potential steps (Next, Review, Submit)
        for _ in range(8): 
            # 1. Check for Submit (The final step)
            submit_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
            if submit_btn:
                submit_btn[0].click()
                print(">>> Application Submitted Successfully!")
                time.sleep(2)
                # Dismiss success message
                dismiss = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if dismiss: dismiss[0].click()
                return True

            # 2. Fill numeric 'Years of Experience' if they appear empty
            num_inputs = driver.find_elements(By.XPATH, "//input[contains(@type, 'text')]")
            for inp in num_inputs:
                if inp.get_attribute("value") == "":
                    inp.send_keys("19") # Your experience level

            # 3. Check for Next or Review button
            next_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue to next step') or contains(@aria-label, 'Review your application')]")
            if next_btn:
                next_btn[0].click()
                time.sleep(1.5)
            else:
                break
        return False
    except Exception as e:
        print(f"POPUP MODULE: Error or blocked -> {e}")
        return False

# --- 5. Search & Process Module ---
def search_and_process_jobs(driver, keyword_query):
    wait = WebDriverWait(driver, 15)
    applied_in_this_search = 0
    
    time_filter = f"&f_TPR={TIMEFRAME_CODE}" if TIMEFRAME_CODE else ""
    # Exact Phrase + USA + Easy Apply Only
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_query}&location=United%20States&f_AL=true{time_filter}"
    
    print(f"\n--- SEARCHING: {keyword_query} ---")
    driver.get(search_url)
    time.sleep(5)

    try:
        # Scroll sidebar to load jobs
        sidebar = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results-list")))
        for _ in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
            time.sleep(2)

        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        print(f"Found {len(job_cards)} potential jobs.")

        for index, card in enumerate(job_cards):
            # Check Skip Logic: If already applied
            card_text = card.text.lower()
            if "applied" in card_text:
                print(f"Job {index + 1}: Already applied. Skipping.")
                continue

            try:
                driver.execute_script("arguments[0].scrollIntoView();", card)
                card.click()
                time.sleep(2)
                
                # Check for Easy Apply button
                apply_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
                if apply_btn:
                    print(f"Job {index + 1}: Starting application...")
                    if handle_easy_apply_popup(driver):
                        applied_in_this_search += 1
                else:
                    print(f"Job {index + 1}: Already applied or manual link.")
            except:
                continue
                
    except Exception as e:
        print(f"SEARCH ERROR: {e}")
    
    return applied_in_this_search

# --- 6. Main Execution ---
if __name__ == "__main__":
    browser = linkedin_login()
    
    if browser:
        active_keywords = get_all_active_keywords()
        total_applied_today = 0
        
        for keyword in active_keywords:
            if total_applied_today >= MAX_APPLICATIONS_PER_DAY:
                print("Daily limit reached. Stopping script.")
                break
                
            count = search_and_process_jobs(browser, keyword)
            total_applied_today += count
            print(f"Applied to {count} jobs for this keyword. Total today: {total_applied_today}")
            time.sleep(5) # Pause between different keyword searches

        print(f"\nDONE! Finished session. Total Applications: {total_applied_today}")
        input("Press Enter to close the browser...")
        browser.quit()