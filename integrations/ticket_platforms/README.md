# Ticket Platform Integrations

Real-time ticket inventory integration with StubHub, SeatGeek, and Ticketmaster.

## 🎯 Overview

This module provides unified access to major ticket marketplaces, enabling your messaging agent to:
- Search real-time inventory across 3 platforms
- Compare prices and find best deals
- Aggregate availability data
- Provide comprehensive event information

## 📦 Platforms Supported

### 1. StubHub
- **API**: https://developer.stubhub.com/
- **Coverage**: Secondary market, resale tickets
- **Features**: Real-time pricing, section details, delivery options
- **Authentication**: OAuth 2.0

### 2. SeatGeek
- **API**: https://platform.seatgeek.com/
- **Coverage**: Primary + secondary market
- **Features**: Recommendations, popularity scores, venue details
- **Authentication**: Client ID

### 3. Ticketmaster
- **API**: https://developer.ticketmaster.com/
- **Coverage**: Primary market, official tickets
- **Features**: Event discovery, venue search, classifications
- **Authentication**: API Key

## 🚀 Quick Start

### 1. Get API Credentials

**StubHub:**
1. Sign up at https://developer.stubhub.com/
2. Create an application
3. Get API key and secret

**SeatGeek:**
1. Sign up at https://platform.seatgeek.com/
2. Create an application
3. Get client ID

**Ticketmaster:**
1. Sign up at https://developer.ticketmaster.com/
2. Create an application
3. Get API key

### 2. Set Environment Variables

```bash
# StubHub
export STUBHUB_API_KEY=your-stubhub-key
export STUBHUB_API_SECRET=your-stubhub-secret
export STUBHUB_ENV=production  # or 'sandbox' for testing

# SeatGeek
export SEATGEEK_CLIENT_ID=your-seatgeek-client-id
export SEATGEEK_CLIENT_SECRET=your-seatgeek-secret  # optional

# Ticketmaster
export TICKETMASTER_API_KEY=your-ticketmaster-key
```

### 3. Use the Unified Aggregator

```python
from integrations.ticket_platforms import UnifiedInventoryAggregator

# Initialize aggregator
aggregator = UnifiedInventoryAggregator()

# Search across all platforms
results = await aggregator.search_events(
    query="Lakers",
    city="Los Angeles"
)

print(f"Found {results['total_events']} events")
print(f"Searched {results['platforms_queried']} platforms")

# Get best deals
for event in results['events']:
    print(f"{event['name']}: ${event['best_min_price']}")
    print(f"Available on: {', '.join([p['platform'] for p in event['platforms']])}")
```

## 📚 Usage Examples

### Example 1: Search Events

```python
from integrations.ticket_platforms import UnifiedInventoryAggregator

aggregator = UnifiedInventoryAggregator()

# Search for Lakers games
results = await aggregator.search_events(
    query="Lakers",
    city="Los Angeles",
    date_from="2025-10-15",
    date_to="2025-10-31"
)

# Results include:
# - Events from all 3 platforms
# - Deduplicated by name/venue/date
# - Price comparison across platforms
# - Total listings available
```

### Example 2: Price Comparison

```python
# Compare prices for specific event
comparison = aggregator.compare_prices(
    event_name="Lakers vs Warriors",
    venue="Crypto.com Arena",
    date="2025-10-20"
)

print(f"Cheapest: ${comparison['price_comparison']['cheapest_price']}")
print(f"Most expensive: ${comparison['price_comparison']['most_expensive_price']}")
print(f"Savings: ${comparison['price_comparison']['potential_savings']}")
print(f"Buy from: {comparison['price_comparison']['best_platform']}")
```

### Example 3: Find Best Deals

```python
# Find best deals under $150
results = await aggregator.search_events("Lakers")
deals = aggregator.find_best_deals(
    results['events'],
    max_price=150,
    min_tickets=2
)

for deal in deals[:5]:
    print(f"{deal['name']}: ${deal['best_min_price']}")
    print(f"Value score: {deal['value_score']:.2f}")
```

### Example 4: Individual Platform Access

```python
from integrations.ticket_platforms import SeatGeekAPI, TicketmasterAPI

# Use specific platform
seatgeek = SeatGeekAPI()
events = seatgeek.search_events("Lakers", city="Los Angeles")

ticketmaster = TicketmasterAPI()
events = ticketmaster.search_events(keyword="Lakers", city="Los Angeles")
```

## 🔧 Integration with Agent Tools

Update your agent tools to use real inventory:

```python
from integrations.ticket_platforms import UnifiedInventoryAggregator

aggregator = UnifiedInventoryAggregator()

@registry.register(
    name="check_inventory",
    description="Check ticket availability across all platforms",
    parameters={...}
)
def check_inventory(event_name: str, quantity: int) -> Dict[str, Any]:
    # Search across all platforms
    results = asyncio.run(aggregator.search_events(event_name))
    
    # Filter by quantity
    available = [
        e for e in results['events']
        if e['total_listings'] >= quantity
    ]
    
    return {
        "available_events": available,
        "total_platforms": results['platforms_queried'],
        "best_price": min([e['best_min_price'] for e in available]) if available else None
    }
```

## 📊 Data Format

### Normalized Event Format

All platforms return events in this unified format:

```python
{
    "platform": "stubhub" | "seatgeek" | "ticketmaster",
    "event_id": "12345",
    "name": "Lakers vs Warriors",
    "venue": "Crypto.com Arena",
    "city": "Los Angeles",
    "state": "CA",
    "date": "2025-10-20",
    "time": "19:00:00",
    "min_price": 85.00,
    "max_price": 500.00,
    "average_price": 180.00,  # SeatGeek only
    "available_tickets": 150,
    "url": "https://...",
    "image_url": "https://..."
}
```

### Aggregated Results Format

```python
{
    "events": [
        {
            "name": "Lakers vs Warriors",
            "venue": "Crypto.com Arena",
            "date": "2025-10-20",
            "platforms": [
                {
                    "platform": "stubhub",
                    "min_price": 95.00,
                    "available_tickets": 50
                },
                {
                    "platform": "seatgeek",
                    "min_price": 85.00,
                    "available_tickets": 75
                },
                {
                    "platform": "ticketmaster",
                    "min_price": 120.00,
                    "available_tickets": 25
                }
            ],
            "best_min_price": 85.00,  # Cheapest across all
            "total_listings": 150,
            "platforms_available": 3
        }
    ],
    "total_events": 1,
    "platforms_queried": 3
}
```

## ⚡ Performance

### Parallel Querying
- **Sequential**: 3 platforms × 500ms = 1500ms
- **Parallel**: max(500ms, 500ms, 500ms) = 500ms
- **Speedup**: **3x faster**

### Caching Strategy
```python
# Cache event searches for 5 minutes
# Cache price comparisons for 2 minutes
# Cache venue data for 1 hour
```

## 🔒 Security

### API Key Management
- Store credentials in environment variables
- Never commit keys to git
- Use Google Secret Manager in production
- Rotate keys regularly

### Rate Limiting
Each platform has rate limits:
- **StubHub**: 5000 requests/day
- **SeatGeek**: 5000 requests/day (free tier)
- **Ticketmaster**: 5000 requests/day

The aggregator respects these limits and implements:
- Request queuing
- Exponential backoff
- Automatic retries

## 🧪 Testing

### Test Individual Platforms

```bash
# Test StubHub
python integrations/ticket_platforms/stubhub_api.py

# Test SeatGeek
python integrations/ticket_platforms/seatgeek_api.py

# Test Ticketmaster
python integrations/ticket_platforms/ticketmaster_api.py
```

### Test Unified Aggregator

```bash
# Test aggregation
python integrations/ticket_platforms/unified_inventory.py
```

### Test with Agent

```python
from agent.tools_with_platforms import search_tickets

# Search across all platforms
results = search_tickets(
    query="Lakers",
    city="Los Angeles"
)

print(f"Found {results['total_events']} events")
print(f"Best deal: ${results['best_deals'][0]['best_min_price']}")
```

## 📈 Business Value

### Price Comparison
- Show customers best prices across platforms
- Increase conversion by offering cheapest options
- Build trust with transparent pricing

### Inventory Aggregation
- 3x more inventory than single platform
- Higher availability = more sales
- Reduce "sold out" scenarios

### Revenue Optimization
- Commission from platform referrals
- Upsell based on availability
- Dynamic pricing insights

## 🚨 Error Handling

All integrations include:
- ✅ Automatic retries (3 attempts)
- ✅ Exponential backoff
- ✅ Graceful degradation (if one platform fails, others continue)
- ✅ Detailed error logging
- ✅ Timeout protection (10 seconds)

```python
# If StubHub fails, still get SeatGeek and Ticketmaster results
results = await aggregator.search_events("Lakers")
# Returns results from available platforms
```

## 🔄 Migration from Mock Data

### Before (Mock Data)
```python
def check_inventory(event_id: str, quantity: int):
    # Returns fake data
    return {"seats": [{"id": "A-1", "price": 120}]}
```

### After (Real Data)
```python
def check_inventory(event_name: str, quantity: int):
    # Returns real data from 3 platforms
    results = search_tickets(query=event_name)
    return results['best_deals']
```

## 📝 TODO: Production Enhancements

- [ ] Add caching layer (Redis) for API responses
- [ ] Implement webhook listeners for price changes
- [ ] Add seat map visualization
- [ ] Implement purchase flow integration
- [ ] Add analytics tracking
- [ ] Set up monitoring for API health
- [ ] Implement fallback strategies
- [ ] Add A/B testing for platform preference

## 📖 API Documentation

### StubHub API
- Docs: https://developer.stubhub.com/store/site/pages/doc-viewer.jag
- Rate Limits: 5000 req/day
- Sandbox: Available for testing

### SeatGeek API
- Docs: https://platform.seatgeek.com/
- Rate Limits: 5000 req/day (free), unlimited (paid)
- No sandbox, but free tier available

### Ticketmaster API
- Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
- Rate Limits: 5000 req/day (free), higher tiers available
- Extensive documentation and examples

## 🤝 Contributing

When adding new platforms:
1. Create new file: `platform_name_api.py`
2. Implement search and inventory methods
3. Use common normalized format
4. Add to UnifiedInventoryAggregator
5. Update this README
6. Add tests

## 📄 License

See main project LICENSE file.
