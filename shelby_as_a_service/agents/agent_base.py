from typing import Any, Dict, List, Optional, Type

from config.app_base import AppBase
from modules.utils.log_service import Logger


class AgentBase(AppBase):
    AGENT_NAME: str
    CLASS_NAME_TYPE: str = "AGENT_NAME"
    CLASS_UI_NAME_TYPE: str = "AGENT_UI_NAME"
    CLASS_CONFIG_TYPE: str = "agents"
    CLASS_MODEL_TYPE: str = "AgentConfigModel"
    AVAILABLE_CLASS_TYPES: List[str] = ["AVAILABLE_SERVICES"]
    AVAILABLE_SERVICES: List[Type]

    log: Logger
    service_config_dict_from_file: Dict[str, Any]

    def __init__(self):
        self.app = AppBase
        self.log = AppBase.log

    def get_service_instances(self):
        list_of_service_instances = []
        for service in self.AVAILABLE_SERVICES:
            if service_instance := getattr(self, service.SERVICE_NAME, None):
                list_of_service_instances.append(service_instance)
            else:
                new_service = service(
                    self.service_config_dict_from_file.get(service.SERVICE_NAME, {})
                )
                setattr(self, service.SERVICE_NAME, new_service)
                list_of_service_instances.append(new_service)

        return list_of_service_instances

    def instantiate_available_services(self, agent_config, **kwargs):
        available_service_instances = []
        services_config = agent_config.get("services", {})
        for service in self.AVAILABLE_SERVICES:
            service_config = services_config.get(service.SERVICE_NAME, {})
            service_instance = service(service_config=service_config, **kwargs)
            setattr(self, service.SERVICE_NAME, service_instance)
            available_service_instances.append(service_instance)
        return available_service_instances
