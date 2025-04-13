from selenium.webdriver.common.by import By
import time
import os

class LinkedInProfile:
    def __init__(self, browser_manager, ocr_processor):
        self.browser = browser_manager
        self.ocr = ocr_processor
    
    def extract_profile_details(self, profile_element):
        """Extract details from a profile in search results"""
        details = {}
        
        try:
            # Click to expand the profile card
            profile_element.click()
            time.sleep(2)  # Wait for animation
            
            # Take screenshot of the profile card
            screenshot_path = "profile_card.png"
            self.browser.take_screenshot(profile_element, screenshot_path)
            
            # Use OCR to extract text from the screenshot
            ocr_details = self.ocr.extract_linkedin_details(screenshot_path)
            
            # Clean up
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            return ocr_details
        except Exception as e:
            print(f"Error extracting profile details: {e}")
            return details
    
    def visit_full_profile(self, profile_element):
        """Visit the full profile page and extract more details"""
        details = {}
        
        try:
            # Find and click the profile link
            link = profile_element.find_element(By.XPATH, ".//a[contains(@class, 'app-aware-link')]")
            profile_url = link.get_attribute('href')
            
            # Open profile in new tab
            self.browser.driver.execute_script(f"window.open('{profile_url}');")
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
            
            # Wait for profile to load
            time.sleep(3)
            
            # Extract details from full profile page
            details.update(self._extract_profile_sections())
            
            # Close the tab and switch back
            self.browser.driver.close()
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
            
            return details
        except Exception as e:
            print(f"Error visiting full profile: {e}")
            return details
    
    def _extract_profile_sections(self):
        """Extract various sections from the full profile page"""
        sections = {}
        
        try:
            # Extract name and headline
            sections['name'] = self.browser.wait_for_element(
                (By.XPATH, "//h1[contains(@class, 'text-heading-xlarge')]")).text
            sections['headline'] = self.browser.wait_for_element(
                (By.XPATH, "//div[contains(@class, 'text-body-medium')]")).text
            
            # Extract about section if available
            try:
                show_more = self.browser.driver.find_element(
                    By.XPATH, "//button[contains(@aria-label, 'Expand about section')]")
                show_more.click()
                time.sleep(1)
                sections['about'] = self.browser.driver.find_element(
                    By.XPATH, "//div[contains(@class, 'display-flex ph5 pv3')]/div/div/div").text
            except:
                pass
            
            # Extract experience
            sections['experience'] = self._extract_experience()
            
            # Extract education
            sections['education'] = self._extract_education()
            
        except Exception as e:
            print(f"Error extracting profile sections: {e}")
        
        return sections
    
    def _extract_experience(self):
        """Extract experience section"""
        experience = []
        
        try:
            exp_section = self.browser.driver.find_element(By.ID, "experience")
            exp_items = exp_section.find_elements(
                By.XPATH, ".//li[contains(@class, 'artdeco-list__item')]")
            
            for item in exp_items:
                try:
                    title = item.find_element(
                        By.XPATH, ".//span[contains(@class, 'mr1 t-bold')]/span").text
                    company = item.find_element(
                        By.XPATH, ".//span[contains(@class, 't-14 t-normal')]/span").text
                    duration = item.find_element(
                        By.XPATH, ".//span[contains(@class, 't-14 t-normal t-black--light')]/span").text
                    
                    experience.append({
                        'title': title,
                        'company': company,
                        'duration': duration
                    })
                except:
                    continue
        except:
            pass
        
        return experience
    
    def _extract_education(self):
        """Extract education section"""
        education = []
        
        try:
            edu_section = self.browser.driver.find_element(By.ID, "education")
            edu_items = edu_section.find_elements(
                By.XPATH, ".//li[contains(@class, 'artdeco-list__item')]")
            
            for item in edu_items:
                try:
                    school = item.find_element(
                        By.XPATH, ".//span[contains(@class, 'mr1 t-bold')]/span").text
                    degree = item.find_element(
                        By.XPATH, ".//span[contains(@class, 't-14 t-normal')]/span").text
                    duration = item.find_element(
                        By.XPATH, ".//span[contains(@class, 't-14 t-normal t-black--light')]/span").text
                    
                    education.append({
                        'school': school,
                        'degree': degree,
                        'duration': duration
                    })
                except:
                    continue
        except:
            pass
        
        return education