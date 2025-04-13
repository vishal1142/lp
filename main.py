import yaml
from modules.browser import BrowserManager
from modules.search import LinkedInSearch
from modules.profile import LinkedInProfile
from modules.ocr import OCRProcessor
import json
import time

def load_config(config_path='config/config.yaml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    # Load configuration
    config = load_config()
    
    # Initialize modules
    browser_manager = BrowserManager(headless=False)  # Set to True for production
    ocr_processor = OCRProcessor(config['ocr']['tesseract_path'])
    search_agent = LinkedInSearch(browser_manager)
    profile_agent = LinkedInProfile(browser_manager, ocr_processor)
    
    try:
        # Start browser and login
        browser_manager.start_browser()
        search_agent.login()
        
        # Perform search
        print("Performing search...")
        results = search_agent.perform_search()
        print(f"Found {len(results)} profiles")
        
        # Process results
        profiles_data = []
        for i, result in enumerate(results[:5]):  # Limit to 5 for demo
            print(f"Processing profile {i+1}/{len(results)}: {result['name']}")
            
            # Extract basic details
            profile_data = {
                'name': result['name'],
                'headline': result['headline']
            }
            
            # Extract details from profile card
            card_details = profile_agent.extract_profile_details(result['element'])
            profile_data.update(card_details)
            
            # Optional: Visit full profile for more details
            full_profile_details = profile_agent.visit_full_profile(result['element'])
            profile_data.update(full_profile_details)
            
            profiles_data.append(profile_data)
            
            # Respect rate limits
            time.sleep(config['linkedin']['limits']['delay_between_actions'])
        
        # Save results
        with open('search_results.json', 'w') as f:
            json.dump(profiles_data, f, indent=2)
        
        print("Search completed. Results saved to search_results.json")
    
    except Exception as e:
        print(f"Error during search: {e}")
    finally:
        browser_manager.close_browser()

if __name__ == "__main__":
    main()