import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

class OCRProcessor:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def preprocess_image(self, image_path):
        """Enhance image for better OCR results"""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.dilate(processed, kernel, iterations=1)
        processed = cv2.erode(processed, kernel, iterations=1)
        
        return processed
    
    def extract_text(self, image_path, preprocess=True):
        """Extract text from image using OCR"""
        if preprocess:
            image = self.preprocess_image(image_path)
        else:
            image = Image.open(image_path)
            
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()
    
    def extract_linkedin_details(self, image_path):
        """Specialized method for extracting LinkedIn profile details"""
        text = self.extract_text(image_path)
        
        # Example patterns for LinkedIn data extraction
        patterns = {
            'name': r'^(.*?)\n',
            'headline': r'\n(.*?)\n',
            'location': r'Location\n(.*?)\n',
            'connections': r'(\d+)\s*connections'
        }
        
        results = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                results[key] = match.group(1).strip()
                
        return results