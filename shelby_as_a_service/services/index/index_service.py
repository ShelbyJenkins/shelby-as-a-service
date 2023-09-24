from models.app_base import AppBase
from models.index_model import IndexModel, DataDomainModel, DataSourceModel
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import List, Optional
from services.apps.app_management import AppManager
from services.providers.database_service import PineconeService, LocalFileStoreService

class DataSourceService(AppBase):
    
    model_ = DataSourceModel()
    required_services_ = [PineconeService, LocalFileStoreService]
    
    def __init__(self):
        """ """
        super().__init__()


class DataDomainService(AppBase):
    
    model_ = DataDomainModel()
    data_source_service_ = DataSourceService
    required_services_ = [PineconeService, LocalFileStoreService]
    
    def __init__(self):
        """ """
        super().__init__()

    def load_data_domains(self, data_domain_config):
        self.setup_config(data_domain_config)

        data_domain_sources_config = data_domain_config.get(
            "data_domain_sources", []
        )
        data_domain_sources = []
        for data_source_config in data_domain_sources_config or [{}]:
            data_source_service = DataSourceService()
            data_source_service.setup_config(data_source_config)
            data_domain_sources.append(data_source_service)

        setattr(self, "data_domain_sources", data_domain_sources)

class IndexService(AppBase):
    
    model_ = IndexModel()
    data_domain_service_ = DataDomainService
    required_services_ = [PineconeService, LocalFileStoreService]
    
    def __init__(self):
        """ """
        super().__init__()


    def load_index(self, sprite):
        sprite_name = sprite.model_.service_name_
        
        config = AppManager.load_app_file(AppBase.app_name)
        index_data_domains_config = (
            config.get("app_instance", None)
            .get("services", None)
            .get(sprite_name, None)
            .get("services", None)
            .get("index_service", None)
            .get("index_data_domains", [])
        )
        
        index_data_domains = []
        for data_domain_config in index_data_domains_config or [{}]:
            data_domain_service = DataDomainService()
            data_domain_service.load_data_domains(data_domain_config)
            index_data_domains.append(data_domain_service)

        setattr(self, "index_data_domains", index_data_domains)
