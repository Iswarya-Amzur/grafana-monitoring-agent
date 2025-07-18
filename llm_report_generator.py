import pandas as pd
import csv
import json
from datetime import datetime
import os
from config import Config

class LLMReportGenerator:
    """Generate reports from OpenAI LLM analysis of Grafana dashboards"""
    
    def __init__(self):
        self.output_folder = Config.OUTPUT_FOLDER
        os.makedirs(self.output_folder, exist_ok=True)
    
    def generate_llm_csv_report(self, analysis_data_list, filename=None):
        """Generate CSV report from LLM analysis data"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"llm_grafana_report_{timestamp}.csv"
            
            filepath = os.path.join(self.output_folder, filename)
            
            # Prepare data for CSV
            rows = []
            
            if not isinstance(analysis_data_list, list):
                analysis_data_list = [analysis_data_list]
            
            for analysis_data in analysis_data_list:
                row = self._extract_llm_row_data(analysis_data)
                rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Write to CSV
            df.to_csv(filepath, index=False)
            
            return filepath
        except Exception as e:
            print(f"Error generating LLM CSV report: {e}")
            return None
    
    def generate_llm_txt_report(self, analysis_data_list, filename=None):
        """Generate TXT report from LLM analysis data"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"llm_grafana_report_{timestamp}.txt"
            
            filepath = os.path.join(self.output_folder, filename)
            
            if not isinstance(analysis_data_list, list):
                analysis_data_list = [analysis_data_list]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("GRAFANA DASHBOARD ANALYSIS REPORT (LLM-POWERED)\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Analysis Method: OpenAI {Config.OPENAI_MODEL}\n")
                f.write(f"Total Dashboards Analyzed: {len(analysis_data_list)}\n\n")
                
                for i, analysis_data in enumerate(analysis_data_list, 1):
                    f.write(f"DASHBOARD {i} ANALYSIS\n")
                    f.write("-" * 40 + "\n")
                    self._write_llm_analysis_to_txt(f, analysis_data)
                    f.write("\n" + "="*70 + "\n\n")
            
            return filepath
        except Exception as e:
            print(f"Error generating LLM TXT report: {e}")
            return None
    
    def generate_llm_json_report(self, analysis_data_list, filename=None):
        """Generate JSON report from LLM analysis data"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"llm_grafana_report_{timestamp}.json"
            
            filepath = os.path.join(self.output_folder, filename)
            
            if not isinstance(analysis_data_list, list):
                analysis_data_list = [analysis_data_list]
            
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'analysis_method': f'OpenAI {Config.OPENAI_MODEL}',
                'total_dashboards': len(analysis_data_list),
                'dashboards': analysis_data_list
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return filepath
        except Exception as e:
            print(f"Error generating LLM JSON report: {e}")
            return None
    
    def _extract_llm_row_data(self, analysis_data):
        """Extract data for a single row in CSV from LLM analysis"""
        row = {}
        
        # Basic info
        row['analyzed_at'] = analysis_data.get('processed_at', datetime.now().isoformat())
        row['model_used'] = analysis_data.get('model_used', Config.OPENAI_MODEL)
        row['image_file'] = analysis_data.get('image_info', {}).get('filename', '')
        
        # Dashboard overview
        overview = analysis_data.get('dashboard_overview', {})
        row['dashboard_title'] = overview.get('title', '')
        row['time_range'] = overview.get('time_range', '')
        row['panel_count'] = overview.get('panel_count', 0)
        row['dashboard_theme'] = overview.get('theme', '')
        
        # Health status
        row['health_status'] = analysis_data.get('health_status', 'UNKNOWN')
        
        # Metrics summary
        metrics = analysis_data.get('metrics', {})
        if metrics:
            # Extract key metrics
            row['cpu_usage'] = metrics.get('cpu_usage', '')
            row['memory_usage'] = metrics.get('memory_usage', '')
            row['disk_usage'] = metrics.get('disk_usage', '')
            row['network_in'] = metrics.get('network_in', '')
            row['network_out'] = metrics.get('network_out', '')
        
        # Panels summary
        panels = analysis_data.get('panels', [])
        if panels:
            row['total_panels'] = len(panels)
            row['panels_with_alerts'] = len([p for p in panels if p.get('status') in ['ERROR', 'WARNING', 'CRITICAL']])
            
            # Extract panel types
            panel_types = [p.get('type', '') for p in panels]
            row['panel_types'] = ', '.join(set(panel_types))
            
            # Extract numeric values
            numeric_values = []
            for panel in panels:
                if 'current_value' in panel:
                    value = panel['current_value']
                    unit = panel.get('unit', '')
                    numeric_values.append(f"{value}{unit}")
            row['key_values'] = ', '.join(numeric_values[:5])  # First 5 values
        
        # Alerts and insights
        alerts = analysis_data.get('alerts', [])
        row['alert_count'] = len(alerts)
        row['has_alerts'] = len(alerts) > 0
        
        insights = analysis_data.get('insights', [])
        row['insights_count'] = len(insights)
        row['key_insights'] = '. '.join(insights[:3]) if insights else ''  # First 3 insights
        
        # Error handling
        if 'error' in analysis_data:
            row['analysis_error'] = analysis_data['error']
        
        # Custom prompt info
        if 'custom_prompt' in analysis_data:
            row['custom_prompt_used'] = True
            row['custom_prompt'] = analysis_data['custom_prompt'][:100] + '...' if len(analysis_data['custom_prompt']) > 100 else analysis_data['custom_prompt']
        else:
            row['custom_prompt_used'] = False
        
        return row
    
    def _write_llm_analysis_to_txt(self, file, analysis_data):
        """Write LLM analysis to text file"""
        try:
            # Basic information
            file.write(f"Analysis Time: {analysis_data.get('processed_at', 'Unknown')}\n")
            file.write(f"Model Used: {analysis_data.get('model_used', Config.OPENAI_MODEL)}\n")
            
            # Dashboard overview
            overview = analysis_data.get('dashboard_overview', {})
            if overview:
                file.write(f"\nDASHBOARD OVERVIEW:\n")
                file.write(f"  Title: {overview.get('title', 'Unknown')}\n")
                file.write(f"  Time Range: {overview.get('time_range', 'Unknown')}\n")
                file.write(f"  Panel Count: {overview.get('panel_count', 0)}\n")
                file.write(f"  Theme: {overview.get('theme', 'Unknown')}\n")
            
            # Health status
            health_status = analysis_data.get('health_status', 'UNKNOWN')
            file.write(f"\nHEALTH STATUS: {health_status}\n")
            
            # Metrics
            metrics = analysis_data.get('metrics', {})
            if metrics:
                file.write(f"\nKEY METRICS:\n")
                for metric_name, value in metrics.items():
                    file.write(f"  {metric_name}: {value}\n")
            
            # Panels analysis
            panels = analysis_data.get('panels', [])
            if panels:
                file.write(f"\nPANELS ANALYSIS ({len(panels)} panels):\n")
                for i, panel in enumerate(panels, 1):
                    file.write(f"  Panel {i}: {panel.get('title', 'Unnamed')}\n")
                    file.write(f"    Type: {panel.get('type', 'Unknown')}\n")
                    file.write(f"    Value: {panel.get('current_value', 'N/A')} {panel.get('unit', '')}\n")
                    file.write(f"    Status: {panel.get('status', 'Unknown')}\n")
                    if 'threshold' in panel:
                        file.write(f"    Threshold: {panel['threshold']}\n")
                    file.write("\n")
            
            # Alerts
            alerts = analysis_data.get('alerts', [])
            if alerts:
                file.write(f"ALERTS ({len(alerts)} active):\n")
                for alert in alerts:
                    file.write(f"  - {alert}\n")
            else:
                file.write("ALERTS: No active alerts\n")
            
            # Insights
            insights = analysis_data.get('insights', [])
            if insights:
                file.write(f"\nINSIGHTS AND RECOMMENDATIONS:\n")
                for insight in insights:
                    file.write(f"  • {insight}\n")
            
            # Raw analysis (if available)
            if 'raw_analysis' in analysis_data:
                file.write(f"\nRAW ANALYSIS:\n")
                file.write(f"{analysis_data['raw_analysis']}\n")
            
            # Custom prompt (if used)
            if 'custom_prompt' in analysis_data:
                file.write(f"\nCUSTOM PROMPT USED:\n")
                file.write(f"{analysis_data['custom_prompt']}\n")
            
            # Error information (if any)
            if 'error' in analysis_data:
                file.write(f"\nERROR: {analysis_data['error']}\n")
            
        except Exception as e:
            file.write(f"Error writing analysis: {e}\n")
    
    def generate_comparative_report(self, analysis_data_list, filename=None):
        """Generate a comparative report across multiple dashboard analyses"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime(Config.REPORT_TIMESTAMP_FORMAT)
                filename = f"comparative_dashboard_analysis_{timestamp}.txt"
            
            filepath = os.path.join(self.output_folder, filename)
            
            if not isinstance(analysis_data_list, list):
                analysis_data_list = [analysis_data_list]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("COMPARATIVE DASHBOARD ANALYSIS REPORT\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Dashboards: {len(analysis_data_list)}\n\n")
                
                # Summary statistics
                health_statuses = [data.get('health_status', 'UNKNOWN') for data in analysis_data_list]
                total_panels = sum(data.get('dashboard_overview', {}).get('panel_count', 0) for data in analysis_data_list)
                total_alerts = sum(len(data.get('alerts', [])) for data in analysis_data_list)
                
                f.write("SUMMARY STATISTICS:\n")
                f.write(f"  Total Panels Analyzed: {total_panels}\n")
                f.write(f"  Total Alerts: {total_alerts}\n")
                f.write(f"  Health Status Distribution:\n")
                
                from collections import Counter
                health_counter = Counter(health_statuses)
                for status, count in health_counter.items():
                    f.write(f"    {status}: {count}\n")
                
                f.write("\nDASHBOARD COMPARISON:\n")
                f.write("-" * 50 + "\n")
                
                for i, analysis in enumerate(analysis_data_list, 1):
                    overview = analysis.get('dashboard_overview', {})
                    f.write(f"\nDashboard {i}: {overview.get('title', 'Unknown')}\n")
                    f.write(f"  Health: {analysis.get('health_status', 'UNKNOWN')}\n")
                    f.write(f"  Panels: {overview.get('panel_count', 0)}\n")
                    f.write(f"  Alerts: {len(analysis.get('alerts', []))}\n")
                    
                    # Key insights
                    insights = analysis.get('insights', [])
                    if insights:
                        f.write(f"  Key Insight: {insights[0]}\n")
                
                # Recommendations
                f.write("\nOVERALL RECOMMENDATIONS:\n")
                f.write("-" * 30 + "\n")
                
                if total_alerts > 0:
                    f.write(f"• {total_alerts} alerts detected across all dashboards - investigate immediately\n")
                
                critical_dashboards = [d for d in analysis_data_list if d.get('health_status') in ['CRITICAL', 'ERROR']]
                if critical_dashboards:
                    f.write(f"• {len(critical_dashboards)} dashboards in critical state - prioritize these\n")
                
                f.write("• Regular monitoring recommended for all systems\n")
                f.write("• Consider setting up automated alerting for critical metrics\n")
            
            return filepath
        except Exception as e:
            print(f"Error generating comparative report: {e}")
            return None
