import os
from typing import Any, List, Type

import services.text_processing.text as TextProcess
from pydantic import BaseModel
from services.database.database_pinecone import PineconeDatabase
from services.provider_base import ProviderBase
from services.service_base import ServiceBase


class LocalFileStoreDatabase(ProviderBase):
    MODULE_NAME: str = "local_filestore_database"
    MODULE_UI_NAME: str = "local_filestore_database"
    REQUIRED_SECRETS: List[str] = []

    class ProviderConfigModel(BaseModel):
        max_response_tokens: int = 1

    config: ProviderConfigModel

    def __init__(self):
        super().__init__()

    def _write_documents_to_database(self, documents, data_domain, data_source):
        data_domain_name_file_path = os.path.join(
            self.app.local_index_dir,
            "outputs",
            data_domain.data_domain_name,
        )
        os.makedirs(data_domain_name_file_path, exist_ok=True)
        for document in documents:
            title = TextProcess.extract_and_clean_title(document, data_source.data_source_url)
            valid_filename = "".join(c if c.isalnum() else "_" for c in title)
            file_path = os.path.join(data_domain_name_file_path, f"{valid_filename}.md")
            page_content = document.page_content
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(page_content)

            # Optionally, log the path to which the document was written
            print(f"Document written to: {file_path}")


class DatabaseService(ServiceBase):
    MODULE_NAME: str = "database_service"
    MODULE_UI_NAME: str = "database_service"
    PROVIDER_TYPE: str = "database_provider"
    DEFAULT_PROVIDER: Type = LocalFileStoreDatabase
    REQUIRED_MODULES: List[Type] = [PineconeDatabase, LocalFileStoreDatabase]

    class ServiceConfigModel(BaseModel):
        agent_select_status_message: str = "Search index to find docs related to request."

    config: ServiceConfigModel

    def __init__(self):
        super().__init__()

    def query_index(
        self,
        search_terms,
        retrieve_n_docs=None,
        data_domain_name=None,
        database_provider=None,
    ):
        provider = self.get_provider(database_provider)
        if provider:
            return provider._query_index(search_terms, retrieve_n_docs, data_domain_name)
        else:
            print("rnr")

    def write_documents_to_database(
        self,
        documents,
        data_domain,
        data_source,
    ):
        provider = self.get_provider(data_source.data_source_database_provider)
        if provider:
            return provider._write_documents_to_database(documents, data_domain, data_source)
        else:
            print("rnr")
