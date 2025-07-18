import openai
import base64
import json
import os
from datetime import datetime
from PIL import Image
import io
from config import Config

class OpenAIProcessor:
    """Process Grafana screenshots using OpenAI's GPT-4 Vision model"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.use_vision = Config.USE_OPENAI_VISION
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        self.temperature = Config.OPENAI_TEMPERATURE
        
        # Validate API key
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in your .env file")
    
    def get_system_prompt(self):
        """Get the system prompt for analyzing Grafana dashboards"""
        return """You are an expert Grafana dashboard analyst. You will be given screenshots of Grafana dashboards and need to extract meaningful monitoring data and insights.

Your task is to analyze the dashboard image and provide structured information in the following format:

1. **Dashboard Overview**:
   - Dashboard title/name
   - Time range shown
   - Number of panels visible
   - Overall dashboard theme/focus (e.g., infrastructure, application, database monitoring)

2. **Panel Analysis**:
   For each panel visible in the dashboard:
   - Panel title
   - Chart type (gauge, graph, table, single stat, etc.)
   - Current values/metrics displayed
   - Units of measurement
   - Status indicators (green/red/yellow states)
   - Trend information if visible

3. **Metrics Extraction**:
   - Key performance indicators (KPIs)
   - Numeric values with their units
   - Percentages
   - Status indicators (UP/DOWN/OK/ERROR/WARNING)
   - Timestamps if visible
   - Thresholds or limits shown

4. **System Health Assessment**:
   - Overall system health status
   - Any alerts or warnings visible
   - Performance trends
   - Resource utilization patterns

5. **Actionable Insights**:
   - Notable patterns or anomalies
   - Recommendations based on the metrics
   - Potential issues to investigate

Please provide your analysis in a structured JSON format that can be easily parsed and converted to CSV/TXT reports. Be specific about numeric values and include units where applicable.

Example JSON structure:
{
  "dashboard_overview": {
    "title": "Infrastructure Monitoring",
    "time_range": "Last 24 hours",
    "panel_count": 8,
    "theme": "infrastructure"
  },
  "panels": [
    {
      "title": "CPU Usage",
      "type": "gauge",
      "current_value": 45.2,
      "unit": "%",
      "status": "OK",
      "threshold": 80
    }
  ],
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1,
    "network_in": 1.5,
    "network_out": 2.3
  },
  "health_status": "HEALTHY",
  "alerts": [],
  "insights": ["CPU usage is within normal range", "Memory usage is elevated but stable"]
}

Focus on accuracy and extract only the information that is clearly visible in the image."""

    def get_analysis_prompt(self, additional_context=""):
        """Get the user prompt for specific analysis"""
        base_prompt = """Analyze this Grafana dashboard screenshot and provide detailed insights about the system's performance and health status. 

Extract all visible metrics, status indicators, and performance data. Pay special attention to:
- Numeric values and their units
- Color-coded status indicators
- Chart patterns and trends
- Alert conditions
- Resource utilization levels

Format your response as structured JSON following the schema provided in the system prompt."""
        
        if additional_context:
            base_prompt += f"\n\nAdditional context: {additional_context}"
        
        return base_prompt
    
    def encode_image(self, image_path):
        """Encode image to base64 for OpenAI API"""
        try:
            # Optimize image size for API
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large (OpenAI has size limits)
                max_size = 2048
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode to base64
                return base64.b64encode(img_byte_arr).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None
    
    def analyze_dashboard_image(self, image_path, additional_context=""):
        """Analyze Grafana dashboard image using OpenAI Vision API"""
        try:
            if not self.use_vision:
                return self._fallback_text_analysis(image_path)
            
            # Encode image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return None
            
            # Create messages for the API
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt()
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.get_analysis_prompt(additional_context)
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                analysis_data = json.loads(analysis_text)
            except json.JSONDecodeError:
                # If not valid JSON, create structured format
                analysis_data = {
                    "raw_analysis": analysis_text,
                    "processed_at": datetime.now().isoformat(),
                    "model_used": self.model,
                    "parsing_error": "Response was not valid JSON"
                }
            
            return analysis_data
            
        except Exception as e:
            print(f"Error analyzing image with OpenAI: {e}")
            return None
    
    def _fallback_text_analysis(self, image_path):
        """Fallback method if Vision API is not available"""
        try:
            # This could integrate with the existing OCR processor
            # For now, return a placeholder
            return {
                "error": "Vision API not available",
                "fallback_method": "OCR analysis would be used here",
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error in fallback analysis: {e}")
            return None
    
    def process_image_with_custom_prompt(self, image_path, custom_prompt):
        """Process image with a custom user-provided prompt"""
        try:
            if not self.use_vision:
                return self._fallback_text_analysis(image_path)
            
            # Encode image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return None
            
            # Create messages with custom prompt
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing Grafana dashboards. Analyze the provided dashboard image and respond according to the user's specific instructions."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": custom_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, otherwise return as text
            try:
                analysis_data = json.loads(analysis_text)
            except json.JSONDecodeError:
                analysis_data = {
                    "analysis": analysis_text,
                    "processed_at": datetime.now().isoformat(),
                    "model_used": self.model,
                    "custom_prompt": custom_prompt
                }
            
            return analysis_data
            
        except Exception as e:
            print(f"Error processing image with custom prompt: {e}")
            return None
    
    def extract_metrics_from_analysis(self, analysis_data):
        """Extract structured metrics from OpenAI analysis"""
        metrics = {}
        
        try:
            if isinstance(analysis_data, dict):
                # Extract dashboard overview
                if 'dashboard_overview' in analysis_data:
                    overview = analysis_data['dashboard_overview']
                    metrics['dashboard_title'] = overview.get('title', '')
                    metrics['time_range'] = overview.get('time_range', '')
                    metrics['panel_count'] = overview.get('panel_count', 0)
                    metrics['theme'] = overview.get('theme', '')
                
                # Extract panels information
                if 'panels' in analysis_data:
                    panels = analysis_data['panels']
                    metrics['panels'] = panels
                    metrics['total_panels'] = len(panels)
                    
                    # Extract numeric values from panels
                    numeric_values = []
                    status_indicators = []
                    
                    for panel in panels:
                        if 'current_value' in panel:
                            numeric_values.append({
                                'value': panel['current_value'],
                                'unit': panel.get('unit', ''),
                                'panel': panel.get('title', '')
                            })
                        if 'status' in panel:
                            status_indicators.append(panel['status'])
                    
                    metrics['numeric_values'] = numeric_values
                    metrics['status_indicators'] = status_indicators
                
                # Extract direct metrics
                if 'metrics' in analysis_data:
                    metrics['extracted_metrics'] = analysis_data['metrics']
                
                # Extract health status
                if 'health_status' in analysis_data:
                    metrics['health_status'] = analysis_data['health_status']
                
                # Extract insights
                if 'insights' in analysis_data:
                    metrics['insights'] = analysis_data['insights']
                
                # Extract alerts
                if 'alerts' in analysis_data:
                    metrics['alerts'] = analysis_data['alerts']
            
            return metrics
            
        except Exception as e:
            print(f"Error extracting metrics from analysis: {e}")
            return {}
    
    def test_api_connection(self):
        """Test OpenAI API connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"OpenAI API connection test failed: {e}")
            return False
