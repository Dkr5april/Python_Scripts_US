import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================
# CONFIGURATION
# ============================================
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")
MAX_APPLICATIONS_PER_DAY = 50
TIMEFRAME_CODE = "r86400" 

MY_DATA = {
    "years of experience": "19",
    "sap basis": "19",
    "how many years": "19",
    "authorized to work": "yes",
    "require sponsorship": "no",
    "salary": "165000",
    "location": "Scottsdale, AZ"
}

# ============================================
# PERSISTENT TRACKING (Memory across days)
# ============================================
def load_processed_ids():
    if not os.path.exists("processed_jobs.txt"):
        return set()
    with open("processed_jobs.txt", "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_job_id(job_id):
    with open("processed_jobs.txt", "a", encoding="utf-8") as f:
        f.write(f"{job_id}\n")

# ============================================
# LOGGING (Separated Reports)
# ============================================
def log_result(file_path, keyword, title, company, url, status):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] KW: {keyword} | {title} at {company} | {status} | {url}\n")

# ============================================
# STRICT FILTER LOGIC
# ============================================
def is_valid_title(found_title, target_keyword):
    """Checks if the actual job title matches your strict keyword."""
    return target_keyword.lower() in found_title.lower()

# ============================================
# EASY APPLY HANDLER
# ============================================
def handle_easy_apply_popup(driver):
    try:
        # Initial click of Easy Apply
        apply_xpath = "//button[contains(., 'Easy Apply') or contains(@aria-label, 'Easy Apply')]"
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, apply_xpath))).click()
        time.sleep(2)

        for _ in range(12):
            # Check for Submit
            submit = driver.find_elements(By.XPATH, "//button[contains(., 'Submit') or contains(@aria-label, 'Submit')]")
            if submit and submit[0].is_displayed():
                driver.execute_script("arguments[0].click();", submit[0])
                time.sleep(3)
                # Close the 'Done' screen
                done = driver.find_elements(By.XPATH, "//button[contains(., 'Done') or contains(@aria-label, 'Dismiss')]")
                if done: driver.execute_script("arguments[0].click();", done[0])
                return True

            # Simple Smart Fill
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], textarea")
            for inp in inputs:
                if inp.is_displayed() and not inp.get_attribute("value"):
                    # Find label text
                    try:
                        label = inp.find_element(By.XPATH, "./ancestor::div[contains(@class, 'fb-dash-form-element')]").text.lower()
                        for key, val in MY_DATA.items():
                            if key in label:
                                inp.send_keys(val)
                                break
                    except: continue

            # Click Next/Review
            next_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Next') or contains(., 'Review')]")
            if next_btn and next_btn[0].is_displayed():
                driver.execute_script("arguments[0].click();", next_btn[0])
                time.sleep(2)
            else: break
        return False
    except: return False

# ============================================
# MAIN SEARCH PROCESS
# ============================================
def search_and_process(driver, keyword, processed_ids):
    applied_count = 0
    # Use quotes in URL for stricter initial search
    url = f"https://www.linkedin.com/jobs/search/?keywords=\"{keyword.replace(' ', '%20')}\"&location=United%20States&f_AL=true&f_TPR={TIMEFRAME_CODE}"
    
    driver.get(url)
    time.sleep(8)

    # 1. Scroll to load initial jobs
    sidebar = driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list")
    for _ in range(3):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
        time.sleep(2)

    # 2. Iterate through cards
    # We re-fetch cards to avoid StaleElement errors
    for i in range(25): # Look at top 25 jobs per keyword
        if applied_count >= MAX_APPLICATIONS_PER_DAY: break
        
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container, [data-occludable-job-id]")
            if i >= len(cards): break
            card = cards[i]

            # CHECK 1: JOB ID (Persistent Memory)
            job_id = card.get_attribute("data-occludable-job-id")
            if not job_id or job_id in processed_ids:
                continue

            # CHECK 2: TITLE (UI Check before clicking)
            card_text = card.text.lower()
            if "applied" in card_text:
                continue

            # Open Job
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(1)
            card.find_element(By.TAG_NAME, "a").click()
            time.sleep(3)

            # FINAL CHECK: TITLE (Strict Matching)
            details = driver.find_element(By.CLASS_NAME, "jobs-search__job-details--container")
            title = details.find_element(By.TAG_NAME, "h1").text.strip()
            company = details.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name").text.strip()
            
            if not is_valid_title(title, keyword):
                print(f"Skipping: '{title}' (Keyword mismatch)")
                continue

            # Mark as processed immediately so we don't try again if it fails
            processed_ids.add(job_id)
            save_job_id(job_id)

            # APPLY LOGIC
            easy_apply_btns = details.find_elements(By.XPATH, "//button[contains(., 'Easy Apply')]")
            if easy_apply_btns:
                print(f"Applying: {title} at {company}")
                if handle_easy_apply_popup(driver):
                    applied_count += 1
                    log_result("easy_apply_success.txt", keyword, title, company, driver.current_url, "SUCCESS")
                else:
                    log_result("easy_apply_failed.txt", keyword, title, company, driver.current_url, "FAILED/STUCK")
            else:
                log_result("manual_apply_list.txt", keyword, title, company, driver.current_url, "MANUAL")

        except Exception as e:
            continue

    return applied_count

if __name__ == "__main__":
    processed_ids = load_processed_ids()
    chrome_options = Options()
    chrome_options.add_argument("--force-device-scale-factor=0.8")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://www.linkedin.com/login")
    driver.maximize_window()
    
    # Manually login or use your existing logic here...
    print("Please ensure you are logged in...")
    time.sleep(15) 

    keywords = ["SAP Basis Administrator"] 
    for kw in keywords:
        search_and_process(driver, kw, processed_ids)
    
    print("\n--- DONE ---")
    driver.quit()