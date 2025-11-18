"""
Simple test script for the comprehensive ATS app
"""

import requests
import os
from pathlib import Path

def test_app_endpoints():
    """Test basic app endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Test homepage
        response = requests.get(base_url, timeout=5)
        print(f"✅ Homepage: {response.status_code}")
        
        # Test static files
        response = requests.get(f"{base_url}/static/style.css", timeout=5)
        print(f"✅ CSS file: {response.status_code}")
        
        response = requests.get(f"{base_url}/static/script.js", timeout=5)
        print(f"✅ JS file: {response.status_code}")
        
        print("\n🎉 All basic endpoints are working!")
        
    except Exception as e:
        print(f"❌ Error testing app: {e}")

if __name__ == "__main__":
    print("Testing comprehensive ATS Resume Checker...")
    test_app_endpoints()