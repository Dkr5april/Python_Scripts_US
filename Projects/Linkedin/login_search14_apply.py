# =========================
# LINKEDIN EASY APPLY BOT
# Stable Version + Duplicate Protection
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
    StaleElementReferenceException,
    TimeoutException,
    NoSuchElementException
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


def get_all_active_keywords():

    keyword_list = []

    if not os.path.exists("keywords.txt"):

        print("ALERT: keywords.txt not found")

        return ["SAP Basis Administrator"]

    with open("keywords.txt", "r", encoding="utf-8") as f:

        for line in f:

            clean_line = line.strip()

            if clean_line and not clean_line.startswith("#"):
                keyword_list.append(clean_line)

    return keyword_list


def log_skipped_job(job_url):

    with open(
        "manual_apply_list.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {job_url}\n"
        )


# ============================================
# LOAD PREVIOUSLY APPLIED JOBS
# ============================================

def load_previous_jobs():

    if os.path.exists("applied_jobs.txt"):

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
# KEYWORD REPORT
# ============================================

def write_keyword_report(
    keyword,
    total_jobs,
    easy_apply_jobs,
    manual_jobs,
    duplicate_jobs,
    already_applied_count
):

    with open(
        "keyword_report.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 60)
        f.write("\n")

        f.write(
            f"KEYWORD: {keyword}\n"
        )

        f.write(
            f"TOTAL JOBS DETECTED: {total_jobs}\n"
        )

        f.write(
            f"EASY APPLY JOBS: {easy_apply_jobs}\n"
        )

        f.write(
            f"MANUAL APPLY JOBS: {manual_jobs}\n"
        )

        f.write(
            f"DUPLICATE JOBS SKIPPED: {duplicate_jobs}\n"
        )

        f.write(
            f"ALREADY APPLIED SKIPPED: "
            f"{already_applied_count}\n"
        )

        f.write("=" * 60)
        f.write("\n")


# ============================================
# LOGIN
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
# SAFE ELEMENT FINDER
# ============================================

def safe_find_elements(driver, by, value):

    try:

        return driver.find_elements(by, value)

    except:
        return []


# ============================================
# EASY APPLY HANDLER
# ============================================

def handle_easy_apply_popup(driver):

    try:

        wait = WebDriverWait(driver, 10)

        apply_btn_xpath = (
            "//button[contains(., 'Easy Apply') "
            "or contains(@aria-label, 'Easy Apply')]"
        )

        try:

            apply_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, apply_btn_xpath)
                )
            )

            driver.execute_script(
                "arguments[0].click();",
                apply_button
            )

        except:
            return False

        random_sleep(2, 4)

        for step in range(15):

            print(f"STEP {step + 1}")

            # ====================================
            # SUBMIT BUTTON
            # ====================================

            submit_xpath = (
                "//button[contains(., 'Submit application') "
                "or contains(@aria-label, 'Submit application')]"
            )

            submit_btns = safe_find_elements(
                driver,
                By.XPATH,
                submit_xpath
            )

            if submit_btns:

                try:

                    if submit_btns[0].is_displayed():

                        driver.execute_script(
                            "arguments[0].click();",
                            submit_btns[0]
                        )

                        print(
                            ">>> SUCCESS: APPLICATION SUBMITTED"
                        )

                        random_sleep(3, 5)

                        dismiss = safe_find_elements(
                            driver,
                            By.XPATH,
                            "//button[contains(@aria-label, 'Dismiss') "
                            "or contains(., 'Done')]"
                        )

                        if dismiss:

                            driver.execute_script(
                                "arguments[0].click();",
                                dismiss[0]
                            )

                        return True

                except:
                    pass

            # ====================================
            # FORM FILLING
            # ====================================

            form_sections = safe_find_elements(
                driver,
                By.CSS_SELECTOR,
                "div.jobs-easy-apply-form-section__grouping"
            )

            for section in form_sections:

                try:

                    section_text = section.text.lower()

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

                            existing = inp.get_attribute("value")

                            if existing:
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

            # ====================================
            # VALIDATION ERROR
            # ====================================

            errors = safe_find_elements(
                driver,
                By.CSS_SELECTOR,
                ".artdeco-inline-feedback--error"
            )

            if errors:

                print("VALIDATION ERROR FOUND")

                return False

            # ====================================
            # NEXT BUTTON
            # ====================================

            next_xpath = (
                "//button[contains(., 'Next') "
                "or contains(., 'Review') "
                "or contains(@aria-label, 'next')]"
            )

            next_btn = safe_find_elements(
                driver,
                By.XPATH,
                next_xpath
            )

            if next_btn:

                try:

                    if next_btn[0].is_displayed():

                        driver.execute_script(
                            "arguments[0].click();",
                            next_btn[0]
                        )

                        random_sleep(2, 4)

                        continue

                except:
                    pass

            break

        # ====================================
        # CLOSE POPUP SAFELY
        # ====================================

        try:

            close_btn = safe_find_elements(
                driver,
                By.XPATH,
                "//button[contains(@aria-label, 'Dismiss')]"
            )

            if close_btn:

                driver.execute_script(
                    "arguments[0].click();",
                    close_btn[0]
                )

                time.sleep(1)

                confirm = safe_find_elements(
                    driver,
                    By.XPATH,
                    "//button[contains(@data-control-name, 'discard')]"
                )

                if confirm:
                    confirm[0].click()

        except:
            pass

        return False

    except Exception as e:

        print(f"POPUP ERROR: {e}")

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
        # SCROLL PAGE
        # ====================================

        for _ in range(5):

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            random_sleep(2, 4)

        # ====================================
        # JOB CARDS COUNT
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
        # LOOP USING INDEX
        # ====================================

        for index in range(total_jobs_detected):

            if applied_in_this_search >= (
                MAX_APPLICATIONS_PER_DAY
            ):
                break

            try:

                # RELOAD ELEMENTS EVERY LOOP
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
                # SKIP ALREADY APPLIED
                # ====================================

                if "applied" in card_text:

                    already_applied_count += 1

                    continue

                # ====================================
                # JOB ID
                # ====================================

                job_id = card.get_attribute(
                    "data-occludable-job-id"
                )

                if not job_id:

                    try:

                        parent_html = card.get_attribute(
                            "innerHTML"
                        )

                        job_id = str(hash(parent_html))

                    except:
                        continue

                # ====================================
                # DUPLICATE PROTECTION
                # ====================================

                if job_id in processed_jobs:

                    duplicate_jobs += 1

                    print(
                        f"Duplicate skipped: {job_id}"
                    )

                    continue

                if job_id in already_applied_jobs:

                    already_applied_count += 1

                    print(
                        f"Already applied skipped: {job_id}"
                    )

                    continue

                processed_jobs.add(job_id)

                # ====================================
                # CLICK JOB CARD
                # ====================================

                try:

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        card
                    )

                    random_sleep(1, 2)

                    clickable = card.find_element(
                        By.TAG_NAME,
                        "a"
                    )

                    driver.execute_script(
                        "arguments[0].click();",
                        clickable
                    )

                except StaleElementReferenceException:

                    print(
                        "STALE ELEMENT DETECTED - RETRYING"
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
                        f"Job {index + 1}: Easy Apply found."
                    )

                    success = handle_easy_apply_popup(driver)

                    if success:

                        applied_in_this_search += 1

                        save_applied_job(job_id)

                        already_applied_jobs.add(job_id)

                        print(
                            f"Applied Count: "
                            f"{applied_in_this_search}"
                        )

                else:

                    manual_apply_count += 1

                    print(
                        f"Job {index + 1}: Manual Apply"
                    )

                    log_skipped_job(
                        driver.current_url
                    )

                random_sleep(2, 5)

            except Exception as e:

                print(
                    f"JOB ERROR: {e}"
                )

                continue

        # ====================================
        # WRITE REPORT
        # ====================================

        write_keyword_report(
            keyword_set,
            total_jobs_detected,
            easy_apply_count,
            manual_apply_count,
            duplicate_jobs,
            already_applied_count
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

        # CLEAR OLD REPORT FILE

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