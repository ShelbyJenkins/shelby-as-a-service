from typing import Literal

from agents.ceq.ceq_agent import CEQAgent
from agents.vanillallm.vanillallm_agent import VanillaLLM

AVAILABLE_AGENTS_TYPINGS = Literal[
    CEQAgent.class_name,
    VanillaLLM.class_name,
]
AVAILABLE_AGENTS_NAMES: list[str] = [
    CEQAgent.CLASS_NAME,
    VanillaLLM.CLASS_NAME,
]
AVAILABLE_AGENTS_UI_NAMES = [
    CEQAgent.CLASS_UI_NAME,
    VanillaLLM.CLASS_UI_NAME,
]
AVAILABLE_AGENTS = [
    CEQAgent,
    VanillaLLM,
]
