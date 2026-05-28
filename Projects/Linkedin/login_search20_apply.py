# =========================
# LINKEDIN EASY APPLY BOT
# FINAL STABLE VERSION
# =========================

import time
import os
import random
import urllib.parse

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

# Time filters:
# r86400 = 24h
# r604800 = 7d
# r1296000 = 15d
# r2592000 = 1 month

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
# JOB FILTERS
# ============================================

ALLOWED_KEYWORDS = [
    "sap basis",
    "basis",
    "hana",
    "s4",
    "s/4",
    "rise",
    "migration",
    "netweaver",
    "technical consultant",
    "basis administrator",
    "basis lead",
    "basis architect",
    "basis support",
    "production support",
    "upgrade",
    "cloud",
    "aws",
    "azure"
]

BLOCKED_KEYWORDS = [
    "security",
    "frontend",
    "salesforce",
    "oracle",
    "java",
    "python developer",
    "data engineer",
    "workday",
    "servicenow",
    "ui developer",
    "react developer"
]

# ============================================
# GLOBALS
# ============================================

processed_jobs = set()

# ============================================
# HELPERS
# ============================================

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))


def get_all_active_keywords():

    keyword_list = []

    if not os.path.exists("keywords.txt"):

        print("ALERT: keywords.txt not found")

        return ["SAP Basis"]

    with open("keywords.txt", "r", encoding="utf-8") as f:

        for line in f:

            clean_line = line.strip()

            if clean_line and not clean_line.startswith("#"):
                keyword_list.append(
                    clean_line.replace('"', '')
                )

    return keyword_list


def log_skipped_job(job_url, title, company):

    with open(
        "manual_apply_jobs.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        f.write(f"TITLE: {title}\n")
        f.write(f"COMPANY: {company}\n")
        f.write(f"URL: {job_url}\n")
        f.write("-" * 60)
        f.write("\n")


def log_failed_easy_apply(job_url, title, company):

    with open(
        "easy_apply_failed.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        f.write(f"TITLE: {title}\n")
        f.write(f"COMPANY: {company}\n")
        f.write(f"URL: {job_url}\n")
        f.write("-" * 60)
        f.write("\n")


# ============================================
# KEYWORD REPORT
# ============================================

def write_keyword_report(
    keyword,
    total_jobs,
    easy_apply_jobs,
    manual_jobs,
    filtered_jobs,
    duplicates
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
            f"FILTERED OUT JOBS: {filtered_jobs}\n"
        )

        f.write(
            f"DUPLICATES SKIPPED: {duplicates}\n"
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

            submit_xpath = (
                "//button[contains(., 'Submit application') "
                "or contains(@aria-label, 'Submit application')]"
            )

            submit_btns = driver.find_elements(
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

                        dismiss = driver.find_elements(
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

            form_sections = driver.find_elements(
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

            errors = driver.find_elements(
                By.CSS_SELECTOR,
                ".artdeco-inline-feedback--error"
            )

            if errors:

                print("VALIDATION ERROR FOUND")

                return False

            next_xpath = (
                "//button[contains(., 'Next') "
                "or contains(., 'Review') "
                "or contains(@aria-label, 'next')]"
            )

            next_btn = driver.find_elements(
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

    filtered_jobs = 0

    duplicate_jobs = 0

    encoded_keyword = urllib.parse.quote(keyword_set)

    search_url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={encoded_keyword}"
        "&location=United%20States"
        "&f_AL=true"
        f"&f_TPR={TIMEFRAME_CODE}"
    )

    print(f"\n--- SEARCHING FOR: \"{keyword_set}\" ---")

    driver.get(search_url)

    random_sleep(6, 9)

    try:

        for _ in range(5):

            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            random_sleep(2, 4)

        job_cards = driver.find_elements(
            By.CSS_SELECTOR,
            ".job-card-container, "
            "[data-occludable-job-id], "
            ".jobs-search-results-list__list-item"
        )

        total_jobs_detected = len(job_cards)

        print(
            f"Detected {total_jobs_detected} job cards."
        )

        for index, card in enumerate(job_cards):

            if applied_in_this_search >= (
                MAX_APPLICATIONS_PER_DAY
            ):
                break

            try:

                if "applied" in (
                    card.text.lower()
                ):
                    continue

                job_id = card.get_attribute(
                    "data-occludable-job-id"
                )

                if not job_id:
                    continue

                if job_id in processed_jobs:

                    duplicate_jobs += 1

                    print(
                        f"Job {index + 1}: Duplicate Skipped"
                    )

                    continue

                processed_jobs.add(job_id)

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

                random_sleep(3, 5)

                title = ""

                company = ""

                try:
                    title = driver.find_element(
                        By.CSS_SELECTOR,
                        "h1"
                    ).text.strip()
                except:
                    title = "Unknown"

                try:
                    company = driver.find_element(
                        By.CSS_SELECTOR,
                        ".job-details-jobs-unified-top-card__company-name"
                    ).text.strip()
                except:
                    company = "Unknown"

                current_url = driver.current_url

                print("\nJOB", index + 1)
                print("TITLE:", title)
                print("COMPANY:", company)
                print("URL:", current_url)

                title_lower = title.lower()

                valid = any(
                    k in title_lower
                    for k in ALLOWED_KEYWORDS
                )

                blocked = any(
                    b in title_lower
                    for b in BLOCKED_KEYWORDS
                )

                if not valid or blocked:

                    filtered_jobs += 1

                    print("Filtered Out")

                    continue

                easy_apply_buttons = driver.find_elements(
                    By.XPATH,
                    "//button[contains(@aria-label,'Easy Apply')]"
                )

                if easy_apply_buttons:

                    easy_apply_count += 1

                    print(
                        "Easy Apply detected. Attempting apply..."
                    )

                    success = handle_easy_apply_popup(driver)

                    if success:

                        applied_in_this_search += 1

                        print(
                            f"Applied Count: "
                            f"{applied_in_this_search}"
                        )

                    else:

                        print(
                            "Easy Apply FAILED - logged."
                        )

                        log_failed_easy_apply(
                            current_url,
                            title,
                            company
                        )

                else:

                    manual_apply_count += 1

                    print("Manual Apply")

                    log_skipped_job(
                        current_url,
                        title,
                        company
                    )

                random_sleep(2, 5)

            except Exception as e:

                print(
                    f"JOB ERROR: {e}"
                )

                continue

        write_keyword_report(
            keyword_set,
            total_jobs_detected,
            easy_apply_count,
            manual_apply_count,
            filtered_jobs,
            duplicate_jobs
        )

    except Exception as e:

        print(f"SEARCH ERROR: {e}")

    return applied_in_this_search

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    browser = linkedin_login()

    if browser:

        open(
            "keyword_report.txt",
            "w",
            encoding="utf-8"
        ).close()

        open(
            "manual_apply_jobs.txt",
            "w",
            encoding="utf-8"
        ).close()

        open(
            "easy_apply_failed.txt",
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
        print("2. manual_apply_jobs.txt")
        print("3. easy_apply_failed.txt")

        input(
            "\nPress ENTER to close browser..."
        )

        browser.quit()