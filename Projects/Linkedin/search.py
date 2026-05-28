def search_and_select_jobs(driver):
    wait = WebDriverWait(driver, 10)
    
    # 1. Define the Search URL (SAP BASIS + Easy Apply filter)
    search_url = "https://www.linkedin.com/jobs/search/?keywords=SAP%20BASIS&f_AL=true"
    print(f"Navigating to Job Search...")
    driver.get(search_url)
    time.sleep(5) # Let the initial list load

    try:
        # 2. Locate the scrollable sidebar where the job list is
        # We scroll this so LinkedIn loads more results (Lazy Loading)
        job_list_sidebar = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results-list")))
        
        print("Scrolling sidebar to load all 25 jobs...")
        for i in range(3):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", job_list_sidebar)
            time.sleep(1.5)

        # 3. Find all job cards in the list
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        print(f"Found {len(job_cards)} jobs on this page.")

        # 4. Loop through each job one by one
        for index, card in enumerate(job_cards):
            try:
                # Scroll the specific card into view and click it
                driver.execute_script("arguments[0].scrollIntoView();", card)
                card.click()
                time.sleep(2) # Give the right pane time to load details
                
                print(f"Processing job {index + 1}...")
                
                # 5. Check if the 'Easy Apply' button exists in the right pane
                apply_button = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
                
                if apply_button:
                    print("--> Easy Apply found!")
                    # Next step: apply_button[0].click() and fill_form()
                else:
                    print("--> Not an Easy Apply job or already applied.")

            except Exception as e:
                print(f"Error selecting job {index + 1}: {e}")
                continue

    except Exception as e:
        print(f"Critical error in search module: {e}")