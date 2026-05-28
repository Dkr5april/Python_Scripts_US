# =========================
# LINKEDIN EASY APPLY BOT
# Stable Version
# Smart Duplicate Removal
# Exact Keyword Match
# Job URL Tracking
# Fresh DOM Reload Fix
# =========================

import time
import os
import random
import hashlib

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

        return ["SAP Basis Administrator"]

    with open("keywords.txt", "r", encoding="utf-8") as f:

        for line in f:

            clean_line = line.strip()

            if clean_line and not clean_line.startswith("#"):

                clean_line = clean_line.replace('"', '').strip()

                keyword_list.append(clean_line)

    return keyword_list


def exact_phrase_match(job_title, keyword):

    title = (
        job_title
        .lower()
        .replace("-", " ")
        .strip()
    )

    keyword = (
        keyword
        .lower()
        .replace('"', '')
        .strip()
    )

    return keyword in title


def normalize_text(text):

    if not text:
        return ""

    text = text.lower()

    replacements = [
        "s/4hana",
        "s4 hana",
        "hana",
        "lead",
        "senior",
        "principal",
        "production",
        "support",
        "admin",
        "administrator",
        "consultant",
        "engineer"
    ]

    for r in replacements:
        text = text.replace(r, "")

    return " ".join(text.split())


def create_job_signature(title, company):

    clean_title = normalize_text(title)

    clean_company = normalize_text(company)

    combined = f"{clean_title}_{clean_company}"

    return hashlib.md5(
        combined.encode("utf-8")
    ).hexdigest()


def extract_job_id(job_url):

    try:

        if "currentJobId=" in job_url:

            return (
                job_url
                .split("currentJobId=")[1]
                .split("&")[0]
            )

    except:
        pass

    return ""


def load_processed_jobs():

    if not os.path.exists("processed_jobs.txt"):
        return set()

    with open(
        "processed_jobs.txt",
        "r",
        encoding="utf-8"
    ) as f:

        return set(
            line.strip()
            for line in f
            if line.strip()
        )


def save_processed_job(signature):

    with open(
        "processed_jobs.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(signature + "\n")


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
# EASY APPLY JOB LIST
# ============================================

def log_easy_apply_job(
    keyword,
    title,
    company,
    job_url,
    status
):

    with open(
        "easy_apply_jobs.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 80)
        f.write("\n")

        f.write(
            f"TIME: "
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        f.write(
            f"KEYWORD: {keyword}\n"
        )

        f.write(
            f"TITLE: {title}\n"
        )

        f.write(
            f"COMPANY: {company}\n"
        )

        f.write(
            f"STATUS: {status}\n"
        )

        f.write(
            f"JOB URL: {job_url}\n"
        )

        f.write("=" * 80)
        f.write("\n")


def save_job_details(
    keyword,
    title,
    company,
    job_url,
    status
):

    with open(
        "all_jobs_today.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write("\n")
        f.write("=" * 80)
        f.write("\n")

        f.write(
            f"TIME: "
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        f.write(
            f"KEYWORD: {keyword}\n"
        )

        f.write(
            f"TITLE: {title}\n"
        )

        f.write(
            f"COMPANY: {company}\n"
        )

        f.write(
            f"STATUS: {status}\n"
        )

        f.write(
            f"JOB URL: {job_url}\n"
        )

        f.write("=" * 80)
        f.write("\n")


# ============================================
# KEYWORD REPORT
# ============================================

def write_keyword_report(
    keyword,
    total_jobs,
    easy_apply_jobs,
    successful_applies,
    manual_jobs,
    duplicates_skipped,
    already_applied_skipped
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
            f'KEYWORD: "{keyword}"\n'
        )

        f.write(
            f"TOTAL JOBS DETECTED: {total_jobs}\n"
        )

        f.write(
            f"EASY APPLY FOUND: {easy_apply_jobs}\n"
        )

        f.write(
            f"SUCCESSFUL APPLIES: "
            f"{successful_applies}\n"
        )

        f.write(
            f"MANUAL APPLY JOBS: "
            f"{manual_jobs}\n"
        )

        f.write(
            f"DUPLICATES SKIPPED: "
            f"{duplicates_skipped}\n"
        )

        f.write(
            f"ALREADY APPLIED SKIPPED: "
            f"{already_applied_skipped}\n"
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

    duplicates_skipped = 0

    already_applied_skipped = 0

    search_url = (
        "https://www.linkedin.com/jobs/search/"
        f'?keywords="%s"' % keyword_set.replace(' ', '%20')
        + "&location=United%20States"
        + f"&f_TPR={TIMEFRAME_CODE}"
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

        initial_cards = driver.find_elements(
            By.CSS_SELECTOR,
            ".job-card-container, "
            "[data-occludable-job-id], "
            ".jobs-search-results-list__list-item"
        )

        total_jobs_detected = len(initial_cards)

        print(
            f"Detected {total_jobs_detected} job cards."
        )

        for index in range(total_jobs_detected):

            if applied_in_this_search >= (
                MAX_APPLICATIONS_PER_DAY
            ):
                break

            try:

                job_cards = driver.find_elements(
                    By.CSS_SELECTOR,
                    ".job-card-container, "
                    "[data-occludable-job-id], "
                    ".jobs-search-results-list__list-item"
                )

                if index >= len(job_cards):
                    break

                card = job_cards[index]

                card_text = card.text.lower()

                if "applied" in card_text:

                    already_applied_skipped += 1

                    print(
                        f"Job {index + 1}: Already Applied"
                    )

                    continue

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

                job_url = driver.current_url

                job_id = extract_job_id(job_url)

                if job_id:

                    signature = job_id

                else:

                    signature = create_job_signature(
                        title,
                        company
                    )

                if signature in processed_jobs:

                    duplicates_skipped += 1

                    print(
                        f"Job {index + 1}: Duplicate Skipped"
                    )

                    continue

                processed_jobs.add(signature)

                save_processed_job(signature)

                print(
                    f"\nJOB {index + 1}"
                )

                print(
                    f"TITLE: {title}"
                )

                print(
                    f"COMPANY: {company}"
                )

                print(
                    f"URL: {job_url}"
                )

                # ====================================
                # EXACT KEYWORD MATCH FILTER
                # ====================================

                if not exact_phrase_match(
                    title,
                    keyword_set
                ):

                    print(
                        "Skipped: Exact keyword not found in title"
                    )

                    continue

                # ====================================
                # EASY APPLY CHECK
                # ====================================

                easy_apply_buttons = driver.find_elements(
                    By.XPATH,
                    "//button[contains(@aria-label,'Easy Apply')]"
                )

                if easy_apply_buttons:

                    easy_apply_count += 1

                    print(
                        "Easy Apply found."
                    )

                    log_easy_apply_job(
                        keyword_set,
                        title,
                        company,
                        job_url,
                        "EASY APPLY FOUND"
                    )

                    success = handle_easy_apply_popup(driver)

                    if success:

                        applied_in_this_search += 1

                        save_job_details(
                            keyword_set,
                            title,
                            company,
                            job_url,
                            "APPLIED"
                        )

                        print(
                            f"Applied Count: "
                            f"{applied_in_this_search}"
                        )

                    else:

                        save_job_details(
                            keyword_set,
                            title,
                            company,
                            job_url,
                            "EASY APPLY FAILED"
                        )

                else:

                    manual_apply_count += 1

                    print(
                        "Manual Apply"
                    )

                    log_skipped_job(job_url)

                    save_job_details(
                        keyword_set,
                        title,
                        company,
                        job_url,
                        "MANUAL APPLY"
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
            applied_in_this_search,
            manual_apply_count,
            duplicates_skipped,
            already_applied_skipped
        )

    except Exception as e:

        print(f"SEARCH ERROR: {e}")

    return applied_in_this_search


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    processed_jobs = load_processed_jobs()

    browser = linkedin_login()

    if browser:

        open(
            "keyword_report.txt",
            "w",
            encoding="utf-8"
        ).close()

        open(
            "all_jobs_today.txt",
            "w",
            encoding="utf-8"
        ).close()

        open(
            "easy_apply_jobs.txt",
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
        print("3. all_jobs_today.txt")
        print("4. processed_jobs.txt")
        print("5. easy_apply_jobs.txt")

        input(
            "\nPress ENTER to close browser..."
        )

        browser.quit()