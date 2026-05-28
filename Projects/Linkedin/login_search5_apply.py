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

# Choose Timeframe: "r86400" (24h), "r604800" (7d), "r1296000" (15d), "r2592000" (1m)
TIMEFRAME_CODE = "r1296000" 

# --- 2. Helper Functions ---
def get_all_active_keywords():
    """Reads keywords.txt and returns a list of lines that don't start with '#'."""
    keyword_list = []
    if not os.path.exists("keywords.txt"):
        print("ALERT: keywords.txt not found. Please create it.")
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
    # Set Zoom Level to 80% to ensure all buttons are visible
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
        
        # Verify successful login
        wait.until(EC.presence_of_element_located((By.ID, "global-nav")))
        print("LOGIN: Success!")
        return driver
    except Exception as e:
        print(f"LOGIN: Failed -> {e}")
        return None

# --- 4. Easy Apply Pop-up Handler ---
def handle_easy_apply_popup(driver):
    """Navigates the screens inside the Easy Apply pop-up."""
    try:
        # Click the actual Easy Apply button to open the modal
        apply_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
        apply_button.click()
        time.sleep(2)

        # Loop through potential steps (Next, Review, Submit)
        for _ in range(10): 
            # 1. Look for Submit (The final step)
            submit_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
            if submit_btn:
                submit_btn[0].click()
                print(">>> SUCCESS: Application Submitted!")
                time.sleep(3)
                # Dismiss the success confirmation
                dismiss = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if dismiss: dismiss[0].click()
                return True

            # 2. Automatically fill numeric fields (e.g., 'Years of Experience')
            num_inputs = driver.find_elements(By.XPATH, "//input[contains(@type, 'text')]")
            for inp in num_inputs:
                if inp.get_attribute("value") == "":
                    inp.send_keys("19") # Your professional experience

            # 3. Check for Next or Review buttons
            next_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue to next step') or contains(@aria-label, 'Review your application')]")
            if next_btn:
                next_btn[0].click()
                time.sleep(2)
            else:
                # If we are stuck on a mandatory question we can't answer, close the pop-up
                print(">>> STUCK: Complex question or manual step required. Skipping.")
                close_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if close_btn: close_btn[0].click()
                break
        return False
    except Exception as e:
        print(f"POPUP ERROR: {e}")
        return False

# --- 5. Main Search and Logic ---
def search_and_process(driver, keyword_set):
    wait = WebDriverWait(driver, 25)  # Increased wait time for slow connections
    applied_in_this_search = 0
    
    time_filter = f"&f_TPR={TIMEFRAME_CODE}" if TIMEFRAME_CODE else ""
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_set}&location=United%20States&f_AL=true{time_filter}"
    
    print(f"\n--- SEARCHING FOR: {keyword_set} ---")
    driver.get(search_url)
    time.sleep(7)  # Initial wait for the framework to settle

    try:
        # SEARCH STRATEGY: Try multiple selectors for the job list
        sidebar_selectors = [
            (By.CLASS_NAME, "jobs-search-results-list"),
            (By.CSS_SELECTOR, "[data-view-name='job-card']"),
            (By.CLASS_NAME, "scaffold-layout__list-container")
        ]
        
        sidebar = None
        for selector_type, selector_val in sidebar_selectors:
            try:
                sidebar = wait.until(EC.presence_of_element_located((selector_type, selector_val)))
                if sidebar: 
                    print(f"Found job list using: {selector_val}")
                    break
            except:
                continue

        if not sidebar:
            raise Exception("Could not locate the job list sidebar.")

        # Scroll sidebar to trigger lazy loading
        for _ in range(4):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
            time.sleep(2)

        # Updated selector for job cards
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-occludable-job-id]")
        print(f"Found {len(job_cards)} potential job matches.")

        for index, card in enumerate(job_cards):
            if applied_in_this_search >= MAX_APPLICATIONS_PER_DAY: break
            
            # Skip check
            card_text = card.text.lower()
            if "applied" in card_text:
                print(f"Job {index + 1}: Already applied. Skipping.")
                continue

            try:
                # Scroll to center the card so it's clickable
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(1)
                card.click()
                time.sleep(3) # Wait for the detail pane
                
                # Verify Easy Apply button exists in the right pane
                apply_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
                if apply_btns:
                    print(f"Job {index + 1}: Proceeding to apply...")
                    if handle_easy_apply_popup(driver):
                        applied_in_this_search += 1
                else:
                    print(f"Job {index + 1}: Skipping (Already applied or manual application).")
            except Exception as e:
                print(f"Error interacting with job {index+1}: {e}")
                continue
                
    except Exception as e:
        print(f"SEARCH ERROR: {e}")
    
    return applied_in_this_search

# --- 6. Executive Block ---
if __name__ == "__main__":
    browser = linkedin_login()
    
    if browser:
        all_keywords = get_all_active_keywords()
        total_applied_today = 0
        
        for k_word in all_keywords:
            if total_applied_today >= MAX_APPLICATIONS_PER_DAY:
                print("Daily limit reached. Exiting loop.")
                break
            
            count = search_and_process(browser, k_word)
            total_applied_today += count
            time.sleep(5) # Short pause between different keyword sets

        print(f"\n--- SESSION COMPLETE ---")
        print(f"Successfully applied to {total_applied_today} new jobs.")
        input("Press ENTER in this window to close the browser and end the session...")
        browser.quit()