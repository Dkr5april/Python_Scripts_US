# =========================
# LINKEDIN EASY APPLY BOT
# Hybrid Stable Version
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
# LOGIN MODULE
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

        for _ in range(15):

            # =================================
            # SUBMIT APPLICATION
            # =================================

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

            # =================================
            # FORM SECTIONS
            # =================================

            form_sections = driver.find_elements(
                By.CSS_SELECTOR,
                "div.jobs-easy-apply-form-section__grouping"
            )

            for section in form_sections:

                try:

                    section_text = section.text.lower()

                    # -------------------------
                    # TEXT INPUTS
                    # -------------------------

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

                    # -------------------------
                    # DROPDOWNS
                    # -------------------------

                    dropdowns = section.find_elements(
                        By.TAG_NAME,
                        "select"
                    )

                    for dd in dropdowns:

                        options = dd.find_elements(
                            By.TAG_NAME,
                            "option"
                        )

                        if len(options) > 1:

                            for opt in options:

                                txt = opt.text.lower()

                                if "yes" in txt:

                                    opt.click()

                                    break

                    # -------------------------
                    # RADIO BUTTONS
                    # -------------------------

                    radios = section.find_elements(
                        By.CSS_SELECTOR,
                        "input[type='radio']"
                    )

                    for radio in radios:

                        value = (
                            radio.get_attribute("value") or ""
                        ).lower()

                        if "yes" in value:

                            driver.execute_script(
                                "arguments[0].click();",
                                radio
                            )

                            break

                    # -------------------------
                    # CHECKBOXES
                    # -------------------------

                    checks = section.find_elements(
                        By.CSS_SELECTOR,
                        "input[type='checkbox']"
                    )

                    for chk in checks:

                        if not chk.is_selected():

                            driver.execute_script(
                                "arguments[0].click();",
                                chk
                            )

                except:
                    continue

            # =================================
            # VALIDATION ERRORS
            # =================================

            errors = driver.find_elements(
                By.CSS_SELECTOR,
                ".artdeco-inline-feedback--error"
            )

            if errors:

                print("VALIDATION ERROR FOUND")

                return False

            # =================================
            # NEXT BUTTON
            # =================================

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

            # =================================
            # CLOSE POPUP IF STUCK
            # =================================

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

    wait = WebDriverWait(driver, 30)

    applied_in_this_search = 0

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

        sidebar_selectors = [
            (
                By.CLASS_NAME,
                "jobs-search-results-list"
            ),
            (
                By.CSS_SELECTOR,
                ".scaffold-layout__list-container"
            ),
            (
                By.TAG_NAME,
                "main"
            )
        ]

        sidebar = None

        for selector_type, selector_val in sidebar_selectors:

            try:

                elements = driver.find_elements(
                    selector_type,
                    selector_val
                )

                if elements:

                    sidebar = elements[0]

                    break

            except:
                continue

        if not sidebar:

            if "no matching jobs" in (
                driver.page_source.lower()
            ):

                print(
                    f"No results for {keyword_set}"
                )

                return 0

            raise Exception(
                "Job sidebar not found"
            )

        # ====================================
        # SCROLL JOB LIST
        # ====================================

        for _ in range(5):

            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight",
                sidebar
            )

            random_sleep(2, 4)

        # ====================================
        # JOB CARDS
        # ====================================

        job_cards = driver.find_elements(
            By.CSS_SELECTOR,
            ".job-card-container, "
            "[data-occludable-job-id], "
            ".jobs-search-results-list__list-item"
        )

        print(
            f"Detected {len(job_cards)} job cards."
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

                # ====================================
                # RIGHT PANE
                # ====================================

                right_pane = driver.find_element(
                    By.CLASS_NAME,
                    "jobs-search__job-details--container"
                )

                if "easy apply" in (
                    right_pane.text.lower()
                ):

                    print(
                        f"Job {index + 1}: Easy Apply found."
                    )

                    if handle_easy_apply_popup(driver):

                        applied_in_this_search += 1

                        print(
                            f"Applied Count: "
                            f"{applied_in_this_search}"
                        )

                else:

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

    except Exception as e:

        print(f"SEARCH ERROR: {e}")

    return applied_in_this_search

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    if not EMAIL or not PASSWORD:

        print("\nSET ENVIRONMENT VARIABLES\n")

        print(
            "set LINKEDIN_EMAIL=yourmail@gmail.com"
        )

        print(
            "set LINKEDIN_PASSWORD=yourpassword"
        )

        exit()

    browser = linkedin_login()

    if browser:

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

        input(
            "Press ENTER to close browser..."
        )

        browser.quit()