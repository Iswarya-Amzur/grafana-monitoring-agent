import schedule
import time
from datetime import datetime
import os
from grafana_client import GrafanaClient
from report_generator import ReportGenerator

class GrafanaScheduler:
    """Automated scheduler for Grafana monitoring"""
    
    def __init__(self):
        self.grafana_client = GrafanaClient()
        self.report_generator = ReportGenerator()
        self.is_running = False
    
    def schedule_monitoring(self):
        """Set up monitoring schedule"""
        # Schedule different types of monitoring
        schedule.every(1).hours.do(self.collect_dashboard_info)
        schedule.every(1).days.do(self.generate_daily_report)
        schedule.every().monday.at("09:00").do(self.generate_weekly_report)
        
        print("Monitoring scheduler started...")
        print("- Dashboard info collection: Every hour")
        print("- Daily reports: Every day")
        print("- Weekly reports: Every Monday at 9:00 AM")
    
    def collect_dashboard_info(self):
        """Collect dashboard information"""
        try:
            print(f"[{datetime.now()}] Collecting dashboard information...")
            
            dashboards = self.grafana_client.get_dashboards()
            
            # Create a summary report
            summary_data = {
                'collected_at': datetime.now().isoformat(),
                'total_dashboards': len(dashboards),
                'dashboards': dashboards
            }
            
            # Generate JSON report
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"dashboard_summary_{timestamp}.json"
            
            self.report_generator.generate_json_report(summary_data, filename)
            print(f"Dashboard summary saved: {filename}")
            
        except Exception as e:
            print(f"Error collecting dashboard info: {e}")
    
    def generate_daily_report(self):
        """Generate daily monitoring report"""
        try:
            print(f"[{datetime.now()}] Generating daily report...")
            
            # Check if we have any processed data from today
            output_folder = self.report_generator.output_folder
            today = datetime.now().strftime('%Y-%m-%d')
            
            daily_files = []
            if os.path.exists(output_folder):
                for filename in os.listdir(output_folder):
                    if today in filename and filename.endswith('.json'):
                        daily_files.append(filename)
            
            if daily_files:
                # Create daily summary
                summary_content = f"Daily Grafana Monitoring Report - {today}\n"
                summary_content += "=" * 50 + "\n\n"
                summary_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                summary_content += f"Files processed today: {len(daily_files)}\n\n"
                
                for filename in daily_files:
                    summary_content += f"- {filename}\n"
                
                # Save daily summary
                daily_filename = f"daily_summary_{today}.txt"
                daily_path = os.path.join(output_folder, daily_filename)
                
                with open(daily_path, 'w', encoding='utf-8') as f:
                    f.write(summary_content)
                
                print(f"Daily report saved: {daily_filename}")
            else:
                print("No data to include in daily report")
                
        except Exception as e:
            print(f"Error generating daily report: {e}")
    
    def generate_weekly_report(self):
        """Generate weekly monitoring report"""
        try:
            print(f"[{datetime.now()}] Generating weekly report...")
            
            # Similar to daily report but for the week
            output_folder = self.report_generator.output_folder
            week_start = datetime.now().strftime('%Y-%m-%d')
            
            weekly_content = f"Weekly Grafana Monitoring Report - Week of {week_start}\n"
            weekly_content += "=" * 60 + "\n\n"
            weekly_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Count files from the past week
            if os.path.exists(output_folder):
                all_files = os.listdir(output_folder)
                weekly_content += f"Total files in output folder: {len(all_files)}\n"
                
                # Group by file type
                csv_files = [f for f in all_files if f.endswith('.csv')]
                txt_files = [f for f in all_files if f.endswith('.txt')]
                json_files = [f for f in all_files if f.endswith('.json')]
                
                weekly_content += f"CSV reports: {len(csv_files)}\n"
                weekly_content += f"TXT reports: {len(txt_files)}\n"
                weekly_content += f"JSON reports: {len(json_files)}\n\n"
            
            # Save weekly summary
            weekly_filename = f"weekly_summary_{week_start}.txt"
            weekly_path = os.path.join(output_folder, weekly_filename)
            
            with open(weekly_path, 'w', encoding='utf-8') as f:
                f.write(weekly_content)
            
            print(f"Weekly report saved: {weekly_filename}")
            
        except Exception as e:
            print(f"Error generating weekly report: {e}")
    
    def run(self):
        """Run the scheduler"""
        self.is_running = True
        self.schedule_monitoring()
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        print("Monitoring scheduler stopped.")

if __name__ == "__main__":
    scheduler = GrafanaScheduler()
    
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.stop()
