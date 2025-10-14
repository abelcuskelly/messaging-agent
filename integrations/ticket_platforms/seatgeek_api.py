"""
SeatGeek API Integration

Official API: https://platform.seatgeek.com/
Documentation: https://platform.seatgeek.com/#events

Features:
- Event search with autocomplete
- Venue information
- Performer details
- Real-time pricing
- Recommendation engine
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class SeatGeekAPI:
    """
    SeatGeek API client for ticket inventory
    
    Authentication:
    - Requires SeatGeek client ID
    - Simple API key authentication
    
    Environment Variables:
    - SEATGEEK_CLIENT_ID: Your client ID
    - SEATGEEK_CLIENT_SECRET: Your client secret (optional)
    """
    
    def __init__(self):
        self.client_id = os.getenv('SEATGEEK_CLIENT_ID')
        self.client_secret = os.getenv('SEATGEEK_CLIENT_SECRET')
        self.base_url = 'https://api.seatgeek.com/2'
    
    def _get_params(self, additional_params: Dict = None) -> Dict[str, Any]:
        """Get request parameters with authentication"""
        params = {}
        
        if self.client_id:
            params['client_id'] = self.client_id
        
        if self.client_secret:
            params['client_secret'] = self.client_secret
        
        if additional_params:
            params.update(additional_params)
        
        return params
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_events(self,
                     query: str,
                     venue: Optional[str] = None,
                     city: Optional[str] = None,
                     state: Optional[str] = None,
                     date_from: Optional[str] = None,
                     date_to: Optional[str] = None,
                     per_page: int = 25) -> List[Dict[str, Any]]:
        """
        Search for events on SeatGeek
        
        Args:
            query: Search query (team, performer, event name)
            venue: Venue name
            city: City name
            state: State code (e.g., 'CA', 'NY')
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            per_page: Results per page (max 100)
        
        Returns:
            List of events with details
        """
        try:
            url = f"{self.base_url}/events"
            
            params = self._get_params({
                'q': query,
                'per_page': per_page
            })
            
            if venue:
                params['venue.name'] = venue
            if city:
                params['venue.city'] = city
            if state:
                params['venue.state'] = state
            if date_from:
                params['datetime_local.gte'] = date_from
            if date_to:
                params['datetime_local.lte'] = date_to
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                logger.info(f"Found {len(events)} events on SeatGeek for '{query}'")
                return self._normalize_events(events)
            else:
                logger.error(f"SeatGeek search failed: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"SeatGeek search error: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_event_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific event
        
        Args:
            event_id: SeatGeek event ID
        
        Returns:
            Event details including stats and recommendations
        """
        try:
            url = f"{self.base_url}/events/{event_id}"
            params = self._get_params()
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                event = response.json()
                logger.info(f"Retrieved event details for {event_id}")
                return self._normalize_event(event)
            else:
                logger.error(f"SeatGeek event details failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"SeatGeek event details error: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_recommendations(self, 
                           event_id: str,
                           client_ip: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recommended events based on an event
        
        Args:
            event_id: SeatGeek event ID
            client_ip: Client IP for personalization
        
        Returns:
            List of recommended events
        """
        try:
            url = f"{self.base_url}/recommendations"
            
            params = self._get_params({
                'events.id': event_id
            })
            
            if client_ip:
                params['client_ip'] = client_ip
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                logger.info(f"Found {len(recommendations)} recommendations")
                return self._normalize_events(recommendations)
            else:
                logger.error(f"SeatGeek recommendations failed: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"SeatGeek recommendations error: {e}")
            return []
    
    def _normalize_event(self, event: Dict) -> Dict[str, Any]:
        """Normalize single event to common format"""
        return {
            "platform": "seatgeek",
            "event_id": str(event.get('id')),
            "name": event.get('title'),
            "short_name": event.get('short_title'),
            "venue": event.get('venue', {}).get('name'),
            "venue_id": str(event.get('venue', {}).get('id')),
            "city": event.get('venue', {}).get('city'),
            "state": event.get('venue', {}).get('state'),
            "address": event.get('venue', {}).get('address'),
            "postal_code": event.get('venue', {}).get('postal_code'),
            "date": event.get('datetime_local'),
            "date_utc": event.get('datetime_utc'),
            "time_tbd": event.get('time_tbd', False),
            "category": event.get('type'),
            "performers": [p.get('name') for p in event.get('performers', [])],
            "min_price": event.get('stats', {}).get('lowest_price'),
            "max_price": event.get('stats', {}).get('highest_price'),
            "average_price": event.get('stats', {}).get('average_price'),
            "median_price": event.get('stats', {}).get('median_price'),
            "available_tickets": event.get('stats', {}).get('listing_count', 0),
            "popularity": event.get('popularity', 0),
            "score": event.get('score', 0),
            "url": event.get('url'),
            "image_url": event.get('performers', [{}])[0].get('image') if event.get('performers') else None
        }
    
    def _normalize_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize multiple events to common format"""
        return [self._normalize_event(event) for event in events]


# Example usage
if __name__ == "__main__":
    # Test the integration
    seatgeek = SeatGeekAPI()
    
    # Search for Lakers games
    events = seatgeek.search_events("Lakers", city="Los Angeles")
    
    if events:
        print(f"Found {len(events)} Lakers events on SeatGeek")
        for event in events[:3]:
            print(f"\n  📅 {event['name']}")
            print(f"     🏟️  {event['venue']}")
            print(f"     📍 {event['city']}, {event['state']}")
            print(f"     💰 ${event['min_price']} - ${event['max_price']}")
            print(f"     🎫 {event['available_tickets']} listings")
        
        # Get detailed info for first event
        if events:
            details = seatgeek.get_event_details(events[0]['event_id'])
            if details:
                print(f"\n📊 Event Details:")
                print(f"   Popularity: {details['popularity']}")
                print(f"   Average price: ${details['average_price']}")
    else:
        print("No events found (credentials may not be configured)")
