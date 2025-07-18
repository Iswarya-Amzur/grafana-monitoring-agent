from flask import Flask, request, render_template, jsonify, send_file, flash, redirect, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import json

from config import Config
from image_processor import ImageProcessor
from report_generator import ReportGenerator
from grafana_client import GrafanaClient

app = Flask(__name__)
Config.init_app(app)

# Initialize components
image_processor = ImageProcessor()
report_generator = ReportGenerator()
grafana_client = GrafanaClient()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file upload and processing"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        output_format = request.form.get('output_format', 'csv')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        processed_data = []
        uploaded_files = []
        
        for file in files:
            if file and Config.allowed_file(file.filename):
                # Save uploaded file
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                uploaded_files.append(filepath)
                
                # Process image
                result = image_processor.process_image(filepath)
                if result:
                    processed_data.append(result)
        
        if not processed_data:
            return jsonify({'error': 'No images could be processed'}), 400
        
        # Generate report
        if output_format == 'csv':
            report_path = report_generator.generate_csv_report(processed_data)
        elif output_format == 'txt':
            report_path = report_generator.generate_txt_report(processed_data)
        elif output_format == 'json':
            report_path = report_generator.generate_json_report(processed_data)
        else:
            return jsonify({'error': 'Invalid output format'}), 400
        
        if report_path:
            # Generate summary for response
            summary = {
                'total_images': len(processed_data),
                'report_file': os.path.basename(report_path),
                'output_format': output_format,
                'processed_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'summary': summary,
                'report_path': report_path
            })
        else:
            return jsonify({'error': 'Failed to generate report'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated report"""
    try:
        file_path = os.path.join(Config.OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-grafana')
def test_grafana_connection():
    """Test Grafana connection"""
    try:
        is_connected = grafana_client.test_connection()
        is_authenticated = grafana_client.validate_credentials()
        
        return jsonify({
            'connected': is_connected,
            'authenticated': is_authenticated,
            'grafana_url': Config.GRAFANA_URL
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboards')
def get_dashboards():
    """Get list of Grafana dashboards"""
    try:
        dashboards = grafana_client.get_dashboards()
        return jsonify(dashboards)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-text', methods=['POST'])
def process_text():
    """Process raw text input (for testing)"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Extract metrics from text
        metrics = image_processor.extract_metrics_from_text(text)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'processed_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports')
def list_reports():
    """List generated reports"""
    try:
        reports = []
        if os.path.exists(Config.OUTPUT_FOLDER):
            for filename in os.listdir(Config.OUTPUT_FOLDER):
                filepath = os.path.join(Config.OUTPUT_FOLDER, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    reports.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return jsonify(reports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Handle settings GET/POST"""
    if request.method == 'GET':
        return jsonify({
            'grafana_url': Config.GRAFANA_URL,
            'default_output_format': Config.DEFAULT_OUTPUT_FORMAT,
            'tesseract_path': Config.TESSERACT_PATH
        })
    
    elif request.method == 'POST':
        # Note: In a real application, you'd want to persist these settings
        # For now, we'll just return success
        return jsonify({'success': True, 'message': 'Settings would be saved'})

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    print("Starting Grafana Monitoring Agent...")
    print(f"Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"Output folder: {Config.OUTPUT_FOLDER}")
    print(f"Grafana URL: {Config.GRAFANA_URL}")
    
    # Test Grafana connection on startup
    try:
        if grafana_client.test_connection():
            print("✓ Grafana connection successful")
        else:
            print("✗ Grafana connection failed")
    except Exception as e:
        print(f"✗ Grafana connection error: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
