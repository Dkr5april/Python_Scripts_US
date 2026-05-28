import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. Configuration ---
EMAIL = "koteswararao.davuluri@gmail.com"
PASSWORD = "MyPassword@nid"


# --- 2. Login Module ---
def linkedin_login():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.get("https://www.linkedin.com/login")
        driver.maximize_window()

        # Enter Credentials
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Verify Home Page Load
        wait.until(EC.presence_of_element_located((By.ID, "global-nav")))
        print("LOGIN MODULE: Success!")
        return driver
    except Exception as e:
        print(f"LOGIN MODULE: Failed -> {e}")
        return None

# --- 3. Search Module ---
def search_and_select_jobs(driver):
    wait = WebDriverWait(driver, 15)
    
    # Target URL: SAP BASIS + Easy Apply
    search_url = "https://www.linkedin.com/jobs/search/?keywords=SAP%20BASIS&f_AL=true"
    print("SEARCH MODULE: Navigating to results...")
    driver.get(search_url)
    time.sleep(5)

    try:
        # Scroll the left sidebar to load jobs
        sidebar = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results-list")))
        for i in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", sidebar)
            time.sleep(2)

        # Identify all job cards
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        print(f"SEARCH MODULE: Found {len(job_cards)} jobs.")

        for index, card in enumerate(job_cards):
            try:
                driver.execute_script("arguments[0].scrollIntoView();", card)
                card.click()
                time.sleep(2) # Wait for right pane to refresh
                
                # Check for the button
                apply_btn = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
                if apply_btn:
                    print(f"RESULT: Job {index + 1} has Easy Apply!")
                else:
                    print(f"RESULT: Job {index + 1} is not Easy Apply.")
            except:
                continue
    except Exception as e:
        print(f"SEARCH MODULE: Critical error -> {e}")

# --- 4. Main Execution ---
if __name__ == "__main__":
    # Start the relay: Login first...
    browser = linkedin_login()
    
    # ...then pass the open browser to the Search module
    if browser:
        search_and_select_jobs(browser)