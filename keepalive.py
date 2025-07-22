#!/usr/bin/env python3
"""
Keepalive server for Discord Stock Bot
Simple HTTP server for UptimeRobot monitoring

This file creates a minimal web server that responds to ping requests
to keep the bot alive on cloud platforms like Replit.
"""

import os
import threading
import time
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPRequestHandler):
    """HTTP request handler for keepalive server"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'status': 'alive',
                    'service': 'Discord Stock Bot Keepalive',
                    'timestamp': datetime.now().isoformat(),
                    'uptime': time.time() - server_start_time,
                    'version': '1.0.0'
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path == '/ping':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'status': 'pong',
                    'timestamp': datetime.now().isoformat(),
                    'uptime': time.time() - server_start_time
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Check if main bot files exist
                bot_files = ['main.py', 'config.py', 'stock_data.py', 'ai_advisor.py']
                files_exist = {file: os.path.exists(file) for file in bot_files}
                
                response = {
                    'status': 'healthy' if all(files_exist.values()) else 'degraded',
                    'timestamp': datetime.now().isoformat(),
                    'uptime': time.time() - server_start_time,
                    'files': files_exist,
                    'data_directory': os.path.exists('data'),
                    'charts_directory': os.path.exists('charts')
                }
                
                self.wfile.write(json.dumps(response).encode())
                
            elif self.path == '/stats':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Get basic stats
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': time.time() - server_start_time,
                    'tracked_stocks': 0,
                    'data_files': []
                }
                
                # Count tracked stocks if file exists
                tracked_stocks_file = 'data/tracked_stocks.json'
                if os.path.exists(tracked_stocks_file):
                    try:
                        with open(tracked_stocks_file, 'r') as f:
                            data = json.load(f)
                            stats['tracked_stocks'] = len(data.get('stocks', []))
                    except:
                        pass
                
                # List data files
                if os.path.exists('data'):
                    for filename in os.listdir('data'):
                        if filename.endswith('.json'):
                            file_path = os.path.join('data', filename)
                            file_stats = os.stat(file_path)
                            stats['data_files'].append({
                                'name': filename,
                                'size': file_stats.st_size,
                                'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                            })
                
                self.wfile.write(json.dumps(stats).encode())
                
            else:
                # 404 for other paths
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'error': 'Not found',
                    'timestamp': datetime.now().isoformat(),
                    'available_endpoints': ['/', '/ping', '/health', '/stats']
                }
                
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'error': 'Internal server error',
                'timestamp': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
    
    def do_HEAD(self):
        """Handle HEAD requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override log message to use our logger"""
        logger.info(f"Request: {format % args}")

class KeepAliveServer:
    """Keepalive server manager"""
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Start the keepalive server"""
        try:
            self.httpd = HTTPServer((self.host, self.port), KeepAliveHandler)
            self.running = True
            
            logger.info(f"Keepalive server starting on {self.host}:{self.port}")
            logger.info(f"Available endpoints:")
            logger.info(f"  http://{self.host}:{self.port}/ - Service status")
            logger.info(f"  http://{self.host}:{self.port}/ping - Simple ping")
            logger.info(f"  http://{self.host}:{self.port}/health - Health check")
            logger.info(f"  http://{self.host}:{self.port}/stats - Bot statistics")
            
            self.httpd.serve_forever()
            
        except KeyboardInterrupt:
            logger.info("Keepalive server stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting keepalive server: {e}")
            self.running = False
    
    def start_in_thread(self):
        """Start the server in a separate thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("Keepalive server is already running")
            return
        
        self.thread = threading.Thread(target=self.start, daemon=True)
        self.thread.start()
        
        # Wait a moment to ensure server starts
        time.sleep(1)
        
        if self.running:
            logger.info(f"Keepalive server started successfully in background thread")
        else:
            logger.error("Failed to start keepalive server")
    
    def stop(self):
        """Stop the keepalive server"""
        self.running = False
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            logger.info("Keepalive server stopped")

# Global variable to track server start time
server_start_time = time.time()

def main():
    """Main function for standalone usage"""
    # Configuration from environment variables
    host = os.getenv('KEEPALIVE_HOST', '0.0.0.0')
    port = int(os.getenv('KEEPALIVE_PORT', '5000'))
    
    # Create and start server
    server = KeepAliveServer(host, port)
    
    try:
        logger.info("Starting Discord Stock Bot Keepalive Server")
        logger.info("Press Ctrl+C to stop")
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop()

if __name__ == "__main__":
    main()