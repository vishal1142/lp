/// this is 1st running fine code //

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import yaml
import os

class LinkedInSearch:
    def __init__(self, browser_manager, config_path='config/config.yaml'):
        self.browser = browser_manager
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['linkedin']
        self.locators = [
            (By.XPATH, "//input[@role='combobox']"),
            (By.CSS_SELECTOR, "input[role='combobox']"),
            (By.XPATH, "//input[contains(@class, 'search-global-typeahead')]"),
            (By.XPATH, "//input[@aria-label='Search']"),
            (By.XPATH, "//input[@type='text' and contains(@id, 'search')]")
        ]
    
    def _debug_page(self, message):
        """Helper method for debugging"""
        timestamp = int(time.time())
        screenshot_path = f"debug/debug_{timestamp}.png"
        source_path = f"debug/page_source_{timestamp}.html"
        
        # Create debug directory if it doesn't exist
        os.makedirs("debug", exist_ok=True)
        
        # Save screenshot and page source
        self.browser.driver.save_screenshot(screenshot_path)
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(self.browser.driver.page_source)
        
        print(f"{message}\nDebug files saved to: {screenshot_path}, {source_path}")
        print(f"Current URL: {self.browser.driver.current_url}")

    def _find_with_multiple_locators(self, timeout=10):
        """Solution 1: Try multiple locators with explicit waits"""
        for by, locator in self.locators:
            try:
                element = WebDriverWait(self.browser.driver, timeout).until(
                    EC.presence_of_element_located((by, locator))
                )
                return element
            except TimeoutException:
                continue
        raise NoSuchElementException(f"Could not find search box with any of these locators: {self.locators}")

    def _check_frames(self, timeout=5):
        """Solution 2: Check if element is inside an iframe"""
        try:
            # Try in main content first
            return self._find_with_multiple_locators(timeout)
        except NoSuchElementException:
            # Get all iframes and try each one
            frames = self.browser.driver.find_elements(By.TAG_NAME, "iframe")
            for frame in frames:
                try:
                    self.browser.driver.switch_to.frame(frame)
                    element = self._find_with_multiple_locators(timeout)
                    return element
                except NoSuchElementException:
                    self.browser.driver.switch_to.default_content()
                    continue
                finally:
                    self.browser.driver.switch_to.default_content()
            raise NoSuchElementException("Search box not found in main content or any iframes")

    def _wait_for_page_complete(self, timeout=30):
        """Solution 3: Wait for page to fully load"""
        try:
            WebDriverWait(self.browser.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except TimeoutException:
            self._debug_page("Page load timed out")
            raise

    def _retry_with_refresh(self, max_attempts=3):
        """Solution 4: Retry with page refresh"""
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    self.browser.driver.refresh()
                    time.sleep(3)
                return self._find_with_multiple_locators()
            except NoSuchElementException:
                if attempt == max_attempts - 1:
                    raise
                continue

    def _js_fallback(self):
        """Solution 5: JavaScript fallback approach"""
        try:
            # Try to find the element via JavaScript
            element = self.browser.driver.execute_script(
                """
                const selectors = [
                    'input[role="combobox"]',
                    'input.search-global-typeahead',
                    'input[aria-label="Search"]'
                ];
                
                for (const selector of selectors) {
                    const el = document.querySelector(selector);
                    if (el) return el;
                }
                return null;
                """
            )
            if element:
                return element
            raise NoSuchElementException("Search box not found via JavaScript")
        except Exception as e:
            raise NoSuchElementException(f"JavaScript fallback failed: {str(e)}")

    def login(self):
        driver = self.browser.driver
        driver.get(self.config['login_url'])
        
        # Wait for page to load completely
        self._wait_for_page_complete()
        
        # Enter credentials with retry logic
        try:
            self.browser.safe_send_keys((By.ID, 'username'), self.config['credentials']['username'])
            self.browser.safe_send_keys((By.ID, 'password'), self.config['credentials']['password'])
            self.browser.safe_click((By.XPATH, "//button[@type='submit']"))
        except Exception as e:
            self._debug_page(f"Login failed: {str(e)}")
            raise
        
        # Wait for login to complete using multiple approaches
        try:
            # Approach 1: Try the standard way first
            self.browser.wait_for_element((By.XPATH, "//input[@role='combobox']"), 20)
        except TimeoutException:
            try:
                # Approach 2: Try alternative locators
                self._find_with_multiple_locators(20)
            except NoSuchElementException:
                try:
                    # Approach 3: Check if in iframe
                    self._check_frames(10)
                except NoSuchElementException:
                    try:
                        # Approach 4: Try JavaScript fallback
                        self._js_fallback()
                    except NoSuchElementException:
                        self._debug_page("All search box location attempts failed")
                        raise
    
    def perform_search(self):
        driver = self.browser.driver
        params = self.config['search_parameters']
        
        # Navigate to search page with retry logic
        for attempt in range(3):
            try:
                driver.get(self.config['search_url'])
                self._wait_for_page_complete()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(2)
        
        time.sleep(self.config['limits']['delay_between_actions'])
        
        # Enter search parameters with robust element finding
        if 'keywords' in params:
            try:
                # Try primary approach first
                search_box = self._find_with_multiple_locators()
                search_box.clear()
                search_box.send_keys(params['keywords'])
                search_box.send_keys(Keys.RETURN)
                time.sleep(self.config['limits']['delay_between_actions'])
            except NoSuchElementException:
                try:
                    # Fallback to JavaScript approach
                    search_box = self._js_fallback()
                    driver.execute_script("arguments[0].value = arguments[1];", search_box, params['keywords'])
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", search_box)
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(self.config['limits']['delay_between_actions'])
                except Exception as e:
                    self._debug_page(f"Failed to enter search keywords: {str(e)}")
                    raise
        
        # Apply filters
        self._apply_filters(params)
        
        # Collect results
        return self._collect_results()
    
    def _apply_filters(self, params):
        # Example filter application (location)
        if 'location' in params:
            try:
                self.browser.safe_click((By.XPATH, "//button[contains(@aria-label, 'Location filter')]"))
                time.sleep(1)
                
                location_input = self.browser.wait_for_element((By.XPATH, "//input[@aria-label='Add a location filter']"))
                location_input.send_keys(params['location'])
                time.sleep(1)
                location_input.send_keys(Keys.RETURN)
                time.sleep(self.config['limits']['delay_between_actions'])
            except Exception as e:
                print(f"Failed to apply location filter: {e}")
    
    def _collect_results(self):
        results = []
        max_profiles = self.config['limits']['max_profiles_per_search']
        collected = 0
        
        while collected < max_profiles:
            # Scroll to load more results
            self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.config['limits']['delay_between_actions'])
            
            # Find profile elements with error handling
            try:
                profile_elements = self.browser.driver.find_elements(By.XPATH, "//li[contains(@class, 'reusable-search__result-container')]")
            except Exception as e:
                print(f"Error finding profile elements: {e}")
                self._debug_page("Error during profile collection")
                break
            
            for element in profile_elements[collected:]:
                if collected >= max_profiles:
                    break
                
                try:
                    # Extract basic info with robust selectors
                    name = element.find_element(By.XPATH, ".//span[@dir='ltr']/span[1]").text
                    headline = element.find_element(By.XPATH, ".//div[contains(@class, 'entity-result__primary-subtitle')]").text
                    
                    results.append({
                        'name': name,
                        'headline': headline,
                        'element': element
                    })
                    collected += 1
                except Exception as e:
                    print(f"Error extracting profile info: {e}")
                    continue
            
            # Check if we've reached the end
            if len(profile_elements) >= max_profiles or not self._has_more_results():
                break
        
        return results
    
    def _has_more_results(self):
        try:
            return self.browser.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Next')]").is_enabled()
        except:
            return False



==================================================================================================================================

linkedin:
  login_url: "https://www.linkedin.com/login"
  search_url: "https://www.linkedin.com/search/results/people/"
  credentials:
    username: "vishalmachan031997@gmail.com"
    password: "DevOps@12"
  search_parameters:
    keywords: "Software Engineer"
    location: "San Francisco"
    connection_level: "2nd"
    current_company: "Google"
  limits:
    max_profiles_per_search: 50
    delay_between_actions: 3

ocr:
  tesseract_path: "/usr/bin/tesseract"
  confidence_threshold: 70


==================================================================================================================================

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import yaml
import os
from enum import Enum

class SearchType(Enum):
    PEOPLE = 1
    JOBS = 2

class LinkedInSearch:
    def __init__(self, browser_manager, config_path='config/config.yaml'):
        """Initialize LinkedIn search with configuration"""
        self.browser = browser_manager
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.config = config.get('linkedin', {})
                self.ocr_config = config.get('ocr', {})
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

        self.search_locators = {
            SearchType.PEOPLE: [
                (By.XPATH, "//input[@role='combobox']"),
                (By.CSS_SELECTOR, "input[role='combobox']"),
                (By.XPATH, "//input[contains(@class, 'search-global-typeahead')]"),
                (By.XPATH, "//input[@aria-label='Search']"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'search')]")
            ],
            SearchType.JOBS: [
                (By.XPATH, "//input[contains(@aria-label, 'Search job titles or companies')]"),
                (By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]"),
                (By.CSS_SELECTOR, "input.jobs-search-box__text-input")
            ]
        }

    def _debug_page(self, message):
        """Save debug information when errors occur"""
        try:
            timestamp = int(time.time())
            debug_dir = "debug"
            os.makedirs(debug_dir, exist_ok=True)
            
            screenshot_path = os.path.join(debug_dir, f"debug_{timestamp}.png")
            source_path = os.path.join(debug_dir, f"page_source_{timestamp}.html")
            
            self.browser.driver.save_screenshot(screenshot_path)
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(self.browser.driver.page_source)
            
            print(f"{message}\nDebug files saved to:\n- {screenshot_path}\n- {source_path}")
            print(f"Current URL: {self.browser.driver.current_url}")
        except Exception as e:
            print(f"Failed to save debug information: {str(e)}")

    def _find_element_with_retry(self, locator, timeout=10, max_attempts=3):
        """Find element with retry logic"""
        for attempt in range(max_attempts):
            try:
                return WebDriverWait(self.browser.driver, timeout).until(
                    EC.presence_of_element_located(locator))
            except TimeoutException:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(2)
                continue

    def _find_search_box(self, search_type, timeout=10):
        """Find search box using multiple possible locators"""
        for by, locator in self.search_locators[search_type]:
            try:
                return self._find_element_with_retry((by, locator), timeout)
            except TimeoutException:
                continue
        raise NoSuchElementException(f"Could not find search box with any locators for {search_type}")

    def _wait_for_page_complete(self, timeout=30):
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.browser.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            self._debug_page("Page load timed out")
            raise

    def login(self):
        """Login to LinkedIn with credentials from config"""
        try:
            self.browser.driver.get(self.config.get('login_url', 'https://www.linkedin.com/login'))
            self._wait_for_page_complete()
            
            # Input credentials
            username = self.config.get('credentials', {}).get('username')
            password = self.config.get('credentials', {}).get('password')
            
            if not username or not password:
                raise ValueError("Username or password not configured")
            
            self.browser.safe_send_keys((By.ID, 'username'), username)
            self.browser.safe_send_keys((By.ID, 'password'), password)
            self.browser.safe_click((By.XPATH, "//button[@type='submit']"))
            
            # Verify login success
            try:
                WebDriverWait(self.browser.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@role='combobox'] | //input[contains(@aria-label, 'Search job titles')]")))
            except TimeoutException:
                self._debug_page("Login verification failed")
                raise Exception("Login verification failed - could not find post-login elements")
                
        except Exception as e:
            self._debug_page(f"Login failed: {str(e)}")
            raise

    def perform_job_search(self):
        """Perform job search with configured parameters"""
        try:
            params = self.config.get('job_search_parameters', {})
            if not params:
                raise ValueError("No job search parameters configured")
            
            # Navigate to jobs page
            self.browser.driver.get(self.config.get('jobs_url', 'https://www.linkedin.com/jobs/search/'))
            self._wait_for_page_complete()
            time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
            
            # Enter search keywords
            if 'keywords' in params:
                search_box = self._find_search_box(SearchType.JOBS)
                search_box.clear()
                search_box.send_keys(params['keywords'])
                search_box.send_keys(Keys.RETURN)
                time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
            
            # Apply filters
            self._apply_job_filters(params)
            
            # Collect results
            return self._collect_job_results()
            
        except Exception as e:
            self._debug_page(f"Job search failed: {str(e)}")
            raise

    def _apply_job_filters(self, params):
        """Apply all configured job filters"""
        try:
            if 'location' in params:
                self._apply_job_filter('location', params['location'])
            
            if 'experience_level' in params:
                self._apply_job_filter('experience', params['experience_level'])
            
            if 'job_type' in params:
                self._apply_job_filter('job_type', params['job_type'])
                
        except Exception as e:
            print(f"Warning: Failed to apply some job filters: {str(e)}")

    def _apply_job_filter(self, filter_type, value):
        """Apply specific job filter type"""
        try:
            filter_map = {
                'location': {
                    'button': "//button[contains(@aria-label, 'Location filter')]",
                    'input': "//input[@aria-label='City, state, or zip code']",
                    'select_first': True
                },
                'experience': {
                    'button': "//button[contains(@aria-label, 'Experience level filter')]",
                    'option': {
                        '1': "Internship",
                        '2': "Entry level",
                        '3': "Associate",
                        '4': "Mid-Senior level",
                        '5': "Director",
                        '6': "Executive"
                    }
                },
                'job_type': {
                    'button': "//button[contains(@aria-label, 'Job type filter')]",
                    'option': {
                        'F': "Full-time",
                        'P': "Part-time",
                        'C': "Contract",
                        'T': "Temporary",
                        'I': "Internship",
                        'V': "Volunteer"
                    }
                }
            }
            
            config = filter_map.get(filter_type)
            if not config:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            # Click filter button
            self.browser.safe_click((By.XPATH, config['button']))
            time.sleep(1)
            
            # Handle different filter types
            if filter_type == 'location':
                self.browser.safe_send_keys((By.XPATH, config['input']), value)
                time.sleep(1)
                if config.get('select_first', False):
                    self.browser.safe_click((By.XPATH, "//div[contains(@class, 'basic-typeahead__selectable')][1]"))
            
            elif filter_type in ['experience', 'job_type']:
                option_text = config['option'].get(str(value))
                if not option_text:
                    raise ValueError(f"Invalid {filter_type} value: {value}")
                
                option_xpath = f"//label[contains(., '{option_text}')]"
                self.browser.safe_click((By.XPATH, option_xpath))
            
            # Apply the filter
            self.browser.safe_click((By.XPATH, "//button[contains(@aria-label, 'Apply current filter')]"))
            time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
            
        except Exception as e:
            print(f"Failed to apply {filter_type} filter: {str(e)}")
            raise

    def _collect_job_results(self):
        """Collect and return job search results"""
        results = []
        max_jobs = self.config.get('limits', {}).get('max_jobs', 50)
        collected = 0
        
        try:
            while collected < max_jobs:
                # Scroll to load more results
                self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
                
                # Find job elements
                job_elements = self.browser.driver.find_elements(
                    By.XPATH, "//li[contains(@class, 'jobs-search-results__list-item')]")
                
                # Process new jobs
                for element in job_elements[collected:]:
                    if collected >= max_jobs:
                        break
                    
                    try:
                        job_info = {
                            'title': element.find_element(
                                By.XPATH, ".//a[contains(@class, 'job-card-list__title')]").text,
                            'company': element.find_element(
                                By.XPATH, ".//span[contains(@class, 'job-card-container__primary-description')]").text,
                            'location': element.find_element(
                                By.XPATH, ".//li[contains(@class, 'job-card-container__metadata-item')]").text,
                            'link': element.find_element(
                                By.XPATH, ".//a[contains(@class, 'job-card-list__title')]").get_attribute('href'),
                            'element': element
                        }
                        results.append(job_info)
                        collected += 1
                    except Exception as e:
                        print(f"Error extracting job info: {str(e)}")
                        continue
                
                # Check if we've reached the end
                if len(job_elements) >= max_jobs or not self._has_more_jobs():
                    break
                    
        except Exception as e:
            print(f"Error during job collection: {str(e)}")
            self._debug_page("Error during job collection")
        
        return results

    def _has_more_jobs(self):
        """Check if more job results are available"""
        try:
            return self.browser.driver.find_element(
                By.XPATH, "//button[contains(@aria-label, 'Next') and contains(@class, 'pagination')]").is_enabled()
        except:
            return False

    def perform_people_search(self):
        """Perform people search with configured parameters"""
        try:
            params = self.config.get('search_parameters', {})
            if not params:
                print("No people search parameters configured")
                return []
            
            # Navigate to search page
            self.browser.driver.get(self.config.get('search_url', 'https://www.linkedin.com/search/results/people/'))
            self._wait_for_page_complete()
            time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
            
            # Enter search keywords
            if 'keywords' in params:
                search_box = self._find_search_box(SearchType.PEOPLE)
                search_box.clear()
                search_box.send_keys(params['keywords'])
                search_box.send_keys(Keys.RETURN)
                time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
            
            # Apply filters
            self._apply_people_filters(params)
            
            # Collect results
            return self._collect_people_results()
            
        except Exception as e:
            self._debug_page(f"People search failed: {str(e)}")
            raise

    def _apply_people_filters(self, params):
        """Apply filters for people search"""
        try:
            if 'location' in params:
                self.browser.safe_click((By.XPATH, "//button[contains(@aria-label, 'Location filter')]"))
                time.sleep(1)
                
                location_input = self._find_element_with_retry(
                    (By.XPATH, "//input[@aria-label='Add a location filter']"))
                location_input.send_keys(params['location'])
                time.sleep(1)
                location_input.send_keys(Keys.RETURN)
                time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
        except Exception as e:
            print(f"Failed to apply people filters: {str(e)}")

    def _collect_people_results(self):
        """Collect and return people search results"""
        results = []
        max_profiles = self.config.get('limits', {}).get('max_profiles_per_search', 50)
        collected = 0
        
        try:
            while collected < max_profiles:
                # Scroll to load more results
                self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.config.get('limits', {}).get('delay_between_actions', 3))
                
                # Find profile elements
                profile_elements = self.browser.driver.find_elements(
                    By.XPATH, "//li[contains(@class, 'reusable-search__result-container')]")
                
                # Process new profiles
                for element in profile_elements[collected:]:
                    if collected >= max_profiles:
                        break
                    
                    try:
                        profile_info = {
                            'name': element.find_element(
                                By.XPATH, ".//span[@dir='ltr']/span[1]").text,
                            'headline': element.find_element(
                                By.XPATH, ".//div[contains(@class, 'entity-result__primary-subtitle')]").text,
                            'element': element
                        }
                        results.append(profile_info)
                        collected += 1
                    except Exception as e:
                        print(f"Error extracting profile info: {str(e)}")
                        continue
                
                # Check if we've reached the end
                if len(profile_elements) >= max_profiles or not self._has_more_people_results():
                    break
                    
        except Exception as e:
            print(f"Error during people collection: {str(e)}")
            self._debug_page("Error during people collection")
        
        return results

    def _has_more_people_results(self):
        """Check if more people results are available"""
        try:
            return self.browser.driver.find_element(
                By.XPATH, "//button[contains(@aria-label, 'Next')]").is_enabled()
        except:
            return False