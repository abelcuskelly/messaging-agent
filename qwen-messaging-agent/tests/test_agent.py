import unittest
from unittest.mock import Mock
from agent.messaging_agent import MessagingAgent


class TestMessagingAgent(unittest.TestCase):
    def setUp(self):
        self.mock_endpoint = Mock()
        self.agent = MessagingAgent(self.mock_endpoint)

    def test_basic_response(self):
        self.mock_endpoint.predict.return_value = Mock(predictions=[{"response": "Hello!"}])
        response = self.agent.chat("Hi")
        self.assertIn("Hello", response)

    def test_conversation_history(self):
        self.mock_endpoint.predict.return_value = Mock(predictions=[{"response": "Noted"}])
        self.agent.chat("My name is John")
        self.agent.chat("What's my name?")
        self.assertEqual(len(self.agent.conversation_history), 4)

    def test_trim_history(self):
        self.mock_endpoint.predict.return_value = Mock(predictions=[{"response": "ok"}])
        for i in range(60):
            self.agent.chat(f"Message {i}")
        self.agent.trim_history(max_messages=50)
        self.assertLessEqual(len(self.agent.conversation_history), 50)


if __name__ == "__main__":
    unittest.main()


