"""
Ticketmaster API Integration

Official API: https://developer.ticketmaster.com/
Documentation: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

Features:
- Event discovery
- Venue search
- Attraction details
- Classification (genre, segment, type)
- Image assets
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class TicketmasterAPI:
    """
    Ticketmaster Discovery API client
    
    Authentication:
    - Requires Ticketmaster API key
    - Simple API key in query params
    
    Environment Variables:
    - TICKETMASTER_API_KEY: Your API key (required)
    """
    
    def __init__(self):
        self.api_key = os.getenv('TICKETMASTER_API_KEY')
        self.base_url = 'https://app.ticketmaster.com/discovery/v2'
        
        if not self.api_key:
            logger.warning("Ticketmaster API key not configured")
    
    def _get_params(self, additional_params: Dict = None) -> Dict[str, Any]:
        """Get request parameters with authentication"""
        params = {}
        
        if self.api_key:
            params['apikey'] = self.api_key
        
        if additional_params:
            params.update(additional_params)
        
        return params
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_events(self,
                     keyword: Optional[str] = None,
                     city: Optional[str] = None,
                     state_code: Optional[str] = None,
                     postal_code: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     classification_name: Optional[str] = None,
                     size: int = 20) -> List[Dict[str, Any]]:
        """
        Search for events on Ticketmaster
        
        Args:
            keyword: Search keyword (artist, team, event)
            city: City name
            state_code: State code (e.g., 'CA', 'NY')
            postal_code: ZIP/postal code
            start_date: Start date (YYYY-MM-DDTHH:mm:ssZ)
            end_date: End date (YYYY-MM-DDTHH:mm:ssZ)
            classification_name: Sports, Music, Arts, etc.
            size: Number of results (max 200)
        
        Returns:
            List of events with details
        """
        try:
            url = f"{self.base_url}/events.json"
            
            params = self._get_params({
                'size': size
            })
            
            if keyword:
                params['keyword'] = keyword
            if city:
                params['city'] = city
            if state_code:
                params['stateCode'] = state_code
            if postal_code:
                params['postalCode'] = postal_code
            if start_date:
                params['startDateTime'] = start_date
            if end_date:
                params['endDateTime'] = end_date
            if classification_name:
                params['classificationName'] = classification_name
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('_embedded', {}).get('events', [])
                
                logger.info(f"Found {len(events)} events on Ticketmaster for '{keyword}'")
                return self._normalize_events(events)
            else:
                logger.error(f"Ticketmaster search failed: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Ticketmaster search error: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_event_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific event
        
        Args:
            event_id: Ticketmaster event ID
        
        Returns:
            Event details with pricing and availability
        """
        try:
            url = f"{self.base_url}/events/{event_id}.json"
            params = self._get_params()
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                event = response.json()
                logger.info(f"Retrieved event details for {event_id}")
                return self._normalize_event(event)
            else:
                logger.error(f"Ticketmaster event details failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Ticketmaster event details error: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_venues(self,
                     keyword: Optional[str] = None,
                     city: Optional[str] = None,
                     state_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for venues
        
        Args:
            keyword: Venue name
            city: City name
            state_code: State code
        
        Returns:
            List of venues
        """
        try:
            url = f"{self.base_url}/venues.json"
            
            params = self._get_params()
            
            if keyword:
                params['keyword'] = keyword
            if city:
                params['city'] = city
            if state_code:
                params['stateCode'] = state_code
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                venues = data.get('_embedded', {}).get('venues', [])
                
                logger.info(f"Found {len(venues)} venues on Ticketmaster")
                return self._normalize_venues(venues)
            else:
                logger.error(f"Ticketmaster venue search failed: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Ticketmaster venue search error: {e}")
            return []
    
    def _normalize_event(self, event: Dict) -> Dict[str, Any]:
        """Normalize event to common format"""
        # Extract price range
        price_ranges = event.get('priceRanges', [{}])
        min_price = price_ranges[0].get('min') if price_ranges else None
        max_price = price_ranges[0].get('max') if price_ranges else None
        currency = price_ranges[0].get('currency', 'USD') if price_ranges else 'USD'
        
        # Extract venue info
        venues = event.get('_embedded', {}).get('venues', [{}])
        venue = venues[0] if venues else {}
        
        # Extract dates
        dates = event.get('dates', {})
        start = dates.get('start', {})
        
        # Extract classifications
        classifications = event.get('classifications', [{}])
        classification = classifications[0] if classifications else {}
        
        return {
            "platform": "ticketmaster",
            "event_id": event.get('id'),
            "name": event.get('name'),
            "url": event.get('url'),
            "venue": venue.get('name'),
            "venue_id": venue.get('id'),
            "city": venue.get('city', {}).get('name'),
            "state": venue.get('state', {}).get('stateCode'),
            "country": venue.get('country', {}).get('countryCode'),
            "address": venue.get('address', {}).get('line1'),
            "postal_code": venue.get('postalCode'),
            "date": start.get('localDate'),
            "time": start.get('localTime'),
            "date_time": start.get('dateTime'),
            "timezone": start.get('timezone'),
            "time_tbd": start.get('timeTBA', False),
            "date_tbd": start.get('dateTBA', False),
            "category": classification.get('segment', {}).get('name'),
            "genre": classification.get('genre', {}).get('name'),
            "sub_genre": classification.get('subGenre', {}).get('name'),
            "type": classification.get('type', {}).get('name'),
            "sub_type": classification.get('subType', {}).get('name'),
            "min_price": min_price,
            "max_price": max_price,
            "currency": currency,
            "status": event.get('dates', {}).get('status', {}).get('code'),
            "sales_public_start": dates.get('public', {}).get('startDateTime'),
            "sales_public_end": dates.get('public', {}).get('endDateTime'),
            "image_url": event.get('images', [{}])[0].get('url') if event.get('images') else None,
            "promoter": event.get('promoter', {}).get('name'),
            "info": event.get('info'),
            "please_note": event.get('pleaseNote')
        }
    
    def _normalize_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize multiple events to common format"""
        return [self._normalize_event(event) for event in events]
    
    def _normalize_venues(self, venues: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize venues to common format"""
        normalized = []
        
        for venue in venues:
            normalized.append({
                "platform": "ticketmaster",
                "venue_id": venue.get('id'),
                "name": venue.get('name'),
                "city": venue.get('city', {}).get('name'),
                "state": venue.get('state', {}).get('stateCode'),
                "country": venue.get('country', {}).get('countryCode'),
                "address": venue.get('address', {}).get('line1'),
                "postal_code": venue.get('postalCode'),
                "timezone": venue.get('timezone'),
                "url": venue.get('url'),
                "image_url": venue.get('images', [{}])[0].get('url') if venue.get('images') else None
            })
        
        return normalized


# Example usage
if __name__ == "__main__":
    # Test the integration
    ticketmaster = TicketmasterAPI()
    
    # Search for Lakers games
    events = ticketmaster.search_events(
        keyword="Lakers",
        city="Los Angeles",
        classification_name="Sports"
    )
    
    if events:
        print(f"Found {len(events)} Lakers events on Ticketmaster")
        for event in events[:3]:
            print(f"\n  📅 {event['name']}")
            print(f"     🏟️  {event['venue']}")
            print(f"     📍 {event['city']}, {event['state']}")
            print(f"     🕐 {event['date']} at {event['time']}")
            if event['min_price']:
                print(f"     💰 ${event['min_price']} - ${event['max_price']} {event['currency']}")
            print(f"     🎫 Status: {event['status']}")
        
        # Get recommendations
        if events:
            recs = ticketmaster.get_recommendations(events[0]['event_id'])
            if recs:
                print(f"\n🎯 Recommended events: {len(recs)}")
    else:
        print("No events found (API key may not be configured)")
