"""
Test script for OAuth2/JWT authentication system
Demonstrates registration, login, and authenticated API calls
"""

import requests
import json
import time

# Base URL - update if running elsewhere
BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """Test the complete authentication flow."""
    
    print("🔐 Testing OAuth2/JWT Authentication System")
    print("=" * 50)
    
    # 1. Register a new user
    print("\n1️⃣ Registering new user...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 200:
        print("✅ User registered successfully")
        user_info = response.json()
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
    else:
        print(f"❌ Registration failed: {response.text}")
        # User might already exist, continue anyway
    
    # 2. Login to get tokens
    print("\n2️⃣ Logging in...")
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data=login_data,  # Form data for OAuth2
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        print("✅ Login successful")
        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print(f"   Access token: {access_token[:20]}...")
        print(f"   Refresh token: {refresh_token[:20]}...")
    else:
        print(f"❌ Login failed: {response.text}")
        return
    
    # 3. Get current user info
    print("\n3️⃣ Getting current user info...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        print("✅ User info retrieved")
        user = response.json()
        print(f"   Username: {user['username']}")
        print(f"   Scopes: {user['scopes']}")
    else:
        print(f"❌ Failed to get user info: {response.text}")
    
    # 4. Make authenticated chat request
    print("\n4️⃣ Making authenticated chat request...")
    chat_data = {
        "message": "What are the ticket prices for Lakers games?",
        "conversation_id": None
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=chat_data,
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Chat request successful")
        chat_response = response.json()
        print(f"   Response: {chat_response['response'][:100]}...")
        print(f"   Conversation ID: {chat_response['conversation_id']}")
    else:
        print(f"❌ Chat request failed: {response.text}")
    
    # 5. Get user sessions
    print("\n5️⃣ Getting active sessions...")
    response = requests.get(f"{BASE_URL}/auth/sessions", headers=headers)
    if response.status_code == 200:
        print("✅ Sessions retrieved")
        sessions = response.json()
        print(f"   Active sessions: {len(sessions['sessions'])}")
    else:
        print(f"❌ Failed to get sessions: {response.text}")
    
    # 6. Refresh access token
    print("\n6️⃣ Refreshing access token...")
    refresh_data = {"refresh_token": refresh_token}
    
    response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
    if response.status_code == 200:
        print("✅ Token refreshed")
        new_tokens = response.json()
        new_access_token = new_tokens["access_token"]
        print(f"   New access token: {new_access_token[:20]}...")
    else:
        print(f"❌ Token refresh failed: {response.text}")
    
    # 7. Logout
    print("\n7️⃣ Logging out...")
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    if response.status_code == 200:
        print("✅ Logged out successfully")
    else:
        print(f"❌ Logout failed: {response.text}")
    
    # 8. Try to access protected endpoint after logout (should fail)
    print("\n8️⃣ Testing token revocation...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 401:
        print("✅ Token properly revoked (access denied)")
    else:
        print(f"❌ Token still valid after logout: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ Authentication test complete!")


def test_api_key_auth():
    """Test API key authentication for service-to-service calls."""
    
    print("\n🔑 Testing API Key Authentication")
    print("=" * 50)
    
    # First login as admin
    print("\n1️⃣ Logging in as admin...")
    login_data = {
        "username": "admin",
        "password": "admin123"  # Change in production!
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print("❌ Admin login failed. Make sure the server is running and admin user exists.")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create API key
    print("\n2️⃣ Creating API key...")
    api_key_data = {
        "service_name": "external_service",
        "scopes": ["chat"]
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/api-key/create",
        params=api_key_data,
        headers=admin_headers
    )
    
    if response.status_code == 200:
        print("✅ API key created")
        api_key_info = response.json()
        api_key = api_key_info["api_key"]
        print(f"   API Key: {api_key[:20]}...")
        print(f"   Service: {api_key_info['service']}")
    else:
        print(f"❌ API key creation failed: {response.text}")
        return
    
    # Use API key for chat
    print("\n3️⃣ Using API key for chat...")
    api_headers = {"X-API-Key": api_key}
    chat_data = {
        "message": "Hello from external service!",
        "conversation_id": None
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=chat_data,
        headers=api_headers
    )
    
    if response.status_code == 200:
        print("✅ Chat with API key successful")
        chat_response = response.json()
        print(f"   Response: {chat_response['response'][:100]}...")
    else:
        print(f"❌ Chat with API key failed: {response.text}")
    
    # Validate API key
    print("\n4️⃣ Validating API key...")
    response = requests.get(
        f"{BASE_URL}/auth/api-key/validate",
        headers=api_headers
    )
    
    if response.status_code == 200:
        validation = response.json()
        print(f"✅ API key valid: {validation['valid']}")
        print(f"   Service: {validation['service']}")
        print(f"   Scopes: {validation['scopes']}")
    else:
        print(f"❌ API key validation failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("✅ API key test complete!")


if __name__ == "__main__":
    import sys
    
    print("🚀 OAuth2/JWT Authentication Test Suite")
    print("\nMake sure the server is running:")
    print("  python3 api/main_secure.py")
    print("\nOr with uvicorn:")
    print("  uvicorn api.main_secure:app --reload")
    print("\nPress Enter to start tests...")
    input()
    
    try:
        # Test user authentication flow
        test_auth_flow()
        
        # Test API key authentication
        test_api_key_auth()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server at", BASE_URL)
        print("Make sure the server is running first!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
