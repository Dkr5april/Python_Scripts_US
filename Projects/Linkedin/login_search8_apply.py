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

# --- Smart Answer Dictionary ---
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

# --- 4. Hardened Easy Apply Pop-up Handler ---
def handle_easy_apply_popup(driver):
    try:
        wait = WebDriverWait(driver, 10)
        
        # Click the 'Easy Apply' button using a broad XPath
        apply_btn_xpath = "//button[contains(., 'Easy Apply') or contains(@aria-label, 'Easy Apply')]"
        try:
            apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, apply_btn_xpath)))
            driver.execute_script("arguments[0].click();", apply_button)
        except:
            return False

        time.sleep(2)

        for _ in range(12): 
            # Check for Submit
            submit_xpath = "//button[contains(., 'Submit application') or contains(@aria-label, 'Submit application')]"
            submit_btns = driver.find_elements(By.XPATH, submit_xpath)
            
            if submit_btns and submit_btns[0].is_displayed():
                driver.execute_script("arguments[0].click();", submit_btns[0])
                print(">>> SUCCESS: Application Submitted!")
                time.sleep(3)
                dismiss = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss') or contains(., 'Done')]")
                if dismiss: driver.execute_script("arguments[0].click();", dismiss[0])
                return True

            # SMART FILL: Look for questions
            form_elements = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], select, textarea")
            for el in form_elements:
                try:
                    # Get context from the parent div to understand the question
                    parent_text = el.find_element(By.XPATH, "./ancestor::div[contains(@class, 'fb-dash-form-element')]").text.lower()
                    for key, val in MY_DATA.items():
                        if key in parent_text and not el.get_attribute("value"):
                            el.send_keys(val)
                            break
                except: continue

            # Click Next/Review
            next_xpath = "//button[contains(., 'Next') or contains(., 'Review') or contains(@aria-label, 'next')]"
            next_btn = driver.find_elements(By.XPATH, next_xpath)
            
            if next_btn and next_btn[0].is_displayed():
                driver.execute_script("arguments[0].click();", next_btn[0])
                time.sleep(2)
            else:
                # If stuck, close the popup
                close_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
                if close_btn: 
                    driver.execute_script("arguments[0].click();", close_btn[0])
                    time.sleep(1)
                    confirm = driver.find_elements(By.XPATH, "//button[contains(@data-control-name, 'discard')]")
                    if confirm: confirm[0].click()
                break
        return False
    except Exception as e:
        print(f"POPUP ERROR: {e}")
        return False

# --- 5. Main Search and Logic ---
def search_and_process(driver, keyword_set):
    wait = WebDriverWait(driver, 30)
    applied_in_this_search = 0
    
    # URL encoded and strictly filtered for Easy Apply (f_AL=true)
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_set.replace(' ', '%20')}&location=United%20States&f_AL=true&f_TPR={TIMEFRAME_CODE}"
    
    print(f"\n--- SEARCHING FOR: {keyword_set} ---")
    driver.get(search_url)
    time.sleep(8) 

    try:
        # Robust sidebar detection
        sidebar_selectors = [
            (By.CLASS_NAME, "jobs-search-results-list"),
            (By.CSS_SELECTOR, ".scaffold-layout__list-container"),
            (By.TAG_NAME, "main")
        ]
        
        sidebar = None
        for selector_type, selector_val in sidebar_selectors:
            try:
                elements = driver.find_elements(selector_type, selector_val)
                if elements:
                    sidebar = elements[0]
                    break
            except: continue

        if not sidebar:
            if "no matching jobs" in driver.page_source.lower():
                print(f"No results for {keyword_set}. Skipping.")
                return 0
            raise Exception("Job list sidebar not found.")

        # Scroll for lazy loading
        for _ in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
            time.sleep(2)

        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-occludable-job-id], .jobs-search-results-list__list-item")
        print(f"Detected {len(job_cards)} job cards.")

        for index, card in enumerate(job_cards):
            if applied_in_this_search >= MAX_APPLICATIONS_PER_DAY: break
            
            try:
                if "applied" in card.text.lower():
                    continue

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(1.5)
                driver.execute_script("arguments[0].click();", card)
                time.sleep(3) 
                
                # Check the Right Pane
                right_pane = driver.find_element(By.CLASS_NAME, "jobs-search__job-details--container")
                
                if "Easy Apply" in right_pane.text:
                    print(f"Job {index + 1}: Easy Apply found. Processing...")
                    if handle_easy_apply_popup(driver):
                        applied_in_this_search += 1
                else:
                    print(f"Job {index + 1}: Regular Apply. Logging to file.")
                    log_skipped_job(driver.current_url)

            except Exception as e:
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
                print("Daily limit reached.")
                break
            
            count = search_and_process(browser, k_word)
            total_applied_today += count
            time.sleep(5)

        print(f"\n--- SESSION COMPLETE ---")
        print(f"Applied to {total_applied_today} jobs.")
        input("Press ENTER to close the browser...")
        browser.quit()