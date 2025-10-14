"""
StubHub API Integration

Official API: https://developer.stubhub.com/
Documentation: https://developer.stubhub.com/store/site/pages/doc-viewer.jag

Features:
- Event search and discovery
- Inventory and pricing
- Real-time availability
- Section and row details
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class StubHubAPI:
    """
    StubHub API client for ticket inventory
    
    Authentication:
    - Requires StubHub API credentials
    - OAuth 2.0 application token
    
    Environment Variables:
    - STUBHUB_API_KEY: Your application key
    - STUBHUB_API_SECRET: Your application secret
    - STUBHUB_ENV: 'sandbox' or 'production'
    """
    
    def __init__(self):
        self.api_key = os.getenv('STUBHUB_API_KEY')
        self.api_secret = os.getenv('STUBHUB_API_SECRET')
        self.env = os.getenv('STUBHUB_ENV', 'production')
        
        # API endpoints
        if self.env == 'sandbox':
            self.base_url = 'https://api.stubhubsandbox.com'
        else:
            self.base_url = 'https://api.stubhub.com'
        
        self.token = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with StubHub API"""
        if not self.api_key or not self.api_secret:
            logger.warning("StubHub credentials not configured")
            return
        
        try:
            auth_url = f"{self.base_url}/login"
            response = requests.post(
                auth_url,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret,
                    'scope': 'PRODUCTION'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                logger.info("StubHub authentication successful")
            else:
                logger.error(f"StubHub auth failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"StubHub authentication error: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        return headers
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_events(self, 
                     query: str,
                     city: Optional[str] = None,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for events on StubHub
        
        Args:
            query: Search query (team name, performer, etc.)
            city: City name
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        
        Returns:
            List of events with details
        """
        try:
            url = f"{self.base_url}/search/catalog/events/v3"
            
            params = {
                'q': query,
                'minAvailableTickets': 1
            }
            
            if city:
                params['city'] = city
            if date_from:
                params['minDate'] = date_from
            if date_to:
                params['maxDate'] = date_to
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                logger.info(f"Found {len(events)} events on StubHub for '{query}'")
                return self._normalize_events(events)
            else:
                logger.error(f"StubHub search failed: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"StubHub search error: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_event_inventory(self, event_id: str) -> Dict[str, Any]:
        """
        Get ticket inventory for a specific event
        
        Args:
            event_id: StubHub event ID
        
        Returns:
            Inventory data with sections, rows, and pricing
        """
        try:
            url = f"{self.base_url}/search/inventory/v2"
            
            params = {
                'eventId': event_id,
                'quantity': 1
            }
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                listings = data.get('listing', [])
                
                logger.info(f"Found {len(listings)} listings for event {event_id}")
                return self._normalize_inventory(listings)
            else:
                logger.error(f"StubHub inventory failed: {response.status_code}")
                return {"listings": [], "total_count": 0}
        
        except Exception as e:
            logger.error(f"StubHub inventory error: {e}")
            return {"listings": [], "total_count": 0}
    
    def _normalize_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize event data to common format"""
        normalized = []
        
        for event in events:
            normalized.append({
                "platform": "stubhub",
                "event_id": str(event.get('id')),
                "name": event.get('name'),
                "venue": event.get('venue', {}).get('name'),
                "city": event.get('venue', {}).get('city'),
                "date": event.get('eventDateLocal'),
                "time": event.get('eventDateLocal'),
                "category": event.get('categories', [{}])[0].get('name') if event.get('categories') else None,
                "min_price": event.get('minPrice'),
                "max_price": event.get('maxPrice'),
                "available_tickets": event.get('ticketInfo', {}).get('totalTickets', 0)
            })
        
        return normalized
    
    def _normalize_inventory(self, listings: List[Dict]) -> Dict[str, Any]:
        """Normalize inventory data to common format"""
        normalized_listings = []
        
        for listing in listings:
            normalized_listings.append({
                "platform": "stubhub",
                "listing_id": str(listing.get('listingId')),
                "section": listing.get('sectionName'),
                "row": listing.get('row'),
                "quantity": listing.get('quantity'),
                "price_per_ticket": listing.get('currentPrice', {}).get('amount'),
                "currency": listing.get('currentPrice', {}).get('currency', 'USD'),
                "total_price": listing.get('currentPrice', {}).get('amount', 0) * listing.get('quantity', 1),
                "seat_numbers": listing.get('seatNumbers'),
                "delivery_type": listing.get('deliveryTypeList', [{}])[0].get('name'),
                "zone": listing.get('zoneId'),
                "splits": listing.get('splitOption')
            })
        
        return {
            "platform": "stubhub",
            "listings": normalized_listings,
            "total_count": len(normalized_listings),
            "min_price": min([l['price_per_ticket'] for l in normalized_listings]) if normalized_listings else None,
            "max_price": max([l['price_per_ticket'] for l in normalized_listings]) if normalized_listings else None
        }


# Example usage
if __name__ == "__main__":
    # Test the integration
    stubhub = StubHubAPI()
    
    # Search for Lakers games
    events = stubhub.search_events("Lakers", city="Los Angeles")
    
    if events:
        print(f"Found {len(events)} Lakers events")
        for event in events[:3]:
            print(f"  - {event['name']} on {event['date']}")
            print(f"    Price range: ${event['min_price']} - ${event['max_price']}")
        
        # Get inventory for first event
        if events:
            inventory = stubhub.get_event_inventory(events[0]['event_id'])
            print(f"\nInventory: {inventory['total_count']} listings available")
    else:
        print("No events found (credentials may not be configured)")
