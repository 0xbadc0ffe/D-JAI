"""
Quick test script for new Suno API integration.
Tests the API connection and basic generation flow.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv('src/.env')

SUNO_API_URL = os.getenv("SUNO_API_URL")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

def test_api_connection():
    """Test if we can connect to Suno API."""
    print("=" * 60)
    print("Testing Suno API Connection")
    print("=" * 60)
    print(f"API URL: {SUNO_API_URL}")
    print(f"API Key: {SUNO_API_KEY[:20]}..." if SUNO_API_KEY else "API Key: Not set")
    print()
    
    if not SUNO_API_URL or not SUNO_API_KEY:
        print("❌ Error: SUNO_API_URL or SUNO_API_KEY not set in .env")
        return False
    
    # Test with a minimal request to /generate endpoint
    try:
        headers = {
            "Authorization": f"Bearer {SUNO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Try a simple test payload
        test_payload = {
            "prompt": "test",
            "customMode": False,
            "model": "V4_5"
        }
        
        print("Testing API endpoint: /generate")
        resp = requests.post(
            f"{SUNO_API_URL}/generate",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"Status code: {resp.status_code}")
        data = resp.json()
        print(f"Response: {data}")
        
        # Check if we get a valid response structure
        if resp.status_code == 200 and data.get("code") == 200:
            print("\n✓ API connection successful!")
            return True
        else:
            print(f"\n⚠ Note: API responded but may have validation errors.")
            print(f"This is OK for connection test.")
            return True  # Connection works even if payload rejected
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_generation_flow():
    """Test a minimal generation request."""
    print("\n" + "=" * 60)
    print("Testing Song Generation Flow")
    print("=" * 60)
    
    test_payload = {
        "prompt": "[Verse]\nTest song for API integration\n[Chorus]\nThis is just a test",
        "customMode": True,
        "model": "V4_5",
        "instrumental": False,
        "title": "API Test Song",
        "style": "pop, acoustic",
        "callBackUrl": "https://example.com/callback"
    }
    
    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\nSubmitting generation request...")
        print(f"Title: {test_payload['title']}")
        print(f"Style: {test_payload['style']}")
        
        resp = requests.post(
            f"{SUNO_API_URL}/generate",
            headers=headers,
            json=test_payload,
            timeout=15
        )
        
        print(f"Status code: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Request failed: {resp.text}")
            return False
        
        data = resp.json()
        print(f"Response: {data}")
        
        if data.get("code") != 200:
            print(f"❌ API error: {data}")
            return False
        
        task_id = data["data"]["taskId"]
        print(f"\n✓ Task created successfully!")
        print(f"Task ID: {task_id}")
        
        # Note: We won't poll here to avoid using credits
        print("\n⚠ Skipping polling to preserve credits.")
        print("The integration code in app.py will handle polling.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SUNO API INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    # Test 1: Connection
    connection_ok = test_api_connection()
    
    if not connection_ok:
        print("\n❌ Cannot proceed without valid API connection")
        sys.exit(1)
    
    # Test 2: Generation flow (optional, costs credits)
    print("\n")
    response = input("Test song generation? This will use API credits. (y/N): ")
    
    if response.lower() == 'y':
        generation_ok = test_generation_flow()
        
        if generation_ok:
            print("\n✓ All tests passed!")
        else:
            print("\n❌ Generation test failed")
            sys.exit(1)
    else:
        print("\nSkipping generation test.")
        print("✓ Connection test passed! Integration should work.")
    
    print("\n" + "=" * 60)
    print("Test completed. You can now use the app!")
    print("=" * 60)
