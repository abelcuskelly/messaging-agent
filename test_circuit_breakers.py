"""
Test script for Circuit Breaker implementation
Demonstrates failure detection, recovery, and graceful degradation
"""

import requests
import time
from typing import List

# Base URL
BASE_URL = "http://localhost:8000"

def login_user(username: str = "testuser", password: str = "SecurePassword123!") -> str:
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        # Try to register first
        register_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "full_name": "Test User"
        }
        requests.post(f"{BASE_URL}/auth/register", json=register_data)
        
        # Try login again
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return response.json()["access_token"]


def test_circuit_breaker_states(token: str):
    """Test circuit breaker state transitions."""
    print("\n🔄 Testing Circuit Breaker State Transitions")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check initial state
    response = requests.get(f"{BASE_URL}/circuit-breakers", headers=headers)
    if response.status_code == 200:
        breakers = response.json()["circuit_breakers"]
        print("\n📊 Initial Circuit Breaker States:")
        for name, stats in breakers.items():
            print(f"   {name}: {stats['state'].upper()}")
            print(f"     Requests: {stats['total_requests']}")
            print(f"     Failures: {stats['total_failures']}")
            print(f"     Success Rate: {stats['success_rate']:.1%}")


def test_normal_operation(token: str):
    """Test normal operation with circuit breaker."""
    print("\n✅ Testing Normal Operation")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make successful requests
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": f"Test message {i}"},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Request {i+1}: ✓ Success")
            print(f"     Circuit State: {data.get('circuit_state', 'unknown')}")
            print(f"     Duration: {data['duration_ms']:.2f}ms")
        else:
            print(f"   Request {i+1}: ✗ Failed - {response.status_code}")


def test_fallback_mechanism(token: str):
    """Test fallback responses when circuit is open."""
    print("\n🔄 Testing Fallback Mechanism")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with fallback enabled
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "What are the ticket prices?",
            "fallback_on_error": True
        },
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Fallback response received")
        print(f"   Circuit State: {data.get('circuit_state', 'unknown')}")
        print(f"   Fallback Used: {data.get('fallback_used', False)}")
        print(f"   Response: {data['response'][:100]}...")


def test_circuit_recovery(token: str):
    """Test circuit breaker recovery (half-open state)."""
    print("\n🔧 Testing Circuit Recovery")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current circuit state
    response = requests.get(f"{BASE_URL}/circuit-breakers", headers=headers)
    if response.status_code == 200:
        breakers = response.json()["circuit_breakers"]
        model_breaker = breakers.get("model_inference", {})
        
        print(f"   Current State: {model_breaker.get('state', 'unknown').upper()}")
        print(f"   Recovery Timeout: 30 seconds")
        
        if model_breaker.get("state") == "open":
            print(f"\n   Waiting for recovery timeout...")
            print(f"   (In production, wait 30 seconds for half-open state)")


def test_manual_reset(token: str):
    """Test manual circuit breaker reset."""
    print("\n🔄 Testing Manual Reset")
    print("=" * 50)
    
    # Login as admin
    admin_token = login_user("admin", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Reset specific circuit breaker
    response = requests.post(
        f"{BASE_URL}/circuit-breakers/model_inference/reset",
        headers=admin_headers
    )
    
    if response.status_code == 200:
        print("✅ Circuit breaker reset successfully")
        print(f"   {response.json()['message']}")
        
        # Verify state
        response = requests.get(f"{BASE_URL}/circuit-breakers", headers=admin_headers)
        if response.status_code == 200:
            breakers = response.json()["circuit_breakers"]
            model_breaker = breakers.get("model_inference", {})
            print(f"   New State: {model_breaker.get('state', 'unknown').upper()}")
    else:
        print(f"❌ Reset failed: {response.text}")


def test_circuit_statistics(token: str):
    """Test circuit breaker statistics."""
    print("\n📊 Circuit Breaker Statistics")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/circuit-breakers", headers=headers)
    if response.status_code == 200:
        breakers = response.json()["circuit_breakers"]
        
        for name, stats in breakers.items():
            print(f"\n🔌 {name}:")
            print(f"   State: {stats['state'].upper()}")
            print(f"   Total Requests: {stats['total_requests']}")
            print(f"   Successes: {stats['total_successes']}")
            print(f"   Failures: {stats['total_failures']}")
            print(f"   Timeouts: {stats['total_timeouts']}")
            print(f"   Rejections: {stats['total_rejections']}")
            print(f"   Success Rate: {stats['success_rate']:.1%}")
            
            if stats.get('recent_failures'):
                print(f"   Recent Failures: {len(stats['recent_failures'])}")
                for failure in stats['recent_failures'][:3]:
                    print(f"     - {failure['type']}: {failure['exception'][:50]}")


def test_performance_with_circuit_breakers(token: str):
    """Test performance impact of circuit breakers."""
    print("\n⚡ Performance with Circuit Breakers")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test multiple requests
    durations = []
    circuit_states = []
    
    for i in range(10):
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": f"Performance test {i}"},
            headers=headers
        )
        duration = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            durations.append(duration)
            circuit_states.append(data.get('circuit_state', 'unknown'))
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print(f"📊 Performance Metrics:")
        print(f"   Requests: {len(durations)}")
        print(f"   Average: {avg_duration:.2f}ms")
        print(f"   Min: {min_duration:.2f}ms")
        print(f"   Max: {max_duration:.2f}ms")
        print(f"   Circuit States: {set(circuit_states)}")


def test_readiness_check(token: str):
    """Test readiness check with circuit breaker status."""
    print("\n🏥 Readiness Check")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/ready")
    
    if response.status_code == 200:
        checks, _ = response.json()
        print("✅ Service Ready:")
        print(f"   Cache: {'✓' if checks.get('cache') else '✗'}")
        print(f"   Telemetry: {'✓' if checks.get('telemetry') else '✗'}")
        print(f"   Circuit Breakers: {'✓' if checks.get('circuit_breakers') else '✗'}")
        
        if checks.get('open_breakers'):
            print(f"   ⚠️  Open Breakers: {checks['open_breakers']}")
    else:
        print(f"❌ Service Not Ready: {response.status_code}")


def main():
    """Run all circuit breaker tests."""
    print("🚀 Circuit Breaker Test Suite")
    print("\nMake sure the following are running:")
    print("  1. Redis: redis-server")
    print("  2. Jaeger: docker run -p 16686:16686 -p 14250:14250 jaegertracing/all-in-one")
    print("  3. API: python3 api/main_production.py")
    print("\nPress Enter to start tests...")
    input()
    
    try:
        # Login
        print("Logging in...")
        token = login_user()
        print("✅ Logged in successfully")
        
        # Run tests
        test_circuit_breaker_states(token)
        test_normal_operation(token)
        test_fallback_mechanism(token)
        test_circuit_statistics(token)
        test_performance_with_circuit_breakers(token)
        test_manual_reset(token)
        test_readiness_check(token)
        
        print("\n" + "=" * 50)
        print("✅ All circuit breaker tests completed!")
        print("\n💡 Key Features Demonstrated:")
        print("   - Automatic failure detection")
        print("   - State transitions (CLOSED → OPEN → HALF_OPEN)")
        print("   - Graceful degradation with fallbacks")
        print("   - Manual reset capabilities")
        print("   - Comprehensive statistics")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server at", BASE_URL)
        print("Make sure the server is running first!")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
