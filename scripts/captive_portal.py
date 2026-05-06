#!/usr/bin/env python3
"""
Captive Portal for Laser DMX Hotspot
Redirects all HTTP traffic to laser-dmx.local when user connects
"""
from flask import Flask, redirect, render_template_string
import socket

app = Flask(__name__)

# Catch all HTTP traffic and redirect to DMX UI
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def captive_portal(path):
    """Redirect to DMX UI"""
    return redirect('http://laser-dmx.local/', code=302)

@app.route('/hotspot.html')
def hotspot():
    """iPhone/Android captive portal detection response"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laser DMX Hotspot</title>
        <meta http-equiv="refresh" content="0; url=http://laser-dmx.local/">
    </head>
    <body>
        <h1>Connecting to Laser DMX...</h1>
        <p>If you are not redirected automatically, <a href="http://laser-dmx.local/">click here</a>.</p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/generate_204')
def generate_204():
    """Android captive portal detection - returns no content"""
    return '', 204

@app.route('/connecttest.txt')
def connecttest():
    """Windows captive portal detection"""
    return 'Microsoft Connect Test'

@app.route('/ncsi.txt')
def ncsi():
    """Windows captive portal detection (alternative)"""
    return 'Microsoft NCSI'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
