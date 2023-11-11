from typing import Literal

from services.agents.ceq.ceq_agent import CEQAgent
from services.agents.vanillallm.vanillallm_agent import VanillaLLM

AVAILABLE_AGENT_NAMES = Literal[
    CEQAgent.class_name,
    VanillaLLM.class_name,
]
AVAILABLE_AGENT_UI_NAMES = [
    CEQAgent.CLASS_UI_NAME,
    VanillaLLM.CLASS_UI_NAME,
]
AVAILABLE_AGENTS = [
    CEQAgent,
    VanillaLLM,
]
