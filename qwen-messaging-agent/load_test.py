import asyncio
import aiohttp
import time


async def send_request(session, url: str, payload: dict):
    async with session.post(url, json=payload) as response:
        return await response.json(), response.status


async def load_test(url: str, num_requests: int, concurrent: int = 10):
    results = {"total": num_requests, "successful": 0, "failed": 0, "latencies": []}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(num_requests):
            payload = {"message": f"Test message {i}", "conversation_id": f"test-{i % concurrent}"}
            start = time.time()
            tasks.append(send_request(session, url, payload))
            if len(tasks) >= concurrent:
                responses = await asyncio.gather(*tasks)
                for _body, status in responses:
                    latency = time.time() - start
                    results["latencies"].append(latency)
                    if status == 200:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                tasks = []
        if tasks:
            responses = await asyncio.gather(*tasks)
            for _body, status in responses:
                if status == 200:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
    latencies = results["latencies"] or [0]
    results["avg_latency"] = sum(latencies) / len(latencies)
    latencies_sorted = sorted(latencies)
    results["p95_latency"] = latencies_sorted[int(len(latencies_sorted) * 0.95) - 1]
    results["p99_latency"] = latencies_sorted[int(len(latencies_sorted) * 0.99) - 1]
    return results


if __name__ == "__main__":
    results = asyncio.run(load_test(url="http://localhost:8080/chat", num_requests=100, concurrent=20))
    print(results)
