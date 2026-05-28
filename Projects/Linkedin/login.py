import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager # Add this import
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
EMAIL = "koteswararao.davuluri@gmail.com"
PASSWORD = "MyPassword@nid"

def linkedin_login():
    # This line now automatically finds and downloads the correct driver for version 147
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.get("https://www.linkedin.com/")
        driver.maximize_window()
        
        # Check if already logged in
        try:
            wait.until(EC.presence_of_element_located((By.ID, "global-nav-typeahead")))
            print("Already logged in.")
            return driver
        except:
            print("Not logged in. Proceeding to login page...")

        driver.get("https://www.linkedin.com/login")

        # Enter Credentials
        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_field.send_keys(EMAIL)

        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(PASSWORD)

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for the home page to load
        wait.until(EC.presence_of_element_located((By.ID, "global-nav")))
        print("Login successful!")
        return driver

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    browser = linkedin_login()