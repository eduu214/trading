#!/usr/bin/env python3
"""
Simple HTTP server to serve the WebSocket UI test page
Task 19: Interactive UI testing for real-time progress updates
"""
import http.server
import socketserver
import webbrowser
import os
import sys
from threading import Timer

def open_browser():
    """Open browser after a short delay"""
    webbrowser.open('http://localhost:8080/websocket_ui_test.html')

def serve_ui():
    """Start the HTTP server"""
    PORT = 8080
    
    # Change to the trading directory
    trading_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(trading_dir)
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("🚀 WebSocket UI Test Server")
            print("=" * 40)
            print(f"📡 Server running at: http://localhost:{PORT}")
            print(f"🔗 UI Test Page: http://localhost:{PORT}/websocket_ui_test.html")
            print("=" * 40)
            print("\n🎯 Instructions:")
            print("1. Make sure the backend is running (docker-compose up)")
            print("2. Open the UI test page in your browser")
            print("3. Click 'Connect to WebSocket'")
            print("4. Start a backtest to see real-time progress")
            print("5. Monitor latency metrics (<1s requirement)")
            print("\n💡 Features to test:")
            print("• WebSocket connection/disconnection")
            print("• Real-time progress updates")
            print("• Latency measurements")
            print("• Multiple concurrent backtests")
            print("• Message logging and export")
            print("\nPress Ctrl+C to stop the server")
            print("=" * 40)
            
            # Open browser after 2 seconds
            Timer(2.0, open_browser).start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thanks for testing!")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use.")
            print("Try closing other applications or use a different port.")
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    serve_ui()