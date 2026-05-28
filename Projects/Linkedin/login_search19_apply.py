# =========================
# LINKEDIN EASY APPLY BOT
# Stable Version + Tracking System
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

# ============================================
# CONFIGURATION
# ============================================

EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

MAX_APPLICATIONS_PER_DAY = 30

# r86400 = 24h
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

# ============================================
# HELPERS
# ============================================

def random_sleep(a=2, b=5):
    time.sleep(random.uniform(a, b))


def get_all_active_keywords():

    keyword_list = []

    if not os.path.exists("keywords.txt"):

        print("ALERT: keywords.txt not found")

        return ['"SAP Basis"']

    with open("keywords.txt", "r", encoding="utf-8") as f:

        for line in f:

            clean_line = line.strip()

            if clean_line and not clean_line.startswith("#"):
                keyword_list.append(clean_line)

    return keyword_list


# ============================================
# FILE LOGGERS
# ============================================

def log_manual_job(keyword, title, company, url):

    with open(
        "manual_apply_list.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write(f"DATE: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"KEYWORD: {keyword}\n")
        f.write(f"TITLE: {title}\n")
        f.write(f"COMPANY: {company}\n")
        f.write("STATUS: MANUAL APPLY\n")
        f.write(f"URL: {url}\n")


def log_easy_apply_success(keyword, title, company, url):

    with open(
        "easy_apply_success.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write(f"DATE: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"KEYWORD: {keyword}\n")
        f.write(f"TITLE: {title}\n")
        f.write(f"COMPANY: {company}\n")
        f.write("STATUS: EASY APPLY SUCCESS\n")
        f.write(f"URL: {url}\n")


def log_easy_apply_failed(keyword, title, company, url):

    with open(
        "easy_apply_failed.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write(f"DATE: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"KEYWORD: {keyword}\n")
        f.write(f"TITLE: {title}\n")
        f.write(f"COMPANY: {company}\n")
        f.write("STATUS: EASY APPLY FAILED\n")
        f.write(f"URL: {url}\n")


# ============================================
# KEYWORD REPORT
# ============================================

def write_keyword_report(
    keyword,
    total_jobs,
    easy_apply_jobs,
    manual_jobs,
    success_jobs,
    failed_jobs
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

        f.write(
            f"TOTAL JOBS DETECTED: {total_jobs}\n"
        )

        f.write(
            f"EASY APPLY JOBS: {easy_apply_jobs}\n"
        )

        f.write(
            f"SUCCESSFUL APPLICATIONS: {success_jobs}\n"
        )

        f.write(
            f"FAILED EASY APPLY: {failed_jobs}\n"
        )

        f.write(
            f"MANUAL APPLY JOBS: {manual_jobs}\n"
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

            close_btn = driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label, 'Dismiss')]"
            )

            if close_btn:

                driver.execute_script(
                    "arguments[0].click();",
                    close_btn[0]
                )

                time.sleep(1)

                confirm = driver.find_elements(
                    By.XPATH,
                    "//button[contains(@data-control-name, 'discard')]"
                )

                if confirm:
                    confirm[0].click()

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

    success_count = 0

    failed_count = 0

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

                title = ""
                company = ""

                try:
                    title = card.find_element(
                        By.CSS_SELECTOR,
                        "strong"
                    ).text.strip()
                except:
                    pass

                try:
                    company = card.find_element(
                        By.CSS_SELECTOR,
                        ".artdeco-entity-lockup__subtitle"
                    ).text.strip()
                except:
                    pass

                unique_key = (
                    f"{job_id}_{title}_{company}"
                )

                if unique_key in processed_jobs:

                    print(
                        f"Job {index + 1}: Duplicate Skipped"
                    )

                    continue

                processed_jobs.add(unique_key)

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

                current_url = driver.current_url

                print("\nJOB", index + 1)
                print(f"TITLE: {title}")
                print(f"COMPANY: {company}")
                print(f"URL: {current_url}")

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

                        success_count += 1

                        applied_in_this_search += 1

                        log_easy_apply_success(
                            keyword_set,
                            title,
                            company,
                            current_url
                        )

                        print(
                            "APPLICATION SUCCESS"
                        )

                    else:

                        failed_count += 1

                        log_easy_apply_failed(
                            keyword_set,
                            title,
                            company,
                            current_url
                        )

                        print(
                            "APPLICATION FAILED"
                        )

                else:

                    manual_apply_count += 1

                    print(
                        "Manual Apply"
                    )

                    log_manual_job(
                        keyword_set,
                        title,
                        company,
                        current_url
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
            success_count,
            failed_count
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
            "manual_apply_list.txt",
            "w",
            encoding="utf-8"
        ).close()

        open(
            "easy_apply_success.txt",
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
        print("2. manual_apply_list.txt")
        print("3. easy_apply_success.txt")
        print("4. easy_apply_failed.txt")

        input(
            "\nPress ENTER to close browser..."
        )

        browser.quit()