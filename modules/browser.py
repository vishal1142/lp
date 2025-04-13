import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BrowserManager:
    def __init__(self, headless=True):
        self.options = EdgeOptions()
        self.user_data_dir = os.path.join(tempfile.gettempdir(), f"edge_profile_{int(time.time())}")
        
        # Common options
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument(f"--user-data-dir={self.user_data_dir}")
        
        # Headless specific options
        if headless:
            self.options.add_argument("--headless=new")  # Use new headless mode
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--remote-debugging-port=9222")
            self.options.add_argument("--disable-extensions")
        
        # Performance optimizations
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = None
        self.service = EdgeService()

    def start_browser(self):
        """Start Edge browser with clean profile"""
        try:
            self.driver = webdriver.Edge(service=self.service, options=self.options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return self.driver
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to start browser: {str(e)}")

    def close_browser(self):
        """Close browser and clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
        self.cleanup()

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if hasattr(self, 'user_data_dir') and os.path.exists(self.user_data_dir):
                for _ in range(3):  # Retry mechanism
                    try:
                        import shutil
                        shutil.rmtree(self.user_data_dir, ignore_errors=True)
                        break
                    except PermissionError:
                        time.sleep(0.5)
        except Exception:
            pass

    def wait_for_element(self, locator, timeout=15):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator),
            message=f"Element not found: {locator}"
        )

    def wait_for_clickable(self, locator, timeout=15):
        """Wait for element to be clickable"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator),
            message=f"Element not clickable: {locator}"
        )

    def safe_click(self, locator, timeout=15):
        """Click element with safety checks"""
        element = self.wait_for_clickable(locator, timeout)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def safe_send_keys(self, locator, text, timeout=15):
        """Send keys with safety checks"""
        element = self.wait_for_element(locator, timeout)
        element.clear()
        element.send_keys(text)

    def take_screenshot(self, filename="screenshot.png"):
        """Take screenshot of current window"""
        path = os.path.join(os.getcwd(), filename)
        self.driver.save_screenshot(path)
        return path

    def scroll_to_element(self, element, behavior="smooth", block="center"):
        """Scroll to element with options"""
        self.driver.execute_script(
            f"arguments[0].scrollIntoView({{behavior: '{behavior}', block: '{block}'}});", 
            element
        )
        time.sleep(0.3)  # Reduced wait time

    def enable_headless_downloads(self, download_dir):
        """Configure downloads in headless mode"""
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        self.options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0
        })

    def get_edge_version(self):
        """Get browser version information"""
        return {
            'browser': self.driver.capabilities['browserVersion'],
            'driver': self.driver.capabilities['msedge']['msedgedriverVersion']
        }

    def __enter__(self):
        """Context manager entry"""
        return self.start_browser()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_browser()