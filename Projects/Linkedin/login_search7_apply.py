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
TIMEFRAME_CODE = "r86400" 

# --- NEW: Smart Answer Dictionary ---
# The script will look for these words in questions and type the value.
MY_DATA = {
    "years of experience": "19",
    "sap basis": "19",
    "how many years": "19",
    "authorized to work": "yes",
    "require sponsorship": "no",
    "notice period": "immediate",
    "salary": "165000",
    "location": "Scottsdale, AZ"
}

# --- 2. Helper Functions ---
def get_all_active_keywords():
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

def log_skipped_job(job_url):
    """Saves external apply links to a file for manual completion with Simplify."""
    with open("manual_apply_list.txt", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {job_url}\n")

# --- 3. Login Module ---
def linkedin_login():
    chrome_options = Options()
    chrome_options.add_argument("--force-device-scale-factor=0.8")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
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

# --- 4. Updated Easy Apply Pop-up Handler ---
def handle_easy_apply_popup(driver):
    try:
        apply_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
        apply_button.click()
        time.sleep(2)

        for _ in range(10): 
            # Check for Final Submit
            submit_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Submit application')]")
            if submit_btn:
                submit_btn[0].click()
                print(">>> SUCCESS: Application Submitted!")
                time.sleep(3)
                dismiss = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if dismiss: dismiss[0].click()
                return True

            # SMART FILL: Look for questions
            form_elements = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], select, textarea")
            for el in form_elements:
                try:
                    # Find the label text for the question
                    parent_text = el.find_element(By.XPATH, "..").text.lower()
                    for key, val in MY_DATA.items():
                        if key in parent_text and (el.get_attribute("value") == "" or el.get_attribute("value") is None):
                            el.send_keys(val)
                            break
                except: continue

            # Click Next/Review
            next_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue to next step') or contains(@aria-label, 'Review your application')]")
            if next_btn:
                next_btn[0].click()
                time.sleep(2)
            else:
                print(">>> STUCK: Manual intervention needed. Skipping.")
                close_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if close_btn: 
                    close_btn[0].click()
                    time.sleep(1)
                    # Confirm discard if prompted
                    confirm_discard = driver.find_elements(By.XPATH, "//button[contains(@data-control-name, 'discard')]")
                    if confirm_discard: confirm_discard[0].click()
                break
        return False
    except Exception as e:
        print(f"POPUP ERROR: {e}")
        return False

# --- 5. Main Search and Logic ---
def search_and_process(driver, keyword_set):
    wait = WebDriverWait(driver, 30) # Increased patience
    applied_in_this_search = 0
    
    time_filter = f"&f_TPR={TIMEFRAME_CODE}" if TIMEFRAME_CODE else ""
    # Ensure the keyword is properly URL encoded
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_set.replace(' ', '%20')}&location=United%20States&f_AL=true{time_filter}"
    
    print(f"\n--- SEARCHING FOR: {keyword_set} ---")
    driver.get(search_url)
    time.sleep(10) # Heavy wait for the sidebar to stabilize

    try:
        # SEARCH STRATEGY: Try broader selectors if the specific sidebar fails
        sidebar_selectors = [
            (By.CLASS_NAME, "jobs-search-results-list"),
            (By.CSS_SELECTOR, ".scaffold-layout__list-container"),
            (By.CSS_SELECTOR, "div[data-view-name='job-card']"),
            (By.TAG_NAME, "main") # Absolute fallback
        ]
        
        sidebar = None
        for selector_type, selector_val in sidebar_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_val)
                if elements:
                    sidebar = elements[0]
                    print(f"Found job list using: {selector_val}")
                    break
            except: continue

        if not sidebar:
            # Check if it's just a 'No Jobs Found' page
            if "no matching jobs" in driver.page_source.lower():
                print(f"No results found for {keyword_set}. Skipping.")
                return 0
            raise Exception("Sidebar not found even with fallback selectors.")

        # Scroll for lazy loading - modified to scroll the window if sidebar scroll fails
        for _ in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Look for job cards using multiple common patterns
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-occludable-job-id], .jobs-search-results-list__list-item")
        
        print(f"Detected {len(job_cards)} job cards.")

        for index, card in enumerate(job_cards):
            if applied_in_this_search >= MAX_APPLICATIONS_PER_DAY: break
            
            # Use a safer text check
            try:
                if "applied" in card.text.lower():
                    continue
            except: continue

            try:
                # Use ActionChains or Javascript to click if standard click fails
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(2)
                
                # Attempt click
                try:
                    card.click()
                except:
                    driver.execute_script("arguments[0].click();", card)
                
                time.sleep(3) 
                
                easy_apply_btns = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
                
                if easy_apply_btns:
                    if handle_easy_apply_popup(driver):
                        applied_in_this_search += 1
                else:
                    current_job_url = driver.current_url
                    print(f"Job {index + 1}: External Apply. Logged to list.")
                    log_skipped_job(current_job_url)

            except Exception as e:
                print(f"Could not process job {index+1}: {e}")
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
                break
            
            count = search_and_process(browser, k_word)
            total_applied_today += count
            time.sleep(3)

        print(f"\n--- SESSION COMPLETE ---")
        print(f"Applied to {total_applied_today} jobs automatically.")
        print("Check 'manual_apply_list.txt' for external jobs to do with Simplify.")
        input("Press ENTER to close...")
        browser.quit()