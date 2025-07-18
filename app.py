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
from openai_processor import OpenAIProcessor
from llm_report_generator import LLMReportGenerator

app = Flask(__name__)
Config.init_app(app)

# Initialize components
image_processor = ImageProcessor()
report_generator = ReportGenerator()
grafana_client = GrafanaClient()
openai_processor = OpenAIProcessor()
llm_report_generator = LLMReportGenerator()

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
        processing_method = request.form.get('processing_method', 'llm')  # 'llm' or 'ocr'
        custom_prompt = request.form.get('custom_prompt', '')
        
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
                
                # Process image based on method
                if processing_method == 'llm':
                    # Use OpenAI LLM processing
                    if custom_prompt:
                        result = openai_processor.process_image_with_custom_prompt(filepath, custom_prompt)
                    else:
                        result = openai_processor.analyze_dashboard_image(filepath)
                    
                    if result:
                        # Add image info to result
                        result['image_info'] = {
                            'filename': filename,
                            'filepath': filepath,
                            'processing_method': 'llm'
                        }
                        processed_data.append(result)
                else:
                    # Use traditional OCR processing
                    result = image_processor.process_image(filepath)
                    if result:
                        result['processing_method'] = 'ocr'
                        processed_data.append(result)
        
        if not processed_data:
            return jsonify({'error': 'No images could be processed'}), 400
        
        # Generate report based on processing method
        if processing_method == 'llm':
            if output_format == 'csv':
                report_path = llm_report_generator.generate_llm_csv_report(processed_data)
            elif output_format == 'txt':
                report_path = llm_report_generator.generate_llm_txt_report(processed_data)
            elif output_format == 'json':
                report_path = llm_report_generator.generate_llm_json_report(processed_data)
            else:
                return jsonify({'error': 'Invalid output format'}), 400
        else:
            # Use traditional report generator
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
                'processing_method': processing_method,
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

@app.route('/api/test-openai')
def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        is_connected = openai_processor.test_api_connection()
        
        return jsonify({
            'connected': is_connected,
            'model': Config.OPENAI_MODEL,
            'vision_enabled': Config.USE_OPENAI_VISION,
            'api_key_configured': bool(Config.OPENAI_API_KEY)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-with-prompt', methods=['POST'])
def analyze_with_custom_prompt():
    """Analyze image with custom prompt"""
    try:
        data = request.get_json()
        image_path = data.get('image_path', '')
        custom_prompt = data.get('prompt', '')
        
        if not image_path or not custom_prompt:
            return jsonify({'error': 'Image path and prompt are required'}), 400
        
        # Check if image exists
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image not found'}), 404
        
        # Analyze with custom prompt
        result = openai_processor.process_image_with_custom_prompt(image_path, custom_prompt)
        
        if result:
            return jsonify({
                'success': True,
                'analysis': result,
                'processed_at': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to analyze image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-comparative-report', methods=['POST'])
def generate_comparative_report():
    """Generate comparative report from multiple analyses"""
    try:
        data = request.get_json()
        report_files = data.get('report_files', [])
        
        if not report_files:
            return jsonify({'error': 'No report files provided'}), 400
        
        # Load analysis data from files
        analysis_data_list = []
        for report_file in report_files:
            file_path = os.path.join(Config.OUTPUT_FOLDER, report_file)
            if os.path.exists(file_path) and report_file.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    if 'dashboards' in report_data:
                        analysis_data_list.extend(report_data['dashboards'])
        
        if not analysis_data_list:
            return jsonify({'error': 'No valid analysis data found'}), 400
        
        # Generate comparative report
        report_path = llm_report_generator.generate_comparative_report(analysis_data_list)
        
        if report_path:
            return jsonify({
                'success': True,
                'report_file': os.path.basename(report_path),
                'dashboards_analyzed': len(analysis_data_list)
            })
        else:
            return jsonify({'error': 'Failed to generate comparative report'}), 500
            
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
