# Grafana Monitoring Agent

A Python-based agent that monitors Grafana dashboards by processing uploaded screenshots and generating reports in CSV/TXT format.

## Features

- Upload and process Grafana dashboard screenshots
- Extract metrics and data from images using OCR
- Generate structured reports in CSV or TXT format
- Automated monitoring and reporting
- Web interface for easy interaction

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Grafana credentials
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## Usage

1. Access the web interface at `http://localhost:5000`
2. Upload Grafana dashboard screenshots
3. Configure report format and output settings
4. Generate and download reports

## Project Structure

```
grafanaagent/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── grafana_client.py      # Grafana API client
├── image_processor.py     # Image processing and OCR
├── report_generator.py    # Report generation logic
├── scheduler.py           # Automated monitoring
├── uploads/               # Uploaded images
├── outputs/               # Generated reports
├── templates/             # HTML templates
└── static/                # Static files (CSS, JS)
```
