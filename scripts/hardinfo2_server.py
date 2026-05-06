#!/usr/bin/env python
"""
HardInfo2 Simple HTTP Server
Serves HardInfo2 system information reports via HTTP on port 8888
No Flask - just simple Python HTTP server
"""

import subprocess
import http.server
import socketserver
import threading
import time
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PORT = 8888

# Cache for reports (refresh every 60 seconds)
report_cache = {
    'html': None,
    'text': None,
    'timestamp': 0
}
CACHE_TTL = 60


def generate_hardinfo_report(format_type='html'):
    """Generate a HardInfo2 report in the specified format"""
    try:
        cmd = ['hardinfo2', '--quiet', '--generate-report', '--report-format', format_type]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Generated {format_type} report successfully")
            return result.stdout
        else:
            logger.error(f"Failed to generate {format_type} report: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"HardInfo2 report generation timed out ({format_type})")
        return None
    except Exception as e:
        logger.error(f"Error generating HardInfo2 report: {e}")
        return None


def get_cached_report(format_type='html'):
    """Get cached report or generate new one if cache expired"""
    now = time.time()
    
    if report_cache[format_type] is None or (now - report_cache['timestamp']) > CACHE_TTL:
        logger.info(f"Cache miss for {format_type} report, generating...")
        report_cache[format_type] = generate_hardinfo_report(format_type)
        report_cache['timestamp'] = now
    else:
        logger.info(f"Serving cached {format_type} report")
    
    return report_cache[format_type]


class HardInfo2Handler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for HardInfo2"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HardInfo2 System Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .links {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 30px;
        }
        
        a {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 15px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
            text-align: center;
        }
        
        a:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .info-box {
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 13px;
            color: #666;
            line-height: 1.6;
        }
        
        .info-box strong {
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ HardInfo2 System Monitor</h1>
        <p class="subtitle">Real-time system information</p>
        
        <div class="links">
            <a href="/report/html">📄 HTML Report</a>
            <a href="/report/text">�� Text Report</a>
        </div>
        
        <div class="info-box">
            <strong>About HardInfo2:</strong><br>
            HardInfo2 is a system information tool that displays detailed information about your system hardware and software.
        </div>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/report/html':
            report = get_cached_report('html')
            if report:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(report.encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Error generating report")
        
        elif self.path == '/report/text':
            report = get_cached_report('text')
            if report:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(report.encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Error generating report")
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"404 Not Found\n\nAvailable endpoints:\n  /\n  /report/html\n  /report/text")
    
    def log_message(self, format, *args):
        """Log HTTP requests"""
        logger.info("%s - %s" % (self.client_address[0], format%args))


def main():
    """Start the HTTP server"""
    logger.info(f"Starting HardInfo2 HTTP Server on port {PORT}...")
    
    with socketserver.TCPServer(("", PORT), HardInfo2Handler) as httpd:
        logger.info(f"Server running at http://0.0.0.0:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped")


if __name__ == '__main__':
    main()
