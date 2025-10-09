"""
Conversation State Management
Implements state machine for multi-turn dialogue management
"""

import json
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict, field
import structlog
from transitions import Machine
import redis

logger = structlog.get_logger()


class ConversationState(Enum):
    """Conversation states for ticketing agent."""
    GREETING = "greeting"
    INQUIRY = "inquiry"
    BROWSING = "browsing"
    SELECTING = "selecting"
    PURCHASING = "purchasing"
    PAYMENT = "payment"
    CONFIRMATION = "confirmation"
    SUPPORT = "support"
    UPGRADE = "upgrade"
    REFUND = "refund"
    CLOSING = "closing"
    ENDED = "ended"


class ConversationIntent(Enum):
    """User intent classification."""
    GREETING = "greeting"
    BROWSE_TICKETS = "browse_tickets"
    CHECK_PRICE = "check_price"
    BUY_TICKET = "buy_ticket"
    UPGRADE_SEAT = "upgrade_seat"
    REQUEST_REFUND = "request_refund"
    ASK_QUESTION = "ask_question"
    COMPLAINT = "complaint"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"


@dataclass
class ConversationContext:
    """Context data for conversation."""
    conversation_id: str
    user_id: str
    current_state: str = ConversationState.GREETING.value
    intent: str = ConversationIntent.UNKNOWN.value
    
    # Ticket selection context
    selected_game: Optional[str] = None
    selected_section: Optional[str] = None
    selected_seats: Optional[List[str]] = None
    ticket_price: Optional[float] = None
    
    # Transaction context
    order_id: Optional[str] = None
    payment_method: Optional[str] = None
    confirmation_code: Optional[str] = None
    
    # Support context
    issue_type: Optional[str] = None
    resolution_status: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    message_count: int = 0
    
    def update(self):
        """Update timestamp."""
        self.updated_at = datetime.utcnow().isoformat()
        self.message_count += 1


class ConversationStateMachine:
    """
    State machine for managing conversation flow.
    Handles transitions between states based on user actions.
    """
    
    # Define valid state transitions
    transitions = [
        # From GREETING
        {'trigger': 'start_browsing', 'source': ConversationState.GREETING.value, 'dest': ConversationState.BROWSING.value},
        {'trigger': 'ask_question', 'source': ConversationState.GREETING.value, 'dest': ConversationState.INQUIRY.value},
        
        # From BROWSING
        {'trigger': 'select_tickets', 'source': ConversationState.BROWSING.value, 'dest': ConversationState.SELECTING.value},
        {'trigger': 'ask_question', 'source': ConversationState.BROWSING.value, 'dest': ConversationState.INQUIRY.value},
        
        # From SELECTING
        {'trigger': 'confirm_purchase', 'source': ConversationState.SELECTING.value, 'dest': ConversationState.PURCHASING.value},
        {'trigger': 'continue_browsing', 'source': ConversationState.SELECTING.value, 'dest': ConversationState.BROWSING.value},
        
        # From PURCHASING
        {'trigger': 'proceed_to_payment', 'source': ConversationState.PURCHASING.value, 'dest': ConversationState.PAYMENT.value},
        {'trigger': 'cancel_purchase', 'source': ConversationState.PURCHASING.value, 'dest': ConversationState.BROWSING.value},
        
        # From PAYMENT
        {'trigger': 'complete_payment', 'source': ConversationState.PAYMENT.value, 'dest': ConversationState.CONFIRMATION.value},
        {'trigger': 'payment_failed', 'source': ConversationState.PAYMENT.value, 'dest': ConversationState.PURCHASING.value},
        
        # From CONFIRMATION
        {'trigger': 'end_conversation', 'source': ConversationState.CONFIRMATION.value, 'dest': ConversationState.CLOSING.value},
        
        # Support flows
        {'trigger': 'request_support', 'source': '*', 'dest': ConversationState.SUPPORT.value},
        {'trigger': 'request_upgrade', 'source': '*', 'dest': ConversationState.UPGRADE.value},
        {'trigger': 'request_refund', 'source': '*', 'dest': ConversationState.REFUND.value},
        
        # From INQUIRY
        {'trigger': 'start_browsing', 'source': ConversationState.INQUIRY.value, 'dest': ConversationState.BROWSING.value},
        {'trigger': 'end_conversation', 'source': ConversationState.INQUIRY.value, 'dest': ConversationState.CLOSING.value},
        
        # From SUPPORT/UPGRADE/REFUND
        {'trigger': 'resolve_issue', 'source': [ConversationState.SUPPORT.value, ConversationState.UPGRADE.value, ConversationState.REFUND.value], 'dest': ConversationState.CLOSING.value},
        {'trigger': 'continue_browsing', 'source': [ConversationState.SUPPORT.value, ConversationState.UPGRADE.value, ConversationState.REFUND.value], 'dest': ConversationState.BROWSING.value},
        
        # From CLOSING
        {'trigger': 'finalize', 'source': ConversationState.CLOSING.value, 'dest': ConversationState.ENDED.value},
    ]
    
    def __init__(self, context: ConversationContext):
        """Initialize state machine with context."""
        self.context = context
        
        # Initialize state machine
        self.machine = Machine(
            model=self,
            states=[state.value for state in ConversationState],
            transitions=self.transitions,
            initial=context.current_state,
            auto_transitions=False,
            send_event=True
        )
        
        logger.debug("State machine initialized",
                    conversation_id=context.conversation_id,
                    initial_state=context.current_state)
    
    def get_state(self) -> str:
        """Get current state."""
        return self.state
    
    def transition(self, trigger: str, **kwargs) -> bool:
        """
        Attempt state transition.
        
        Args:
            trigger: Transition trigger name
            **kwargs: Additional context data
            
        Returns:
            True if transition successful
        """
        try:
            # Update context
            for key, value in kwargs.items():
                if hasattr(self.context, key):
                    setattr(self.context, key, value)
            
            # Trigger transition
            trigger_func = getattr(self, trigger, None)
            if trigger_func and callable(trigger_func):
                trigger_func()
                
                # Update context state
                self.context.current_state = self.state
                self.context.update()
                
                logger.info("State transition",
                           conversation_id=self.context.conversation_id,
                           trigger=trigger,
                           from_state=self.context.current_state,
                           to_state=self.state)
                
                return True
            else:
                logger.warning("Invalid trigger",
                             trigger=trigger,
                             current_state=self.state)
                return False
                
        except Exception as e:
            logger.error("State transition failed",
                        trigger=trigger,
                        error=str(e))
            return False
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions from current state."""
        available = []
        
        for transition in self.transitions:
            source = transition['source']
            if source == '*' or source == self.state or (isinstance(source, list) and self.state in source):
                available.append(transition['trigger'])
        
        return list(set(available))
    
    def get_next_prompt(self) -> str:
        """Get suggested prompt for current state."""
        prompts = {
            ConversationState.GREETING.value: "Hello! How can I help you with tickets today?",
            ConversationState.BROWSING.value: "What game or event are you interested in?",
            ConversationState.SELECTING.value: "Which seats would you like to select?",
            ConversationState.PURCHASING.value: "Ready to complete your purchase?",
            ConversationState.PAYMENT.value: "Please provide your payment information.",
            ConversationState.CONFIRMATION.value: "Your order is confirmed! Is there anything else I can help with?",
            ConversationState.SUPPORT.value: "I'm here to help. What issue are you experiencing?",
            ConversationState.UPGRADE.value: "I can help you upgrade your seats. What would you like to upgrade to?",
            ConversationState.REFUND.value: "I'll help you with your refund request. Can you provide your order details?",
            ConversationState.CLOSING.value: "Thank you for using our service. Have a great day!",
        }
        
        return prompts.get(self.state, "How can I assist you?")


class ConversationManager:
    """Manages conversation state across multiple users."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.state_machines: Dict[str, ConversationStateMachine] = {}
    
    def get_or_create_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> ConversationStateMachine:
        """Get existing conversation or create new one."""
        
        # Try to load from Redis
        if self.redis_client:
            context_data = self.redis_client.get(f"conversation:{conversation_id}")
            if context_data:
                context_dict = json.loads(context_data)
                context = ConversationContext(**context_dict)
                
                # Create state machine
                state_machine = ConversationStateMachine(context)
                self.state_machines[conversation_id] = state_machine
                
                logger.debug("Conversation loaded from Redis",
                           conversation_id=conversation_id)
                
                return state_machine
        
        # Check in-memory cache
        if conversation_id in self.state_machines:
            return self.state_machines[conversation_id]
        
        # Create new conversation
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        state_machine = ConversationStateMachine(context)
        self.state_machines[conversation_id] = state_machine
        
        # Save to Redis
        self._save_conversation(conversation_id, context)
        
        logger.info("New conversation created",
                   conversation_id=conversation_id,
                   user_id=user_id)
        
        return state_machine
    
    def _save_conversation(self, conversation_id: str, context: ConversationContext):
        """Save conversation context to Redis."""
        if self.redis_client:
            self.redis_client.set(
                f"conversation:{conversation_id}",
                json.dumps(asdict(context)),
                ex=86400  # 24 hour expiry
            )
    
    def update_conversation(
        self,
        conversation_id: str,
        trigger: str,
        **context_updates
    ) -> bool:
        """Update conversation state."""
        state_machine = self.state_machines.get(conversation_id)
        if not state_machine:
            logger.error("Conversation not found", conversation_id=conversation_id)
            return False
        
        # Attempt transition
        success = state_machine.transition(trigger, **context_updates)
        
        if success:
            # Save updated context
            self._save_conversation(conversation_id, state_machine.context)
        
        return success
    
    def get_conversation_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context."""
        state_machine = self.state_machines.get(conversation_id)
        return state_machine.context if state_machine else None
    
    def end_conversation(self, conversation_id: str):
        """End and cleanup conversation."""
        if conversation_id in self.state_machines:
            state_machine = self.state_machines[conversation_id]
            
            # Transition to ended
            state_machine.transition('finalize')
            
            # Save final state
            self._save_conversation(conversation_id, state_machine.context)
            
            # Remove from memory
            del self.state_machines[conversation_id]
            
            logger.info("Conversation ended", conversation_id=conversation_id)
    
    def get_all_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active conversations, optionally filtered by user."""
        conversations = []
        
        for conv_id, state_machine in self.state_machines.items():
            context = state_machine.context
            
            if user_id is None or context.user_id == user_id:
                conversations.append({
                    "conversation_id": conv_id,
                    "user_id": context.user_id,
                    "state": context.current_state,
                    "intent": context.intent,
                    "message_count": context.message_count,
                    "created_at": context.created_at,
                    "updated_at": context.updated_at
                })
        
        return conversations


# Global conversation manager
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create global conversation manager."""
    global _conversation_manager
    
    if _conversation_manager is None:
        try:
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
            redis_client.ping()
            _conversation_manager = ConversationManager(redis_client)
        except:
            _conversation_manager = ConversationManager()
        
        logger.info("Conversation manager initialized")
    
    return _conversation_manager


class IntentClassifier:
    """Classify user intent from message."""
    
    def __init__(self):
        self.intent_keywords = {
            ConversationIntent.GREETING: ["hello", "hi", "hey", "good morning", "good evening"],
            ConversationIntent.BROWSE_TICKETS: ["show", "browse", "available", "games", "events"],
            ConversationIntent.CHECK_PRICE: ["price", "cost", "how much", "pricing"],
            ConversationIntent.BUY_TICKET: ["buy", "purchase", "get tickets", "book"],
            ConversationIntent.UPGRADE_SEAT: ["upgrade", "better seat", "move to"],
            ConversationIntent.REQUEST_REFUND: ["refund", "cancel", "money back"],
            ConversationIntent.ASK_QUESTION: ["what", "when", "where", "how", "why"],
            ConversationIntent.COMPLAINT: ["problem", "issue", "complaint", "unhappy"],
            ConversationIntent.GOODBYE: ["bye", "goodbye", "thanks", "thank you"],
        }
    
    def classify(self, message: str) -> ConversationIntent:
        """Classify user intent from message."""
        message_lower = message.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            logger.debug("Intent classified",
                        message=message[:50],
                        intent=best_intent.value)
            return best_intent
        
        return ConversationIntent.UNKNOWN


class ConversationFlowManager:
    """Manages conversation flow with state machine."""
    
    def __init__(
        self,
        conversation_manager: ConversationManager,
        intent_classifier: IntentClassifier
    ):
        self.conversation_manager = conversation_manager
        self.intent_classifier = intent_classifier
    
    def process_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process user message and update conversation state.
        
        Returns:
            Dictionary with state, intent, suggested actions, and prompt
        """
        # Get or create conversation
        state_machine = self.conversation_manager.get_or_create_conversation(
            conversation_id, user_id
        )
        
        # Classify intent
        intent = self.intent_classifier.classify(message)
        
        # Update context with intent
        state_machine.context.intent = intent.value
        state_machine.context.update()
        
        # Determine appropriate transition
        trigger = self._get_trigger_for_intent(intent, state_machine.get_state())
        
        if trigger:
            self.conversation_manager.update_conversation(
                conversation_id, trigger
            )
        
        # Get current state info
        current_state = state_machine.get_state()
        available_actions = state_machine.get_available_actions()
        next_prompt = state_machine.get_next_prompt()
        
        return {
            "conversation_id": conversation_id,
            "current_state": current_state,
            "intent": intent.value,
            "available_actions": available_actions,
            "suggested_prompt": next_prompt,
            "context": asdict(state_machine.context)
        }
    
    def _get_trigger_for_intent(
        self,
        intent: ConversationIntent,
        current_state: str
    ) -> Optional[str]:
        """Map intent to state transition trigger."""
        
        # Intent to trigger mapping
        intent_triggers = {
            ConversationIntent.BROWSE_TICKETS: "start_browsing",
            ConversationIntent.BUY_TICKET: "confirm_purchase",
            ConversationIntent.UPGRADE_SEAT: "request_upgrade",
            ConversationIntent.REQUEST_REFUND: "request_refund",
            ConversationIntent.ASK_QUESTION: "ask_question",
            ConversationIntent.COMPLAINT: "request_support",
            ConversationIntent.GOODBYE: "end_conversation",
        }
        
        return intent_triggers.get(intent)
