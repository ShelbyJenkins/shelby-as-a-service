from models.app_base import AppBase
from models.index_model import IndexModel, DataDomainModel, DataSourceModel
from typing import List, Optional
from services.utils.app_management import AppManager

class DataSourceService(AppBase):
    
    model_ = DataSourceModel()
    
    def __init__(self):
        """ """
        super().__init__()


class DataDomainService(AppBase):
    
    model_ = DataDomainModel()
    data_source_service_ = DataSourceService
    
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
    
    def __init__(self):
        """ """
        super().__init__()
        
        config = AppManager.load_app_file(AppBase.app_name)
        self.index_config = (
            config.get("app_instance", None)
            .get("services", None)
            .get("index_service", None)
        )
        self.index_data_domains_config = (
            self.index_config.get("index_data_domains", [])
        )
        self.setup_config(self.index_config)

    def load_index(self):
        
        
        index_data_domains = []
        for data_domain_config in self.index_data_domains_config or [{}]:
            data_domain_service = DataDomainService()
            data_domain_service.load_data_domains(data_domain_config)
            index_data_domains.append(data_domain_service)

        setattr(self, "index_data_domains", index_data_domains)

        self.app.index_service = self