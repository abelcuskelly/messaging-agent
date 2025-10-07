from typing import Dict


class Agent:
    def __init__(self, name: str, endpoint, system_prompt: str):
        self.name = name
        self.endpoint = endpoint
        self.system_prompt = system_prompt

    def process(self, message: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]
        response = self.endpoint.predict(instances=[{"messages": messages}])
        return response.predictions[0]["response"]


class MultiAgentSystem:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.agents: Dict[str, Agent] = {}
        self._setup_agents()

    def _setup_agents(self) -> None:
        self.agents["router"] = Agent(
            name="router",
            endpoint=self.endpoint,
            system_prompt=(
                "You are a router agent. Respond with only one word: technical, sales, or support."
            ),
        )
        self.agents["technical"] = Agent(
            name="technical",
            endpoint=self.endpoint,
            system_prompt="You are a technical specialist. Provide detailed technical answers.",
        )
        self.agents["sales"] = Agent(
            name="sales",
            endpoint=self.endpoint,
            system_prompt="You are a sales specialist. Help users understand ticket offerings.",
        )
        self.agents["support"] = Agent(
            name="support",
            endpoint=self.endpoint,
            system_prompt="You are a customer support specialist. Help resolve issues.",
        )

    def process_request(self, user_message: str) -> Dict:
        specialist_name = self.agents["router"].process(user_message).strip().lower()
        if specialist_name not in ("technical", "sales", "support"):
            specialist_name = "support"
        response = self.agents[specialist_name].process(user_message)
        return {"specialist": specialist_name, "response": response}


