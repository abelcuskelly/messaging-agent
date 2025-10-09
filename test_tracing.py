"""
Test script for OpenTelemetry Distributed Tracing
Demonstrates trace propagation and observability features
"""

import requests
import json
import time
import asyncio
from typing import Dict, List

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


def test_basic_tracing(token: str):
    """Test basic request tracing."""
    print("\n🔍 Testing Basic Request Tracing")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make a traced request
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "What are the ticket prices?"},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Request traced successfully")
        print(f"   Trace ID: {data['trace_id']}")
        print(f"   Duration: {data['duration_ms']:.2f}ms")
        print(f"   Cached: {data['cached']}")
        
        # Get trace info
        trace_response = requests.get(
            f"{BASE_URL}/trace/{data['trace_id']}",
            headers=headers
        )
        
        if trace_response.status_code == 200:
            trace_data = trace_response.json()
            print(f"\n📊 Trace Details:")
            print(f"   Service: {trace_data['service']}")
            print(f"   Environment: {trace_data['environment']}")
            print(f"   Total Duration: {trace_data['metrics']['total_duration_ms']}ms")
            
            print(f"\n   Spans:")
            for span in trace_data['spans']:
                print(f"     - {span['name']}: {span['duration_ms']}ms")
                for child in span.get('children', []):
                    print(f"       - {child['name']}: {child['duration_ms']}ms")
        
        return data['trace_id']
    else:
        print(f"❌ Request failed: {response.text}")
        return None


def test_trace_propagation(token: str, parent_trace_id: str = None):
    """Test trace context propagation."""
    print("\n🔗 Testing Trace Propagation")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make request with parent trace
    request_data = {
        "message": "Test trace propagation"
    }
    
    if parent_trace_id:
        request_data["trace_id"] = parent_trace_id
        print(f"   Using parent trace: {parent_trace_id}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json=request_data,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Trace propagated successfully")
        print(f"   New Trace ID: {data['trace_id']}")
        
        if parent_trace_id:
            print(f"   Parent Trace: {parent_trace_id}")
            print(f"   Child Trace: {data['trace_id']}")
    else:
        print(f"❌ Request failed: {response.text}")


def test_distributed_tracing(token: str):
    """Test distributed service call tracing."""
    print("\n🌐 Testing Distributed Tracing")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Simulate distributed call
    response = requests.post(
        f"{BASE_URL}/simulate/distributed",
        params={"service": "payment-service"},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Distributed call traced")
        print(f"   Service: {data['service']}")
        print(f"   Result: {data['result']}")
        print(f"   Trace Headers:")
        for key, value in data['trace_headers'].items():
            print(f"     {key}: {value[:50]}...")
    else:
        print(f"❌ Request failed: {response.text}")


def test_baggage(token: str):
    """Test baggage propagation."""
    print("\n🎒 Testing Baggage Propagation")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Set baggage
    response = requests.post(
        f"{BASE_URL}/trace/baggage",
        params={"key": "user_tier", "value": "premium"},
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Baggage set successfully")
        
        # Get baggage
        response = requests.get(
            f"{BASE_URL}/trace/baggage/user_tier",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Key: {data['key']}")
            print(f"   Value: {data['value']}")
    else:
        print(f"❌ Failed to set baggage: {response.text}")


def test_performance_with_tracing(token: str):
    """Test performance impact of tracing."""
    print("\n⚡ Testing Performance with Tracing")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Warm up
    requests.post(
        f"{BASE_URL}/chat",
        json={"message": "warmup"},
        headers=headers
    )
    
    # Test multiple requests
    durations = []
    trace_ids = []
    
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
            trace_ids.append(data['trace_id'])
    
    if durations:
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print(f"📊 Performance Metrics:")
        print(f"   Requests: {len(durations)}")
        print(f"   Average: {avg_duration:.2f}ms")
        print(f"   Min: {min_duration:.2f}ms")
        print(f"   Max: {max_duration:.2f}ms")
        print(f"   Traces Generated: {len(trace_ids)}")
        
        print(f"\n   Sample Trace IDs:")
        for trace_id in trace_ids[:3]:
            print(f"     - {trace_id}")


def check_metrics(token: str):
    """Check application metrics."""
    print("\n📈 Checking Application Metrics")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/metrics")
    
    if response.status_code == 200:
        metrics = response.json()
        
        print("✅ Metrics Retrieved:")
        
        # Cache metrics
        if "cache" in metrics:
            cache_stats = metrics["cache"]
            print(f"\n   Cache Statistics:")
            print(f"     Hits: {cache_stats.get('hits', 0)}")
            print(f"     Misses: {cache_stats.get('misses', 0)}")
            print(f"     Hit Rate: {cache_stats.get('hit_rate', 0):.2%}")
        
        # Telemetry info
        if "telemetry" in metrics:
            telemetry = metrics["telemetry"]
            print(f"\n   Telemetry Configuration:")
            print(f"     Service: {telemetry['service']}")
            print(f"     Version: {telemetry['version']}")
            print(f"     Environment: {telemetry['environment']}")
            print(f"     Prometheus: {telemetry['prometheus_endpoint']}")
        
        # Traces info
        if "traces" in metrics:
            traces = metrics["traces"]
            print(f"\n   Tracing Configuration:")
            print(f"     Jaeger UI: {traces['jaeger_ui']}")
            print(f"     Sampling Rate: {traces['sampling_rate']:.0%}")
    else:
        print(f"❌ Failed to get metrics: {response.text}")


def view_jaeger_instructions():
    """Print instructions for viewing traces in Jaeger."""
    print("\n🔍 Viewing Traces in Jaeger UI")
    print("=" * 50)
    print("\n1. Start Jaeger (if not running):")
    print("   docker run -d --name jaeger \\")
    print("     -p 16686:16686 \\")
    print("     -p 14250:14250 \\")
    print("     jaegertracing/all-in-one")
    print("\n2. Open Jaeger UI:")
    print("   http://localhost:16686")
    print("\n3. Select service:")
    print("   'qwen-messaging-agent'")
    print("\n4. Click 'Find Traces' to see all traces")
    print("\n5. Click on any trace to see detailed span breakdown")


def main():
    """Run all tracing tests."""
    print("🚀 OpenTelemetry Distributed Tracing Test Suite")
    print("\nMake sure the following are running:")
    print("  1. Redis: redis-server")
    print("  2. Jaeger: docker run -p 16686:16686 -p 14250:14250 jaegertracing/all-in-one")
    print("  3. API: python3 api/main_traced.py")
    print("\nPress Enter to start tests...")
    input()
    
    try:
        # Login
        print("Logging in...")
        token = login_user()
        print("✅ Logged in successfully")
        
        # Run tests
        trace_id = test_basic_tracing(token)
        test_trace_propagation(token, trace_id)
        test_distributed_tracing(token)
        test_baggage(token)
        test_performance_with_tracing(token)
        check_metrics(token)
        view_jaeger_instructions()
        
        print("\n" + "=" * 50)
        print("✅ All tracing tests completed!")
        print("\n💡 Check Jaeger UI for visual trace analysis:")
        print("   http://localhost:16686")
        
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
