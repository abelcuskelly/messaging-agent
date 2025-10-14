"""
Ticket Platform Integrations

Integrations with major ticket marketplaces:
- StubHub
- SeatGeek  
- Ticketmaster

Usage:
    from integrations.ticket_platforms import UnifiedInventoryAggregator
    
    aggregator = UnifiedInventoryAggregator()
    results = await aggregator.search_events("Lakers", city="Los Angeles")
"""

from integrations.ticket_platforms.stubhub_api import StubHubAPI
from integrations.ticket_platforms.seatgeek_api import SeatGeekAPI
from integrations.ticket_platforms.ticketmaster_api import TicketmasterAPI
from integrations.ticket_platforms.unified_inventory import UnifiedInventoryAggregator

__all__ = [
    'StubHubAPI',
    'SeatGeekAPI',
    'TicketmasterAPI',
    'UnifiedInventoryAggregator'
]

__version__ = '1.0.0'
