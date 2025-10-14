"""
Agent Tools with Real Ticket Platform Integration

Updated tools that integrate with StubHub, SeatGeek, and Ticketmaster
for real-time ticket inventory and pricing.

Usage:
    from agent.tools_with_platforms import registry, get_unified_inventory
    
    # Search across all platforms
    results = get_unified_inventory("Lakers", city="Los Angeles")
"""

import json
import datetime
import asyncio
from typing import List, Dict, Any, Callable, Optional
import sys
sys.path.append('../..')

from integrations.ticket_platforms import UnifiedInventoryAggregator


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: Dict):
        def decorator(func: Callable[..., Any]):
            self.tools[name] = {
                "function": func,
                "description": description,
                "parameters": parameters,
            }
            return func
        return decorator

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        definitions = []
        for name, tool in self.tools.items():
            definitions.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
            )
        return definitions

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.tools[name]["function"](**arguments)


registry = ToolRegistry()

# Initialize unified aggregator
_aggregator = None

def get_aggregator() -> UnifiedInventoryAggregator:
    """Get global aggregator instance"""
    global _aggregator
    if _aggregator is None:
        _aggregator = UnifiedInventoryAggregator()
    return _aggregator


@registry.register(
    name="search_tickets",
    description="Search for tickets across StubHub, SeatGeek, and Ticketmaster",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query (team, artist, event)"},
            "city": {"type": "string", "description": "City name"},
            "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)"},
        },
        "required": ["query"],
    },
)
def search_tickets(query: str, 
                  city: Optional[str] = None,
                  date_from: Optional[str] = None,
                  date_to: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for tickets across all platforms
    
    Returns aggregated results with price comparison
    """
    aggregator = get_aggregator()
    
    # Run async search
    results = asyncio.run(aggregator.search_events(
        query=query,
        city=city,
        date_from=date_from,
        date_to=date_to
    ))
    
    return {
        "query": query,
        "total_events": results['total_events'],
        "platforms_searched": results['platforms_queried'],
        "events": results['events'][:10],  # Return top 10
        "best_deals": aggregator.find_best_deals(results['events'], min_tickets=1)[:5]
    }


@registry.register(
    name="compare_prices",
    description="Compare ticket prices across platforms for the same event",
    parameters={
        "type": "object",
        "properties": {
            "event_name": {"type": "string", "description": "Event name"},
            "venue": {"type": "string", "description": "Venue name"},
            "date": {"type": "string", "description": "Event date (YYYY-MM-DD)"},
        },
        "required": ["event_name", "venue", "date"],
    },
)
def compare_prices(event_name: str, venue: str, date: str) -> Dict[str, Any]:
    """
    Compare prices for the same event across all platforms
    
    Returns price comparison with savings recommendations
    """
    aggregator = get_aggregator()
    comparison = aggregator.compare_prices(event_name, venue, date)
    
    return comparison


@registry.register(
    name="find_best_deals",
    description="Find the best ticket deals across all platforms",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_price": {"type": "number", "description": "Maximum price per ticket"},
            "min_tickets": {"type": "integer", "description": "Minimum tickets needed"},
            "city": {"type": "string", "description": "City name"},
        },
        "required": ["query"],
    },
)
def find_best_deals(query: str,
                   max_price: Optional[float] = None,
                   min_tickets: int = 1,
                   city: Optional[str] = None) -> Dict[str, Any]:
    """
    Find best deals across all platforms with filters
    
    Returns events sorted by value (price + availability + platform count)
    """
    aggregator = get_aggregator()
    
    # Search events
    results = asyncio.run(aggregator.search_events(query, city=city))
    
    # Find best deals
    deals = aggregator.find_best_deals(
        results['events'],
        max_price=max_price,
        min_tickets=min_tickets
    )
    
    return {
        "query": query,
        "filters": {
            "max_price": max_price,
            "min_tickets": min_tickets,
            "city": city
        },
        "total_deals_found": len(deals),
        "best_deals": deals[:10],  # Top 10 deals
        "platforms": list(set(p['platform'] for event in deals for p in event.get('platforms', [])))
    }


@registry.register(
    name="check_inventory",
    description="Get available seats for an event (legacy - use search_tickets for real data)",
    parameters={
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "section": {"type": "string"},
            "quantity": {"type": "integer", "minimum": 1},
        },
        "required": ["event_id", "quantity"],
    },
)
def check_inventory(event_id: str, quantity: int, section: Optional[str] = None) -> Dict[str, Any]:
    """Legacy function - kept for backward compatibility"""
    base_section = section or "A"
    seats = [
        {"id": f"{base_section}-{i}", "price": 120.0 + i * 5, "section": base_section, "row": str(5 + i)}
        for i in range(1, quantity + 1)
    ]
    return {"event_id": event_id, "seats": seats}


@registry.register(
    name="hold_tickets",
    description="Place a temporary hold on seats",
    parameters={
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "seat_ids": {"type": "array", "items": {"type": "string"}},
            "expires_in_seconds": {"type": "integer", "default": 300},
        },
        "required": ["event_id", "seat_ids"],
    },
)
def hold_tickets(event_id: str, seat_ids: List[str], expires_in_seconds: int = 300) -> Dict[str, Any]:
    """Place a hold on tickets"""
    hold_id = f"HOLD_{int(datetime.datetime.utcnow().timestamp())}"
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)).isoformat() + "Z"
    return {"hold_id": hold_id, "event_id": event_id, "seat_ids": seat_ids, "expires_at": expires_at}


@registry.register(
    name="create_order",
    description="Create an order from a hold",
    parameters={
        "type": "object",
        "properties": {
            "hold_id": {"type": "string"},
            "customer_id": {"type": "string"},
            "payment_method_token": {"type": "string"},
        },
        "required": ["hold_id", "customer_id", "payment_method_token"],
    },
)
def create_order(hold_id: str, customer_id: str, payment_method_token: str) -> Dict[str, Any]:
    """Create an order"""
    order_id = f"ORD_{int(datetime.datetime.utcnow().timestamp())}"
    return {"order_id": order_id, "status": "confirmed", "customer_id": customer_id, "hold_id": hold_id}


@registry.register(
    name="upgrade_tickets",
    description="Upgrade existing tickets to better seats",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "target_section": {"type": "string"},
            "max_price_delta": {"type": "number"},
        },
        "required": ["order_id"],
    },
)
def upgrade_tickets(order_id: str, target_section: Optional[str] = None, max_price_delta: Optional[float] = None) -> Dict[str, Any]:
    """Upgrade tickets"""
    price_delta = 30.0 if max_price_delta is None else min(30.0, max_price_delta)
    return {"order_id": order_id, "status": "upgraded", "price_delta": price_delta, "target_section": target_section}


@registry.register(
    name="release_hold",
    description="Release a temporary hold",
    parameters={
        "type": "object",
        "properties": {"hold_id": {"type": "string"}},
        "required": ["hold_id"],
    },
)
def release_hold(hold_id: str) -> Dict[str, Any]:
    """Release a hold"""
    return {"hold_id": hold_id, "released": True}


@registry.register(
    name="get_event_info",
    description="Fetch metadata for an event (legacy - use search_tickets for real data)",
    parameters={
        "type": "object",
        "properties": {"event_id": {"type": "string"}},
        "required": ["event_id"],
    },
)
def get_event_info(event_id: str) -> Dict[str, Any]:
    """Legacy function - kept for backward compatibility"""
    return {"event_id": event_id, "name": "Pro Sports Game", "start_time": "2025-10-07T19:00:00Z", "venue": "Main Arena"}


class ToolCallingAgent:
    def __init__(self, endpoint, tool_registry: ToolRegistry):
        self.endpoint = endpoint
        self.tools = tool_registry

    def chat(self, user_message: str, conversation_history: List[Dict]) -> str:
        messages = [
            {
                "role": "system",
                "content": f"You have access to these tools: {json.dumps(self.tools.get_tool_definitions())}",
            }
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        response = self.endpoint.predict(instances=[{"messages": messages}])
        assistant_message = response.predictions[0]["response"]

        if "<tool_call>" in assistant_message:
            tool_call = self._parse_tool_call(assistant_message)
            tool_result = self.tools.execute(tool_call["name"], tool_call["arguments"])

            messages.append({"role": "assistant", "content": assistant_message})
            messages.append({"role": "tool", "content": str(tool_result)})

            final = self.endpoint.predict(instances=[{"messages": messages}])
            return final.predictions[0]["response"]

        return assistant_message

    def _parse_tool_call(self, message: str) -> Dict:
        import re

        match = re.search(r"<tool_call>(.*?)</tool_call>", message, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return {"name": "", "arguments": {}}
