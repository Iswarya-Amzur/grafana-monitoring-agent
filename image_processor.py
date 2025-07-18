import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
import os
from datetime import datetime
from config import Config

class ImageProcessor:
    """Process uploaded images and extract metrics using OCR"""
    
    def __init__(self):
        # Set Tesseract path for Windows
        if os.path.exists(Config.TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH
        else:
            print(f"Warning: Tesseract not found at {Config.TESSERACT_PATH}")
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to make text more visible
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Denoise
            denoised = cv2.medianBlur(thresh, 5)
            
            # Resize for better OCR (if image is too small)
            height, width = denoised.shape
            if height < 500 or width < 500:
                scale_factor = max(500/height, 500/width)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                denoised = cv2.resize(denoised, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return denoised
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """Extract text from image using OCR"""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return ""
            
            # Convert to PIL Image
            pil_image = Image.fromarray(processed_image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(pil_image, config='--psm 6')
            
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""
    
    def extract_metrics_from_text(self, text):
        """Extract metrics and values from OCR text"""
        metrics = {}
        
        try:
            # Common patterns for metrics
            patterns = {
                'numbers': r'(\d+(?:\.\d+)?)\s*([%kmgtKMGT]?[Bb]?/?[sS]?)',
                'percentages': r'(\d+(?:\.\d+)?)\s*%',
                'time_values': r'(\d+(?:\.\d+)?)\s*(ms|s|m|h|d)',
                'memory_values': r'(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)',
                'network_values': r'(\d+(?:\.\d+)?)\s*(bps|Kbps|Mbps|Gbps)',
                'status_indicators': r'(UP|DOWN|OK|ERROR|CRITICAL|WARNING|HEALTHY|UNHEALTHY)',
                'timestamps': r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}:\d{2}:\d{2})',
                'labels': r'([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*([^\n\r]+)'
            }
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract different types of metrics
                for pattern_name, pattern in patterns.items():
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        if pattern_name not in metrics:
                            metrics[pattern_name] = []
                        metrics[pattern_name].extend(matches)
            
            # Extract dashboard title (usually at the top)
            first_lines = text.split('\n')[:3]
            dashboard_title = ""
            for line in first_lines:
                if line.strip() and len(line.strip()) > 5:
                    dashboard_title = line.strip()
                    break
            
            if dashboard_title:
                metrics['dashboard_title'] = dashboard_title
            
            # Extract panel titles (lines that look like headers)
            panel_titles = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 3 and len(line) < 50:
                    if not any(char.isdigit() for char in line):
                        panel_titles.append(line)
            
            if panel_titles:
                metrics['panel_titles'] = panel_titles
            
            return metrics
        except Exception as e:
            print(f"Error extracting metrics: {e}")
            return {}
    
    def process_image(self, image_path):
        """Main method to process image and extract all information"""
        try:
            # Extract text from image
            text = self.extract_text_from_image(image_path)
            
            # Extract metrics from text
            metrics = self.extract_metrics_from_text(text)
            
            # Get image metadata
            image_info = self.get_image_info(image_path)
            
            # Combine all information
            result = {
                'image_path': image_path,
                'processed_at': datetime.now().isoformat(),
                'raw_text': text,
                'metrics': metrics,
                'image_info': image_info
            }
            
            return result
        except Exception as e:
            print(f"Error processing image: {e}")
            return None
    
    def get_image_info(self, image_path):
        """Get basic image information"""
        try:
            image = Image.open(image_path)
            return {
                'filename': os.path.basename(image_path),
                'size': image.size,
                'format': image.format,
                'mode': image.mode,
                'file_size': os.path.getsize(image_path)
            }
        except Exception as e:
            print(f"Error getting image info: {e}")
            return {}
    
    def detect_chart_type(self, image_path):
        """Attempt to detect the type of chart/graph in the image"""
        try:
            # This is a basic implementation - could be enhanced with ML
            text = self.extract_text_from_image(image_path)
            text_lower = text.lower()
            
            chart_types = {
                'time_series': ['time', 'series', 'timeline', 'hours', 'minutes'],
                'bar_chart': ['bar', 'column', 'histogram'],
                'pie_chart': ['pie', 'donut', 'percentage'],
                'gauge': ['gauge', 'meter', 'speed'],
                'table': ['table', 'row', 'column'],
                'single_stat': ['total', 'count', 'sum', 'average'],
                'heatmap': ['heatmap', 'heat', 'density']
            }
            
            detected_types = []
            for chart_type, keywords in chart_types.items():
                if any(keyword in text_lower for keyword in keywords):
                    detected_types.append(chart_type)
            
            return detected_types if detected_types else ['unknown']
        except Exception as e:
            print(f"Error detecting chart type: {e}")
            return ['unknown']
