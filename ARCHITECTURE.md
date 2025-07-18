# Grafana Monitoring Agent - Architecture & Code Walkthrough

## 🏗️ **System Architecture Overview**

The Grafana Monitoring Agent is a sophisticated Flask-based web application designed to process Grafana dashboard screenshots and generate structured reports using OCR (Optical Character Recognition) technology.

### **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Grafana Monitoring Agent                     │
├─────────────────────────────────────────────────────────────────┤
│  Web Interface (Flask + Bootstrap)                             │
│  ├── Upload Interface (Drag & Drop)                           │
│  ├── Settings Management                                       │
│  ├── Report Downloads                                          │
│  └── Connection Status                                         │
├─────────────────────────────────────────────────────────────────┤
│  Core Processing Engine                                         │
│  ├── Image Processor (OCR + OpenCV)                           │
│  ├── Report Generator (CSV/TXT/JSON)                          │
│  ├── Grafana Client (API Integration)                         │
│  └── Scheduler (Automated Tasks)                              │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ├── Configuration Management                                  │
│  ├── File Storage (Uploads/Outputs)                           │
│  └── Environment Variables                                     │
└─────────────────────────────────────────────────────────────────┘
```

### **Data Flow Architecture**

```
[User Upload] → [Image Processing] → [OCR Extraction] → [Metrics Parsing] → [Report Generation] → [Download]
      │                 │                  │                    │                     │
      │                 │                  │                    │                     │
   [Web UI]    [OpenCV/PIL Processing]  [Tesseract]      [Regex Patterns]    [CSV/TXT/JSON]
      │                 │                  │                    │                     │
      │                 │                  │                    │                     │
   [Flask]           [Image Enhancement]  [Text Extraction]  [Metric Classification] [File Storage]
```

---

## 🔧 **Deep Code Walkthrough**

### **1. Configuration Management (`config.py`)**

```python
class Config:
    """Configuration class for the Grafana monitoring agent"""
```

**Purpose**: Centralized configuration management using environment variables.

**Key Features**:
- **Environment Variable Loading**: Uses `python-dotenv` to load `.env` file
- **Secure Credential Management**: Handles Grafana authentication safely
- **Directory Management**: Automatically creates necessary directories
- **File Validation**: Validates uploaded file types

**Critical Methods**:
- `init_app()`: Initializes Flask application with configuration
- `allowed_file()`: Validates file extensions for security

**Configuration Categories**:
- **Grafana Settings**: URL, credentials, API keys
- **Flask Settings**: Secret key, upload limits, folders
- **OCR Settings**: Tesseract path configuration
- **Report Settings**: Output formats, timestamp formats

---

### **2. Grafana API Client (`grafana_client.py`)**

```python
class GrafanaClient:
    """Client for interacting with Grafana API"""
```

**Purpose**: Handles all interactions with Grafana's REST API.

**Authentication Methods**:
1. **API Key Authentication** (Recommended):
   ```python
   self.session.headers.update({
       'Authorization': f'Bearer {self.api_key}'
   })
   ```

2. **Username/Password Authentication**:
   ```python
   self.session.auth = (self.username, self.password)
   ```

**Key Features**:
- **Connection Testing**: Validates Grafana accessibility
- **Credential Validation**: Ensures authentication works
- **Dashboard Enumeration**: Lists available dashboards
- **Session Management**: Maintains persistent HTTP sessions

**API Endpoints Used**:
- `/api/health` - Health check
- `/api/user` - User validation
- `/api/search?type=dash-db` - Dashboard listing
- `/api/dashboards/uid/{uid}` - Dashboard details

---

### **3. Image Processing Engine (`image_processor.py`)**

```python
class ImageProcessor:
    """Process uploaded images and extract metrics using OCR"""
```

**Purpose**: Converts dashboard screenshots into structured data.

#### **Image Preprocessing Pipeline**:

1. **Image Loading & Validation**:
   ```python
   image = cv2.imread(image_path)
   if image is None:
       raise ValueError(f"Could not read image: {image_path}")
   ```

2. **Grayscale Conversion**:
   ```python
   gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
   ```

3. **Thresholding (OTSU)**:
   ```python
   _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
   ```

4. **Noise Reduction**:
   ```python
   denoised = cv2.medianBlur(thresh, 5)
   ```

5. **Image Scaling** (for small images):
   ```python
   if height < 500 or width < 500:
       scale_factor = max(500/height, 500/width)
       denoised = cv2.resize(denoised, (new_width, new_height))
   ```

#### **OCR Text Extraction**:

**Tesseract Configuration**:
```python
text = pytesseract.image_to_string(pil_image, config='--psm 6')
```

**Page Segmentation Mode 6**: Uniform block of text (optimal for dashboard screenshots)

#### **Metric Extraction Patterns**:

**Regex Patterns for Different Metrics**:
```python
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
```

**Chart Type Detection**:
- Time Series, Bar Charts, Pie Charts
- Gauges, Tables, Single Stats, Heatmaps
- Based on keyword matching in extracted text

---

### **4. Report Generation Engine (`report_generator.py`)**

```python
class ReportGenerator:
    """Generate reports from processed image data"""
```

**Purpose**: Converts extracted metrics into structured reports.

#### **Output Formats**:

1. **CSV Reports**:
   ```python
   df = pd.DataFrame(rows)
   df.to_csv(filepath, index=False)
   ```

2. **TXT Reports**:
   ```python
   f.write("GRAFANA MONITORING REPORT\n")
   f.write("=" * 50 + "\n\n")
   ```

3. **JSON Reports**:
   ```python
   json.dump(report_data, f, indent=2, ensure_ascii=False)
   ```

#### **Data Structuring**:

**CSV Column Mapping**:
- `filename`: Original image filename
- `processed_at`: Processing timestamp
- `dashboard_title`: Extracted dashboard name
- `image_size`: Image dimensions
- `primary_value`: Main metric value
- `status`: System status indicators
- `panel_titles`: Dashboard panel names
- `memory_metrics`: Memory usage values
- `time_metrics`: Time-based measurements

**Summary Statistics**:
- Total metrics extracted
- Unique dashboards processed
- Status indicator counts
- Processing timestamps

---

### **5. Flask Web Application (`app.py`)**

```python
app = Flask(__name__)
Config.init_app(app)
```

**Purpose**: Web interface and API endpoints.

#### **Key Routes**:

1. **Main Interface**:
   ```python
   @app.route('/')
   def index():
       return render_template('index.html')
   ```

2. **File Upload & Processing**:
   ```python
   @app.route('/upload', methods=['POST'])
   def upload_files():
       # Multi-file processing
       # Image analysis
       # Report generation
   ```

3. **Grafana Connection Testing**:
   ```python
   @app.route('/api/test-grafana')
   def test_grafana_connection():
       is_connected = grafana_client.test_connection()
       is_authenticated = grafana_client.validate_credentials()
   ```

4. **Report Management**:
   ```python
   @app.route('/api/reports')
   def list_reports():
       # List generated reports
       # File metadata
   ```

#### **Security Features**:
- **File Type Validation**: Only allow image files
- **File Size Limits**: Configurable upload limits
- **Secure Filenames**: Use `secure_filename()` for uploads
- **CSRF Protection**: Flask's built-in CSRF protection

---

### **6. Automated Scheduler (`scheduler.py`)**

```python
class GrafanaScheduler:
    """Automated scheduler for Grafana monitoring"""
```

**Purpose**: Background automation for continuous monitoring.

#### **Scheduling Features**:

1. **Hourly Dashboard Collection**:
   ```python
   schedule.every(1).hours.do(self.collect_dashboard_info)
   ```

2. **Daily Report Generation**:
   ```python
   schedule.every(1).days.do(self.generate_daily_report)
   ```

3. **Weekly Summary Reports**:
   ```python
   schedule.every().monday.at("09:00").do(self.generate_weekly_report)
   ```

**Automation Benefits**:
- **Continuous Monitoring**: Regular dashboard snapshots
- **Automated Reporting**: No manual intervention required
- **Historical Data**: Build monitoring history over time
- **Alerting Capability**: Can be extended for alerts

---

### **7. Frontend Interface (`templates/index.html`)**

#### **Modern Web Interface Features**:

1. **Drag & Drop Upload**:
   ```javascript
   uploadArea.addEventListener('drop', (e) => {
       e.preventDefault();
       fileInput.files = e.dataTransfer.files;
       updateFilePreview();
   });
   ```

2. **Real-time Connection Status**:
   ```javascript
   async function testConnection() {
       const response = await fetch('/api/test-grafana');
       const data = await response.json();
       // Update UI based on connection status
   }
   ```

3. **Dynamic Report Management**:
   ```javascript
   async function refreshReports() {
       const response = await fetch('/api/reports');
       const reports = await response.json();
       // Update reports list
   }
   ```

4. **Bootstrap Responsive Design**:
   - Mobile-friendly interface
   - Modern card-based layout
   - Font Awesome icons
   - Progress indicators

---

## 🔄 **Processing Workflow**

### **Complete Data Pipeline**:

1. **Image Upload** → User selects/drags dashboard screenshots
2. **File Validation** → Check file type and size
3. **Image Preprocessing** → OpenCV enhancement for OCR
4. **OCR Processing** → Tesseract text extraction
5. **Metric Parsing** → Regex pattern matching
6. **Data Structuring** → Organize into standardized format
7. **Report Generation** → Create CSV/TXT/JSON output
8. **File Storage** → Save reports to outputs folder
9. **Download/Display** → Present results to user

### **Error Handling Strategy**:

- **Graceful Degradation**: Continue processing even if some images fail
- **Detailed Logging**: Comprehensive error messages
- **User Feedback**: Clear error reporting in UI
- **Retry Logic**: Automatic retry for transient failures

---

## 🚀 **Performance Optimizations**

### **Image Processing**:
- **Preprocessing Pipeline**: Optimized for dashboard screenshots
- **Selective Scaling**: Only resize small images
- **Efficient Memory Usage**: Process images sequentially

### **OCR Optimization**:
- **PSM Mode Selection**: Page Segmentation Mode 6 for dashboards
- **Language Configuration**: English-only for speed
- **Preprocessing**: Enhanced contrast and noise reduction

### **Report Generation**:
- **Batch Processing**: Handle multiple images efficiently
- **Memory Management**: Stream large datasets
- **Concurrent Processing**: Can be extended for parallel processing

---

## 🔐 **Security Considerations**

### **File Security**:
- **Type Validation**: Only image files allowed
- **Size Limits**: Prevent DoS attacks
- **Secure Storage**: Isolated upload directory
- **Filename Sanitization**: Prevent directory traversal

### **Configuration Security**:
- **Environment Variables**: Credentials not in code
- **Secret Key Management**: Secure Flask sessions
- **API Key Handling**: Secure Grafana authentication

### **Network Security**:
- **HTTPS Support**: Can be configured for production
- **CORS Configuration**: Controlled cross-origin requests
- **Rate Limiting**: Can be added for production use

---

## 📊 **Monitoring & Maintenance**

### **System Monitoring**:
- **Connection Health**: Grafana API availability
- **Processing Metrics**: Success/failure rates
- **Resource Usage**: Memory and CPU monitoring
- **Error Tracking**: Comprehensive logging

### **Maintenance Tasks**:
- **Regular Cleanup**: Remove old uploads/reports
- **Configuration Updates**: Environment variable management
- **Dependency Updates**: Keep libraries current
- **Performance Tuning**: OCR accuracy improvements

---

## 🛠️ **Extension Points**

### **Planned Enhancements**:
1. **Machine Learning Integration**: Improve chart recognition
2. **Database Storage**: Persistent data storage
3. **API Expansion**: RESTful API for external integration
4. **Real-time Monitoring**: WebSocket connections
5. **Advanced Analytics**: Trend analysis and prediction
6. **Multi-tenant Support**: Organization-based access
7. **Integration APIs**: Slack, Teams, Email notifications
8. **Advanced Scheduling**: Cron-like configuration UI

This architecture provides a robust, scalable foundation for Grafana monitoring with excellent extensibility for future enhancements.
