import requests
import json
from datetime import datetime
from config import Config

class GrafanaClient:
    """Client for interacting with Grafana API"""
    
    def __init__(self):
        self.base_url = Config.GRAFANA_URL.rstrip('/')
        self.username = Config.GRAFANA_USERNAME
        self.password = Config.GRAFANA_PASSWORD
        self.api_key = Config.GRAFANA_API_KEY
        self.session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup authentication for Grafana API"""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        elif self.username and self.password:
            self.session.auth = (self.username, self.password)
            self.session.headers.update({
                'Content-Type': 'application/json'
            })
        else:
            raise ValueError("Either API key or username/password must be provided")
    
    def test_connection(self):
        """Test connection to Grafana"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_dashboards(self):
        """Get list of all dashboards"""
        try:
            response = self.session.get(f"{self.base_url}/api/search?type=dash-db")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get dashboards: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting dashboards: {e}")
            return []
    
    def get_dashboard_by_uid(self, uid):
        """Get dashboard by UID"""
        try:
            response = self.session.get(f"{self.base_url}/api/dashboards/uid/{uid}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get dashboard {uid}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting dashboard {uid}: {e}")
            return None
    
    def get_dashboard_snapshot(self, dashboard_id, panel_id=None, width=1000, height=500):
        """Get dashboard snapshot (if available)"""
        try:
            params = {
                'width': width,
                'height': height,
                'tz': 'UTC'
            }
            if panel_id:
                params['panelId'] = panel_id
            
            url = f"{self.base_url}/render/d-solo/{dashboard_id}"
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"Failed to get snapshot: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting snapshot: {e}")
            return None
    
    def validate_credentials(self):
        """Validate Grafana credentials"""
        try:
            response = self.session.get(f"{self.base_url}/api/user")
            return response.status_code == 200
        except Exception as e:
            print(f"Credential validation failed: {e}")
            return False
