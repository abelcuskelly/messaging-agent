"""
Test script to demonstrate Redis caching performance improvements
Shows dramatic speed improvements with caching
"""

import requests
import time
import statistics
from typing import List, Dict
import json

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


def test_chat_caching(token: str):
    """Test chat response caching performance."""
    print("\n🚀 Testing Chat Response Caching")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    test_messages = [
        "What are the ticket prices for Lakers games?",
        "Tell me about the refund policy",
        "Where can I park at the arena?",
        "What time do games usually start?",
        "How do I upgrade my seat?"
    ]
    
    for message in test_messages:
        print(f"\nTesting: {message[:40]}...")
        
        # First request (cache miss)
        start_time = time.time()
        response1 = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "use_cache": True},
            headers=headers
        )
        time1 = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"  ❌ Cache miss: {time1:.2f}ms (cached={data1.get('cached', False)})")
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "use_cache": True},
            headers=headers
        )
        time2 = (time.time() - start_time) * 1000
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"  ✅ Cache hit:  {time2:.2f}ms (cached={data2.get('cached', False)})")
            
            # Calculate improvement
            if time1 > 0:
                improvement = ((time1 - time2) / time1) * 100
                speedup = time1 / time2 if time2 > 0 else float('inf')
                print(f"  📊 Performance: {improvement:.1f}% faster ({speedup:.1f}x speedup)")


def test_knowledge_base_caching(token: str):
    """Test knowledge base search caching."""
    print("\n📚 Testing Knowledge Base Caching")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    test_queries = [
        "ticket prices",
        "refund policy",
        "parking information",
        "game schedule",
        "seat upgrades"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # First request (cache miss)
        start_time = time.time()
        response1 = requests.get(
            f"{BASE_URL}/knowledge-base/search",
            params={"query": query, "top_k": 5},
            headers=headers
        )
        time1 = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"  ❌ Cache miss: {time1:.2f}ms")
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = requests.get(
            f"{BASE_URL}/knowledge-base/search",
            params={"query": query, "top_k": 5},
            headers=headers
        )
        time2 = (time.time() - start_time) * 1000
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"  ✅ Cache hit:  {time2:.2f}ms")
            
            if time1 > 0 and time2 > 0:
                speedup = time1 / time2
                print(f"  📊 Speedup: {speedup:.1f}x faster")


def test_embedding_caching(token: str):
    """Test embedding generation caching."""
    print("\n🧮 Testing Embedding Caching")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    test_texts = [
        "Lakers vs Warriors game",
        "Refund policy information",
        "Parking at Crypto.com Arena"
    ]
    
    for text in test_texts:
        print(f"\nText: {text[:40]}...")
        
        # First request (cache miss)
        start_time = time.time()
        response1 = requests.post(
            f"{BASE_URL}/embeddings",
            params={"text": text},
            headers=headers
        )
        time1 = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"  ❌ Cache miss: {time1:.2f}ms")
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = requests.post(
            f"{BASE_URL}/embeddings",
            params={"text": text},
            headers=headers
        )
        time2 = (time.time() - start_time) * 1000
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"  ✅ Cache hit:  {time2:.2f}ms")
            
            if time1 > 0 and time2 > 0:
                speedup = time1 / time2
                print(f"  📊 Speedup: {speedup:.1f}x faster")


def test_computation_caching(token: str):
    """Test cached computation."""
    print("\n🔢 Testing Computation Caching")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    test_params = [(10, 20), (15, 25), (30, 40)]
    
    for x, y in test_params:
        print(f"\nComputation: {x} * {y} * 1000")
        
        # First request (cache miss - slow)
        start_time = time.time()
        response1 = requests.get(
            f"{BASE_URL}/compute",
            params={"x": x, "y": y},
            headers=headers
        )
        time1 = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"  ❌ Cache miss: {time1:.2f}ms (result={data1['result']})")
        
        # Second request (cache hit - fast)
        start_time = time.time()
        response2 = requests.get(
            f"{BASE_URL}/compute",
            params={"x": x, "y": y},
            headers=headers
        )
        time2 = (time.time() - start_time) * 1000
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"  ✅ Cache hit:  {time2:.2f}ms (result={data2['result']})")
            
            if time1 > 0 and time2 > 0:
                speedup = time1 / time2
                print(f"  📊 Speedup: {speedup:.1f}x faster")


def test_cache_statistics(token: str):
    """Get and display cache statistics."""
    print("\n📊 Cache Statistics")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get admin token
    admin_token = login_user("admin", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = requests.get(f"{BASE_URL}/cache/stats", headers=admin_headers)
    
    if response.status_code == 200:
        stats = response.json()
        
        print("\nCache Performance:")
        cache_stats = stats.get("stats", {})
        print(f"  Total Requests: {cache_stats.get('total_requests', 0)}")
        print(f"  Cache Hits: {cache_stats.get('hits', 0)}")
        print(f"  Cache Misses: {cache_stats.get('misses', 0)}")
        print(f"  Hit Rate: {cache_stats.get('hit_rate', 0):.2%}")
        print(f"  Errors: {cache_stats.get('errors', 0)}")
        
        redis_info = stats.get("redis_info", {})
        if redis_info:
            print("\nRedis Server Info:")
            print(f"  Version: {redis_info.get('version', 'N/A')}")
            print(f"  Memory Used: {redis_info.get('used_memory', 'N/A')}")
            print(f"  Connected Clients: {redis_info.get('connected_clients', 'N/A')}")
            print(f"  Uptime: {redis_info.get('uptime_days', 'N/A')} days")
    else:
        print("Failed to get cache statistics")


def run_performance_benchmark(token: str):
    """Run a comprehensive performance benchmark."""
    print("\n⚡ Performance Benchmark")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test message
    message = "What are the ticket prices?"
    
    # Warm up cache
    requests.post(
        f"{BASE_URL}/chat",
        json={"message": message, "use_cache": True},
        headers=headers
    )
    
    # Benchmark without cache
    print("\n❌ Without Cache (use_cache=False):")
    no_cache_times = []
    for i in range(5):
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": f"{message} {i}", "use_cache": False},
            headers=headers
        )
        elapsed = (time.time() - start_time) * 1000
        no_cache_times.append(elapsed)
        print(f"  Request {i+1}: {elapsed:.2f}ms")
    
    # Benchmark with cache
    print("\n✅ With Cache (use_cache=True):")
    cache_times = []
    for i in range(5):
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message, "use_cache": True},
            headers=headers
        )
        elapsed = (time.time() - start_time) * 1000
        cache_times.append(elapsed)
        print(f"  Request {i+1}: {elapsed:.2f}ms")
    
    # Statistics
    print("\n📈 Performance Summary:")
    print(f"  Without Cache:")
    print(f"    Average: {statistics.mean(no_cache_times):.2f}ms")
    print(f"    Median:  {statistics.median(no_cache_times):.2f}ms")
    print(f"    Min:     {min(no_cache_times):.2f}ms")
    print(f"    Max:     {max(no_cache_times):.2f}ms")
    
    print(f"  With Cache:")
    print(f"    Average: {statistics.mean(cache_times):.2f}ms")
    print(f"    Median:  {statistics.median(cache_times):.2f}ms")
    print(f"    Min:     {min(cache_times):.2f}ms")
    print(f"    Max:     {max(cache_times):.2f}ms")
    
    avg_speedup = statistics.mean(no_cache_times) / statistics.mean(cache_times)
    print(f"\n  🚀 Average Speedup: {avg_speedup:.1f}x faster with cache!")


if __name__ == "__main__":
    import sys
    
    print("🚀 Redis Caching Performance Test")
    print("\nMake sure both Redis and the API server are running:")
    print("  1. Start Redis: redis-server")
    print("  2. Start API: python3 api/main_cached.py")
    print("\nPress Enter to start tests...")
    input()
    
    try:
        # Login
        print("Logging in...")
        token = login_user()
        print("✅ Logged in successfully")
        
        # Run tests
        test_chat_caching(token)
        test_knowledge_base_caching(token)
        test_embedding_caching(token)
        test_computation_caching(token)
        run_performance_benchmark(token)
        test_cache_statistics(token)
        
        print("\n" + "=" * 50)
        print("✅ All cache tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server at", BASE_URL)
        print("Make sure the server is running first!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
