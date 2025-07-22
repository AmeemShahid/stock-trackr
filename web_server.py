"""
Simple web server for ping endpoint to keep bot alive
"""

import threading
import logging
from datetime import datetime
import json
import os

try:
    from flask import Flask, jsonify, request
    flask_available = True
except ImportError:
    Flask = None
    jsonify = None
    request = None
    flask_available = False

from config import Config

logger = logging.getLogger(__name__)

class WebServer:
    """Simple web server for uptime monitoring"""
    
    def __init__(self):
        self.config = Config()
        
        if Flask is None:
            logger.warning("Flask not installed. Web server will not be available.")
            self.app = None
            return
        
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup web server routes"""
        if not self.app:
            return
        
        @self.app.route('/')
        def home():
            """Home endpoint for basic info"""
            return jsonify({
                'status': 'online',
                'service': 'Discord Stock Bot',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/ping')
        def ping():
            """Ping endpoint for UptimeRobot"""
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'uptime': True
            })
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            try:
                # Check if data files exist and are accessible
                data_dir = self.config.DATA_DIR
                charts_dir = self.config.CHARTS_DIR
                
                health_status = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'data_directory': os.path.exists(data_dir),
                    'charts_directory': os.path.exists(charts_dir),
                    'config_loaded': True
                }
                
                # Check tracked stocks file
                tracked_stocks_file = self.config.get_tracked_stocks_file()
                health_status['tracked_stocks_file'] = os.path.exists(tracked_stocks_file)
                
                # Check user preferences file
                user_prefs_file = self.config.get_user_preferences_file()
                health_status['user_preferences_file'] = os.path.exists(user_prefs_file)
                
                return jsonify(health_status)
                
            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }), 500
        
        @self.app.route('/stats')
        def stats():
            """Bot statistics endpoint"""
            try:
                stats_data = {
                    'timestamp': datetime.now().isoformat(),
                    'tracked_stocks': 0,
                    'data_files': []
                }
                
                # Count tracked stocks
                tracked_stocks_file = self.config.get_tracked_stocks_file()
                if os.path.exists(tracked_stocks_file):
                    try:
                        with open(tracked_stocks_file, 'r') as f:
                            data = json.load(f)
                            stats_data['tracked_stocks'] = len(data.get('stocks', []))
                            stats_data['last_updated'] = data.get('last_updated')
                    except:
                        pass
                
                # List data files
                data_dir = self.config.DATA_DIR
                if os.path.exists(data_dir):
                    for filename in os.listdir(data_dir):
                        if filename.endswith('.json'):
                            file_path = os.path.join(data_dir, filename)
                            file_stats = os.stat(file_path)
                            stats_data['data_files'].append({
                                'name': filename,
                                'size': file_stats.st_size,
                                'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                            })
                
                return jsonify(stats_data)
                
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/tracked-stocks')
        def api_tracked_stocks():
            """API endpoint to get tracked stocks"""
            try:
                tracked_stocks_file = self.config.get_tracked_stocks_file()
                if not os.path.exists(tracked_stocks_file):
                    return jsonify({'stocks': [], 'count': 0})
                
                with open(tracked_stocks_file, 'r') as f:
                    data = json.load(f)
                    return jsonify(data)
                    
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'Not found',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'error': 'Internal server error',
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def run(self):
        """Run the web server"""
        if not self.app:
            logger.warning("Web server not available (Flask not installed)")
            return
        
        try:
            logger.info(f"Starting web server on {self.config.WEB_HOST}:{self.config.WEB_PORT}")
            self.app.run(
                host=self.config.WEB_HOST,
                port=self.config.WEB_PORT,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Error running web server: {e}")
    
    def run_in_thread(self):
        """Run web server in a separate thread"""
        if not self.app:
            return None
        
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
