import pandas as pd
import csv
import json
from datetime import datetime
import os
from config import Config

class ReportGenerator:
    """Generate reports from processed image data"""
    
    def __init__(self):
        self.output_folder = Config.OUTPUT_FOLDER
        os.makedirs(self.output_folder, exist_ok=True)
    
    def generate_csv_report(self, processed_data, filename=None):
        """Generate CSV report from processed data"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"grafana_report_{timestamp}.csv"
            
            filepath = os.path.join(self.output_folder, filename)
            
            # Prepare data for CSV
            rows = []
            
            if isinstance(processed_data, list):
                # Multiple images processed
                for data in processed_data:
                    row = self._extract_row_data(data)
                    rows.append(row)
            else:
                # Single image processed
                row = self._extract_row_data(processed_data)
                rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Write to CSV
            df.to_csv(filepath, index=False)
            
            return filepath
        except Exception as e:
            print(f"Error generating CSV report: {e}")
            return None
    
    def generate_txt_report(self, processed_data, filename=None):
        """Generate TXT report from processed data"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"grafana_report_{timestamp}.txt"
            
            filepath = os.path.join(self.output_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("GRAFANA MONITORING REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if isinstance(processed_data, list):
                    for i, data in enumerate(processed_data, 1):
                        f.write(f"IMAGE {i}: {data.get('image_info', {}).get('filename', 'Unknown')}\n")
                        f.write("-" * 30 + "\n")
                        self._write_data_to_txt(f, data)
                        f.write("\n")
                else:
                    f.write(f"IMAGE: {processed_data.get('image_info', {}).get('filename', 'Unknown')}\n")
                    f.write("-" * 30 + "\n")
                    self._write_data_to_txt(f, processed_data)
            
            return filepath
        except Exception as e:
            print(f"Error generating TXT report: {e}")
            return None
    
    def generate_json_report(self, processed_data, filename=None):
        """Generate JSON report from processed data"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"grafana_report_{timestamp}.json"
            
            filepath = os.path.join(self.output_folder, filename)
            
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'data': processed_data if isinstance(processed_data, list) else [processed_data]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return filepath
        except Exception as e:
            print(f"Error generating JSON report: {e}")
            return None
    
    def _extract_row_data(self, data):
        """Extract data for a single row in CSV"""
        row = {}
        
        # Basic info
        row['filename'] = data.get('image_info', {}).get('filename', '')
        row['processed_at'] = data.get('processed_at', '')
        row['dashboard_title'] = data.get('metrics', {}).get('dashboard_title', '')
        
        # Image info
        image_info = data.get('image_info', {})
        row['image_size'] = f"{image_info.get('size', ['', ''])[0]}x{image_info.get('size', ['', ''])[1]}" if image_info.get('size') else ''
        row['file_size'] = image_info.get('file_size', '')
        
        # Extract metrics
        metrics = data.get('metrics', {})
        
        # Numbers
        numbers = metrics.get('numbers', [])
        if numbers:
            row['primary_value'] = numbers[0][0] if numbers[0] else ''
            row['primary_unit'] = numbers[0][1] if len(numbers[0]) > 1 else ''
            row['total_numbers'] = len(numbers)
        
        # Percentages
        percentages = metrics.get('percentages', [])
        if percentages:
            row['percentage_values'] = ', '.join([str(p) for p in percentages])
        
        # Status indicators
        status_indicators = metrics.get('status_indicators', [])
        if status_indicators:
            row['status'] = ', '.join(status_indicators)
        
        # Panel titles
        panel_titles = metrics.get('panel_titles', [])
        if panel_titles:
            row['panel_titles'] = ', '.join(panel_titles[:3])  # First 3 panels
        
        # Time values
        time_values = metrics.get('time_values', [])
        if time_values:
            row['time_metrics'] = ', '.join([f"{tv[0]}{tv[1]}" for tv in time_values])
        
        # Memory values
        memory_values = metrics.get('memory_values', [])
        if memory_values:
            row['memory_metrics'] = ', '.join([f"{mv[0]}{mv[1]}" for mv in memory_values])
        
        # Raw text length (for reference)
        row['raw_text_length'] = len(data.get('raw_text', ''))
        
        return row
    
    def _write_data_to_txt(self, file, data):
        """Write single data entry to text file"""
        # Basic information
        file.write(f"Processed: {data.get('processed_at', 'Unknown')}\n")
        
        # Dashboard title
        dashboard_title = data.get('metrics', {}).get('dashboard_title', '')
        if dashboard_title:
            file.write(f"Dashboard: {dashboard_title}\n")
        
        # Image info
        image_info = data.get('image_info', {})
        if image_info:
            file.write(f"Image Size: {image_info.get('size', 'Unknown')}\n")
            file.write(f"File Size: {image_info.get('file_size', 'Unknown')} bytes\n")
        
        # Metrics
        metrics = data.get('metrics', {})
        
        if metrics.get('numbers'):
            file.write(f"Numeric Values: {len(metrics['numbers'])} found\n")
            for i, (value, unit) in enumerate(metrics['numbers'][:5]):  # Show first 5
                file.write(f"  - {value} {unit}\n")
        
        if metrics.get('percentages'):
            file.write(f"Percentages: {', '.join(str(p) for p in metrics['percentages'])}\n")
        
        if metrics.get('status_indicators'):
            file.write(f"Status: {', '.join(metrics['status_indicators'])}\n")
        
        if metrics.get('panel_titles'):
            file.write(f"Panel Titles:\n")
            for title in metrics['panel_titles'][:5]:  # Show first 5
                file.write(f"  - {title}\n")
        
        # Raw text sample
        raw_text = data.get('raw_text', '')
        if raw_text:
            file.write(f"Raw Text Sample (first 200 chars):\n")
            file.write(f"  {raw_text[:200]}...\n")
        
        file.write("\n")
    
    def generate_summary_report(self, processed_data_list):
        """Generate a summary report from multiple processed images"""
        try:
            timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
            filename = f"grafana_summary_{timestamp}.txt"
            filepath = os.path.join(self.output_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("GRAFANA MONITORING SUMMARY REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Images Processed: {len(processed_data_list)}\n\n")
                
                # Collect statistics
                total_metrics = 0
                status_counts = {}
                dashboard_titles = set()
                
                for data in processed_data_list:
                    metrics = data.get('metrics', {})
                    
                    # Count total metrics
                    for metric_type in ['numbers', 'percentages', 'time_values', 'memory_values']:
                        if metric_type in metrics:
                            total_metrics += len(metrics[metric_type])
                    
                    # Count status indicators
                    for status in metrics.get('status_indicators', []):
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Collect dashboard titles
                    dashboard_title = metrics.get('dashboard_title', '')
                    if dashboard_title:
                        dashboard_titles.add(dashboard_title)
                
                # Write statistics
                f.write(f"Total Metrics Extracted: {total_metrics}\n")
                f.write(f"Unique Dashboards: {len(dashboard_titles)}\n")
                
                if status_counts:
                    f.write(f"Status Indicators:\n")
                    for status, count in status_counts.items():
                        f.write(f"  - {status}: {count}\n")
                
                if dashboard_titles:
                    f.write(f"\nDashboard Titles:\n")
                    for title in sorted(dashboard_titles):
                        f.write(f"  - {title}\n")
            
            return filepath
        except Exception as e:
            print(f"Error generating summary report: {e}")
            return None
