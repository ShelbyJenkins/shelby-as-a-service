import os
from typing import Any, List, Type

import modules.text_processing.text as TextProcess
import modules.utils.config_manager as ConfigManager
import pinecone
from services.providers.database_pinecone import PineconeDatabase
from services.service_base import ServiceBase


class LocalFileStoreDatabase(ServiceBase):
    provider_name: str = "local_filestore_database"

    def __init__(self, parent_service):
        super().__init__(parent_service=parent_service)

    def _write_documents_to_database(self, documents, data_domain, data_source):
        data_domain_name_file_path = os.path.join(
            self.app.local_index_dir,
            "outputs",
            data_domain.data_domain_name,
        )
        os.makedirs(data_domain_name_file_path, exist_ok=True)
        for document in documents:
            title = TextProcess.extract_and_clean_title(
                document, data_source.data_source_url
            )
            valid_filename = "".join(c if c.isalnum() else "_" for c in title)
            file_path = os.path.join(data_domain_name_file_path, f"{valid_filename}.md")
            page_content = document.page_content
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(page_content)

            # Optionally, log the path to which the document was written
            print(f"Document written to: {file_path}")


class DatabaseService(ServiceBase):
    service_name: str = "database_service"
    service_ui_name: str = "database_service"
    provider_type: str = "database_provider"
    available_providers: List[Type] = [PineconeDatabase, LocalFileStoreDatabase]
    default_provider: Type = LocalFileStoreDatabase

    def __init__(self, parent_agent=None):
        super().__init__(parent_agent=parent_agent)

    def query_index(
        self,
        search_terms,
        retrieve_n_docs=None,
        data_domain_name=None,
        database_provider=None,
    ):
        provider = self.get_provider(database_provider)
        if provider:
            return provider._query_index(
                search_terms, retrieve_n_docs, data_domain_name
            )
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
            return provider._write_documents_to_database(
                documents, data_domain, data_source
            )
        else:
            print("rnr")
