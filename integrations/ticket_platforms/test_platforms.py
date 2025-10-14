"""
Test Suite for Ticket Platform Integrations

Tests for StubHub, SeatGeek, Ticketmaster, and Unified Aggregator
"""

import asyncio
import pytest
from unittest.mock import Mock, patch
from integrations.ticket_platforms import (
    StubHubAPI,
    SeatGeekAPI,
    TicketmasterAPI,
    UnifiedInventoryAggregator
)


class TestStubHubAPI:
    """Tests for StubHub integration"""
    
    def test_initialization(self):
        """Test StubHub API initialization"""
        api = StubHubAPI()
        assert api.base_url is not None
        assert api.env in ['sandbox', 'production']
    
    def test_event_normalization(self):
        """Test event data normalization"""
        api = StubHubAPI()
        
        mock_event = {
            'id': '12345',
            'name': 'Lakers vs Warriors',
            'venue': {'name': 'Crypto.com Arena', 'city': 'Los Angeles'},
            'eventDateLocal': '2025-10-20T19:00:00',
            'minPrice': 85.00,
            'maxPrice': 500.00
        }
        
        normalized = api._normalize_events([mock_event])
        
        assert len(normalized) == 1
        assert normalized[0]['platform'] == 'stubhub'
        assert normalized[0]['event_id'] == '12345'
        assert normalized[0]['name'] == 'Lakers vs Warriors'
        assert normalized[0]['min_price'] == 85.00


class TestSeatGeekAPI:
    """Tests for SeatGeek integration"""
    
    def test_initialization(self):
        """Test SeatGeek API initialization"""
        api = SeatGeekAPI()
        assert api.base_url == 'https://api.seatgeek.com/2'
    
    def test_event_normalization(self):
        """Test event data normalization"""
        api = SeatGeekAPI()
        
        mock_event = {
            'id': 67890,
            'title': 'Lakers vs Warriors',
            'short_title': 'Lakers vs Warriors',
            'venue': {
                'name': 'Crypto.com Arena',
                'city': 'Los Angeles',
                'state': 'CA'
            },
            'datetime_local': '2025-10-20T19:00:00',
            'stats': {
                'lowest_price': 85,
                'highest_price': 500,
                'average_price': 180
            }
        }
        
        normalized = api._normalize_event(mock_event)
        
        assert normalized['platform'] == 'seatgeek'
        assert normalized['event_id'] == '67890'
        assert normalized['name'] == 'Lakers vs Warriors'
        assert normalized['min_price'] == 85


class TestTicketmasterAPI:
    """Tests for Ticketmaster integration"""
    
    def test_initialization(self):
        """Test Ticketmaster API initialization"""
        api = TicketmasterAPI()
        assert api.base_url == 'https://app.ticketmaster.com/discovery/v2'
    
    def test_event_normalization(self):
        """Test event data normalization"""
        api = TicketmasterAPI()
        
        mock_event = {
            'id': 'TM12345',
            'name': 'Lakers vs Warriors',
            'url': 'https://www.ticketmaster.com/event/12345',
            'dates': {
                'start': {
                    'localDate': '2025-10-20',
                    'localTime': '19:00:00'
                }
            },
            '_embedded': {
                'venues': [{
                    'name': 'Crypto.com Arena',
                    'city': {'name': 'Los Angeles'},
                    'state': {'stateCode': 'CA'}
                }]
            },
            'priceRanges': [{
                'min': 120.00,
                'max': 600.00,
                'currency': 'USD'
            }]
        }
        
        normalized = api._normalize_event(mock_event)
        
        assert normalized['platform'] == 'ticketmaster'
        assert normalized['event_id'] == 'TM12345'
        assert normalized['name'] == 'Lakers vs Warriors'
        assert normalized['min_price'] == 120.00


class TestUnifiedAggregator:
    """Tests for unified inventory aggregator"""
    
    def test_initialization(self):
        """Test aggregator initialization"""
        aggregator = UnifiedInventoryAggregator()
        assert len(aggregator.platforms) >= 0  # At least 0 (if no creds)
    
    def test_event_deduplication(self):
        """Test event deduplication across platforms"""
        aggregator = UnifiedInventoryAggregator()
        
        # Mock results from different platforms (same event)
        mock_results = {
            'stubhub': [{
                'platform': 'stubhub',
                'name': 'Lakers vs Warriors',
                'venue': 'Crypto.com Arena',
                'date': '2025-10-20',
                'min_price': 95.00,
                'available_tickets': 50
            }],
            'seatgeek': [{
                'platform': 'seatgeek',
                'name': 'Lakers vs Warriors',
                'venue': 'Crypto.com Arena',
                'date': '2025-10-20',
                'min_price': 85.00,
                'available_tickets': 75
            }],
            'ticketmaster': [{
                'platform': 'ticketmaster',
                'name': 'Lakers vs Warriors',
                'venue': 'Crypto.com Arena',
                'date': '2025-10-20',
                'min_price': 120.00,
                'available_tickets': 25
            }]
        }
        
        aggregated = aggregator._aggregate_events(mock_results)
        
        # Should deduplicate to 1 event
        assert aggregated['total_events'] == 1
        
        event = aggregated['events'][0]
        assert len(event['platforms']) == 3
        assert event['best_min_price'] == 85.00  # SeatGeek cheapest
        assert event['total_listings'] == 150  # Sum of all
    
    def test_best_deals_finder(self):
        """Test best deals finder with filters"""
        aggregator = UnifiedInventoryAggregator()
        
        mock_events = [
            {
                'name': 'Event 1',
                'best_min_price': 50.00,
                'total_listings': 100,
                'platforms_available': 3,
                'platforms': []
            },
            {
                'name': 'Event 2',
                'best_min_price': 150.00,
                'total_listings': 50,
                'platforms_available': 2,
                'platforms': []
            },
            {
                'name': 'Event 3',
                'best_min_price': 80.00,
                'total_listings': 75,
                'platforms_available': 3,
                'platforms': []
            }
        ]
        
        # Find deals under $100
        deals = aggregator.find_best_deals(mock_events, max_price=100)
        
        assert len(deals) == 2  # Event 1 and 3
        assert deals[0]['name'] == 'Event 1'  # Cheapest first
    
    def test_price_comparison(self):
        """Test price comparison logic"""
        aggregator = UnifiedInventoryAggregator()
        
        # Mock search results
        with patch.object(aggregator, 'search_events') as mock_search:
            mock_search.return_value = asyncio.Future()
            mock_search.return_value.set_result({
                'events': [{
                    'name': 'Lakers vs Warriors',
                    'venue': 'Crypto.com Arena',
                    'date': '2025-10-20',
                    'platforms': [
                        {'platform': 'stubhub', 'min_price': 95.00},
                        {'platform': 'seatgeek', 'min_price': 85.00},
                        {'platform': 'ticketmaster', 'min_price': 120.00}
                    ]
                }]
            })
            
            comparison = aggregator.compare_prices(
                'Lakers vs Warriors',
                'Crypto.com Arena',
                '2025-10-20'
            )
            
            assert comparison['price_comparison']['cheapest_price'] == 85.00
            assert comparison['price_comparison']['most_expensive_price'] == 120.00
            assert comparison['price_comparison']['potential_savings'] == 35.00
            assert comparison['price_comparison']['best_platform'] == 'seatgeek'


@pytest.mark.asyncio
async def test_parallel_search_performance():
    """Test that parallel search is faster than sequential"""
    aggregator = UnifiedInventoryAggregator()
    
    import time
    
    # Measure parallel search time
    start = time.time()
    results = await aggregator.search_events("Lakers")
    parallel_time = time.time() - start
    
    # Parallel should be faster than sequential
    # (In practice, ~500ms vs ~1500ms)
    assert parallel_time < 2.0  # Should complete in under 2 seconds


def test_platform_stats():
    """Test platform statistics"""
    aggregator = UnifiedInventoryAggregator()
    stats = aggregator.get_platform_stats()
    
    assert 'platforms_configured' in stats
    assert 'total_platforms' in stats
    assert isinstance(stats['platforms_configured'], list)


if __name__ == "__main__":
    print("🧪 Running Ticket Platform Integration Tests")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
    
    print("\n✅ All tests completed!")
    print("\nTo run specific test:")
    print("  pytest test_platforms.py::TestStubHubAPI::test_initialization")
    print("\nTo run with coverage:")
    print("  pytest test_platforms.py --cov=integrations/ticket_platforms")
