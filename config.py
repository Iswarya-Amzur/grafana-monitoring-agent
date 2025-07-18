import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Grafana monitoring agent"""
    
    # Grafana Configuration
    GRAFANA_URL = os.getenv('GRAFANA_URL', 'http://localhost:3000')
    GRAFANA_USERNAME = os.getenv('GRAFANA_USERNAME', '')
    GRAFANA_PASSWORD = os.getenv('GRAFANA_PASSWORD', '')
    GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY', '')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    USE_OPENAI_VISION = os.getenv('USE_OPENAI_VISION', 'true').lower() == 'true'
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 4000))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.1))
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'outputs')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # OCR Configuration
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    
    # Report Configuration
    DEFAULT_OUTPUT_FORMAT = os.getenv('DEFAULT_OUTPUT_FORMAT', 'csv')
    REPORT_TIMESTAMP_FORMAT = os.getenv('REPORT_TIMESTAMP_FORMAT', '%Y-%m-%d_%H-%M-%S')
    
    # Supported file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    
    @staticmethod
    def init_app(app):
        """Initialize Flask app with configuration"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        
        # Set Flask configuration
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
