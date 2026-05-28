# =========================
# LINKEDIN EASY APPLY BOT
# ULTRA STABLE VERSION
# Login kept untouched
# =========================

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

from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)

# ============================================
# CONFIGURATION
# ============================================

EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

MAX_APPLICATIONS_PER_DAY = 50

TIMEFRAME_CODE = "r86400"

# ============================================
# YOUR ANSWERS
# ============================================

MY_DATA = {
    "years of experience": "19",
    "sap basis": "19",
    "how many years": "19",
    "authorized to work": "yes",
    "require sponsorship": "no",
    "sponsorship": "no",
    "notice period": "immediate",
    "salary": "165000",
    "expected salary": "165000",
    "location": "Scottsdale, AZ",
    "current location": "Scottsdale, AZ",
    "phone": "9999999999"
}

# ============================================
# GLOBALS
# ============================================

processed_jobs = set()
already_applied_jobs = set()

# ============================================
# HELPERS
# ============================================

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))


def safe_find_elements(driver, by, value):

    try:
        return driver.find_elements(by, value)
    except:
        return []


def safe_click(driver, element):

    try:

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            element
        )

        time.sleep(1)

        driver.execute_script(
            "arguments[0].click();",
            element
        )

        return True

    except:
        return False


# ============================================
# KEYWORDS
# ============================================

def get_all_active_keywords():

    keyword_list = []

    if not os.path.exists("keywords.txt"):

        print("ALERT: keywords.txt not found")

        return ["SAP Basis Administrator"]

    with open(
        "keywords.txt",
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            clean_line = line.strip()

            if clean_line and not clean_line.startswith("#"):

                keyword_list.append(clean_line)

    return keyword_list


# ============================================
# LOAD PREVIOUS JOBS
# ============================================

def load_previous_jobs():

    if not os.path.exists("applied_jobs.txt"):
        return

    with open(
        "applied_jobs.txt",
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            already_applied_jobs.add(
                line.strip()
            )


def save_applied_job(job_id):

    with open(
        "applied_jobs.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(f"{job_id}\n")


# ============================================
# LOGGING
# ============================================

def log_skipped_job(job_url):

    with open(
        "manual_apply_list.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"- {job_url}\n"
        )


# ============================================
# REPORT
# ============================================

def write_keyword_report(
    keyword,
    total_jobs,
    easy_apply_jobs,
    manual_jobs,
    duplicate_jobs,
    already_applied_count,
    successful_applies
):

    with open(
        "keyword_report.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 60)
        f.write("\n")

        f.write(f"KEYWORD: {keyword}\n")
        f.write(f"TOTAL JOBS DETECTED: {total_jobs}\n")
        f.write(f"EASY APPLY FOUND: {easy_apply_jobs}\n")
        f.write(f"SUCCESSFUL APPLIES: {successful_applies}\n")
        f.write(f"MANUAL APPLY JOBS: {manual_jobs}\n")
        f.write(f"DUPLICATES SKIPPED: {duplicate_jobs}\n")
        f.write(
            f"ALREADY APPLIED SKIPPED: "
            f"{already_applied_count}\n"
        )

        f.write("=" * 60)
        f.write("\n")


# ============================================
# LOGIN
# DO NOT TOUCH
# ============================================

def linkedin_login():

    chrome_options = Options()

    chrome_options.add_argument(
        "--force-device-scale-factor=0.8"
    )

    service = Service(
        ChromeDriverManager().install()
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    wait = WebDriverWait(driver, 20)

    try:

        driver.get(
            "https://www.linkedin.com/login"
        )

        driver.maximize_window()

        wait.until(
            EC.presence_of_element_located(
                (By.ID, "username")
            )
        ).send_keys(EMAIL)

        driver.find_element(
            By.ID,
            "password"
        ).send_keys(PASSWORD)

        driver.find_element(
            By.XPATH,
            "//button[@type='submit']"
        ).click()

        wait.until(
            EC.presence_of_element_located(
                (By.ID, "global-nav")
            )
        )

        print("LOGIN: SUCCESS")

        return driver

    except Exception as e:

        print(f"LOGIN FAILED: {e}")

        return None


# ============================================
# CLOSE POPUP SAFELY
# ============================================

def close_popup(driver):

    try:

        dismiss = safe_find_elements(
            driver,
            By.XPATH,
            "//button[contains(@aria-label,'Dismiss')]"
        )

        if dismiss:

            safe_click(driver, dismiss[0])

            time.sleep(1)

            discard = safe_find_elements(
                driver,
                By.XPATH,
                "//button[contains(@data-control-name,'discard')]"
            )

            if discard:
                safe_click(driver, discard[0])

    except:
        pass


# ============================================
# EASY APPLY HANDLER
# ============================================

def handle_easy_apply_popup(driver):

    try:

        wait = WebDriverWait(driver, 10)

        # ====================================
        # FIND EASY APPLY BUTTON
        # ====================================

        apply_xpath = (
            "//button[contains(@aria-label,'Easy Apply') "
            "or contains(.,'Easy Apply')]"
        )

        apply_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, apply_xpath)
            )
        )

        # ====================================
        # CLICK WITH RETRIES
        # ====================================

        clicked = False

        for attempt in range(3):

            try:

                safe_click(driver, apply_button)

                clicked = True

                break

            except:

                random_sleep(1, 2)

        if not clicked:

            print("FAILED TO CLICK EASY APPLY")

            return False

        # ====================================
        # WAIT FOR POPUP
        # ====================================

        try:

            wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        ".jobs-easy-apply-modal"
                    )
                )
            )

        except:

            print("POPUP DID NOT OPEN")

            return False

        random_sleep(2, 3)

        # ====================================
        # PROCESS STEPS
        # ====================================

        for step in range(20):

            print(f"STEP {step + 1}")

            random_sleep(1, 2)

            # ====================================
            # CHECK IF POPUP STILL EXISTS
            # ====================================

            popup_exists = safe_find_elements(
                driver,
                By.CSS_SELECTOR,
                ".jobs-easy-apply-modal"
            )

            if not popup_exists:

                print("POPUP CLOSED")

                return False

            # ====================================
            # FILL INPUTS
            # ====================================

            try:

                sections = safe_find_elements(
                    driver,
                    By.CSS_SELECTOR,
                    "div.jobs-easy-apply-form-section__grouping"
                )

                for section in sections:

                    try:

                        section_text = (
                            section.text.lower()
                        )

                        inputs = section.find_elements(
                            By.CSS_SELECTOR,
                            "input[type='text'], "
                            "input[type='number'], "
                            "textarea"
                        )

                        for inp in inputs:

                            try:

                                if not inp.is_displayed():
                                    continue

                                current_value = (
                                    inp.get_attribute("value")
                                )

                                if current_value:
                                    continue

                                for key, val in MY_DATA.items():

                                    if key in section_text:

                                        inp.clear()

                                        inp.send_keys(val)

                                        time.sleep(1)

                                        break

                            except:
                                continue

                    except:
                        continue

            except:
                pass

            # ====================================
            # VALIDATION ERROR
            # ====================================

            errors = safe_find_elements(
                driver,
                By.CSS_SELECTOR,
                ".artdeco-inline-feedback--error"
            )

            if errors:

                print("VALIDATION ERROR")

                close_popup(driver)

                return False

            # ====================================
            # SUBMIT BUTTON
            # ====================================

            submit_btns = safe_find_elements(
                driver,
                By.XPATH,
                "//button[contains(.,'Submit application') "
                "or contains(@aria-label,'Submit application')]"
            )

            if submit_btns:

                try:

                    if submit_btns[0].is_displayed():

                        safe_click(
                            driver,
                            submit_btns[0]
                        )

                        print(
                            ">>> APPLICATION SUBMITTED"
                        )

                        random_sleep(3, 5)

                        close_popup(driver)

                        return True

                except:
                    pass

            # ====================================
            # NEXT BUTTON
            # ====================================

            next_btns = safe_find_elements(
                driver,
                By.XPATH,
                "//button[contains(.,'Next') "
                "or contains(.,'Review') "
                "or contains(@aria-label,'Continue')]"
            )

            if next_btns:

                try:

                    if next_btns[0].is_displayed():

                        safe_click(
                            driver,
                            next_btns[0]
                        )

                        random_sleep(2, 4)

                        continue

                except:
                    pass

            # ====================================
            # NOTHING FOUND
            # ====================================

            print(
                "NO NEXT OR SUBMIT BUTTON FOUND"
            )

            break

        close_popup(driver)

        return False

    except Exception as e:

        print(f"POPUP ERROR: {e}")

        close_popup(driver)

        return False


# ============================================
# SEARCH AND APPLY
# ============================================

def search_and_process(driver, keyword_set):

    applied_in_this_search = 0

    easy_apply_count = 0

    manual_apply_count = 0

    duplicate_jobs = 0

    already_applied_count = 0

    search_url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={keyword_set.replace(' ', '%20')}"
        "&location=United%20States"
        "&f_AL=true"
        f"&f_TPR={TIMEFRAME_CODE}"
    )

    print(f"\n--- SEARCHING FOR: {keyword_set} ---")

    driver.get(search_url)

    random_sleep(6, 9)

    try:

        # ====================================
        # SCROLL
        # ====================================

        for _ in range(5):

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            random_sleep(2, 4)

        # ====================================
        # COUNT JOBS
        # ====================================

        total_jobs_detected = len(

            safe_find_elements(
                driver,
                By.CSS_SELECTOR,
                ".job-card-container, "
                "[data-occludable-job-id], "
                ".jobs-search-results-list__list-item"
            )
        )

        print(
            f"Detected {total_jobs_detected} job cards."
        )

        # ====================================
        # PROCESS JOBS
        # ====================================

        for index in range(total_jobs_detected):

            if applied_in_this_search >= (
                MAX_APPLICATIONS_PER_DAY
            ):
                break

            try:

                # REFRESH ELEMENTS
                job_cards = safe_find_elements(
                    driver,
                    By.CSS_SELECTOR,
                    ".job-card-container, "
                    "[data-occludable-job-id], "
                    ".jobs-search-results-list__list-item"
                )

                if index >= len(job_cards):
                    continue

                card = job_cards[index]

                card_text = card.text.lower()

                # ====================================
                # ALREADY APPLIED
                # ====================================

                if "applied" in card_text:

                    already_applied_count += 1

                    print(
                        f"Job {index+1}: "
                        f"Already Applied"
                    )

                    continue

                # ====================================
                # JOB ID
                # ====================================

                job_id = card.get_attribute(
                    "data-occludable-job-id"
                )

                if not job_id:

                    try:

                        job_id = str(
                            hash(
                                card.get_attribute(
                                    "innerHTML"
                                )
                            )
                        )

                    except:
                        continue

                # ====================================
                # DUPLICATES
                # ====================================

                if job_id in processed_jobs:

                    duplicate_jobs += 1

                    print(
                        f"Job {index+1}: "
                        f"Duplicate skipped"
                    )

                    continue

                if job_id in already_applied_jobs:

                    already_applied_count += 1

                    print(
                        f"Job {index+1}: "
                        f"Already applied earlier"
                    )

                    continue

                processed_jobs.add(job_id)

                # ====================================
                # OPEN JOB
                # ====================================

                try:

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});",
                        card
                    )

                    random_sleep(1, 2)

                    clickable = card.find_element(
                        By.TAG_NAME,
                        "a"
                    )

                    safe_click(
                        driver,
                        clickable
                    )

                except StaleElementReferenceException:

                    print(
                        f"Job {index+1}: "
                        f"Stale card skipped"
                    )

                    continue

                random_sleep(3, 5)

                # ====================================
                # EASY APPLY DETECTION
                # ====================================

                easy_apply_buttons = safe_find_elements(
                    driver,
                    By.XPATH,
                    "//button[contains(@aria-label,'Easy Apply')]"
                )

                if easy_apply_buttons:

                    easy_apply_count += 1

                    print(
                        f"Job {index+1}: "
                        f"Easy Apply found."
                    )

                    success = handle_easy_apply_popup(
                        driver
                    )

                    if success:

                        applied_in_this_search += 1

                        save_applied_job(job_id)

                        already_applied_jobs.add(job_id)

                        print(
                            f"Applied Count: "
                            f"{applied_in_this_search}"
                        )

                    else:

                        print(
                            "Easy Apply process failed."
                        )

                else:

                    manual_apply_count += 1

                    print(
                        f"Job {index+1}: "
                        f"Manual Apply"
                    )

                    log_skipped_job(
                        driver.current_url
                    )

                random_sleep(2, 5)

            except Exception as e:

                print(
                    f"JOB ERROR: {e}"
                )

                close_popup(driver)

                continue

        # ====================================
        # REPORT
        # ====================================

        write_keyword_report(
            keyword_set,
            total_jobs_detected,
            easy_apply_count,
            manual_apply_count,
            duplicate_jobs,
            already_applied_count,
            applied_in_this_search
        )

    except Exception as e:

        print(f"SEARCH ERROR: {e}")

    return applied_in_this_search


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    load_previous_jobs()

    browser = linkedin_login()

    if browser:

        open(
            "keyword_report.txt",
            "w",
            encoding="utf-8"
        ).close()

        all_keywords = get_all_active_keywords()

        total_applied_today = 0

        for k_word in all_keywords:

            if total_applied_today >= (
                MAX_APPLICATIONS_PER_DAY
            ):

                print("Daily limit reached.")

                break

            count = search_and_process(
                browser,
                k_word
            )

            total_applied_today += count

            random_sleep(5, 8)

        print("\n--- SESSION COMPLETE ---")

        print(
            f"Applied to "
            f"{total_applied_today} jobs."
        )

        print("\nGenerated Files:")
        print("1. keyword_report.txt")
        print("2. manual_apply_list.txt")
        print("3. applied_jobs.txt")

        input(
            "\nPress ENTER to close browser..."
        )

        browser.quit()