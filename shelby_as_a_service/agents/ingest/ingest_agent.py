from typing import Any, Dict, List, Optional, Type

# from modules.index.data_model import DataModels
from agents.agent_base import AgentBase
from pydantic import BaseModel
from services.database.database_service import DatabaseService
from services.ingest.ingest_service import IngestService


class IngestAgent(AgentBase):
    MODULE_NAME: str = "ingest_agent"
    AGENT_UI_NAME: str = "ingest_agent"
    DEFAULT_PROMPT_TEMPLATE_PATH: str = "ceq_main_prompt.yaml"
    REQUIRED_MODULES: List[Type] = [IngestService, DatabaseService]

    class AgentConfigModel(BaseModel):
        agent_select_status_message: str = (
            "Load a URL Data Tab, and we'll access it and use it to generate a response."
        )
        llm_provider: str = "openai_llm"
        llm_model: str = "gpt-4"
        database_provider: str = "local_filestore_database"

    config: AgentConfigModel

    def __init__(self):
        super().__init__()

    def load_single_website(self, url):
        data_source = DataSourceModel(
            data_source_name=None,
            data_source_description=None,
            data_source_filter_url=None,
            data_source_ingest_provider="generic_web_scraper",
            data_source_database_provider="local_filestore_database",
            data_source_url=url,
        )
        data_domain = DataDomainModel(
            data_domain_name="web_agent",
            data_domain_database_provider="local_filestore_database",
            data_domain_sources=[data_source],
        )
        documents_list = []
        for data_source in data_domain.data_domain_sources:
            documents_iterator = self.ingest_service.load(data_source)
            if documents_iterator is not None:
                try:
                    documents_list = list(documents_iterator)
                except TypeError:
                    print(f"Error: Object {documents_iterator} is not iterable")
            else:
                print("Error: documents_iterator is None")
            if documents_list:
                self.database_service.write_documents_to_database(
                    documents_list, data_domain, data_source
                )
                return documents_list

    def ingest_docs(self):
        # indexes = pinecone.list_indexes()
        # if self.index_name not in indexes:
        #     # create new index
        #     self.create_index()
        #     indexes = pinecone.list_indexes()
        #     self.log.print_and_log(f"Created index: {indexes}")
        # self.vectorstore = pinecone.Index(self.index_name)

        # ### Adds sources from yaml config file to queue ###

        # self.enabled_data_sources = []
        # # Iterate over each source aka namespace
        # for domain in self.index_description_file["data_domains"]:
        #     data_domain_name = domain["name"]
        #     domain_description = domain["description"]
        #     for data_source_name, source in domain["sources"].items():
        #         data_source = DataSourceConfig(
        #             self, data_domain_name, domain_description, data_source_name, source
        #         )
        #         if data_source.update_enabled == False:
        #             continue
        #         self.enabled_data_sources.append(data_source)
        #         self.log.print_and_log(f"Will index: {data_source_name}")
        self.log.print_and_log(f"Initial index stats: {self.vectorstore.describe_index_stats()}\n")

        for data_source in self.enabled_data_sources:
            # Retries if there is an error
            retry_count = 2
            for i in range(retry_count):
                try:
                    self.log.print_and_log(f"-----Now indexing: {data_source.data_source_name}\n")
                    # Get count of vectors in index matching the "resource" metadata field
                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={"data_source_name": {"$eq": data_source.data_source_name}}
                    )
                    existing_resource_vector_count = (
                        index_resource_stats.get("namespaces", {})
                        .get(self.deployment_name, {})
                        .get("vector_count", 0)
                    )
                    self.log.print_and_log(
                        f"Existing vector count for {data_source.data_source_name}: {existing_resource_vector_count}"
                    )

                    # Load documents
                    documents = data_source.scraper.load()
                    if not documents:
                        self.log.print_and_log(
                            f"Skipping data_source: no data loaded for {data_source.data_source_name}"
                        )
                        break
                    self.log.print_and_log(f"Total documents loaded for indexing: {len(documents)}")

                    # Removes bad chars, and chunks text
                    document_chunks = data_source.preprocessor.run(documents)
                    if not document_chunks:
                        self.log.print_and_log(
                            f"Skipping data_source: no data after preprocessing {data_source.data_source_name}"
                        )
                        break
                    self.log.print_and_log(
                        f"Total document chunks after processing: {len(document_chunks)}"
                    )

                    # Checks against local docs if there are changes or new docs
                    (
                        has_changes,
                        new_or_changed_chunks,
                    ) = data_source.preprocessor.compare_chunks(data_source, document_chunks)
                    # If there are changes or new docs, delete existing local files and write new files
                    if not has_changes:
                        self.log.print_and_log(
                            f"Skipping data_source: no new data found for {data_source.data_source_name}"
                        )
                        break
                    self.log.print_and_log(
                        f"Found {len(new_or_changed_chunks)} new or changed documents"
                    )
                    (
                        text_chunks,
                        document_chunks,
                    ) = data_source.preprocessor.create_text_chunks(data_source, document_chunks)
                    self.log.print_and_log(
                        f"Total document chunks after final check: {len(document_chunks)}"
                    )

                    # Get dense_embeddings
                    dense_embeddings = data_source.embedding_retriever.embed_documents(text_chunks)

                    # If the "resource" already has vectors delete the existing vectors before upserting new vectors
                    # We have to delete all because the difficulty in specifying specific documents in pinecone
                    if existing_resource_vector_count != 0:
                        self._clear_data_source(data_source)
                        index_resource_stats = data_source.vectorstore.describe_index_stats(
                            filter={"data_source_name": {"$eq": data_source.data_source_name}}
                        )
                        cleared_resource_vector_count = (
                            index_resource_stats.get("namespaces", {})
                            .get(self.deployment_name, {})
                            .get("vector_count", 0)
                        )
                        self.log.print_and_log(
                            f"Removing pre-existing vectors. New count: {cleared_resource_vector_count} (should be 0)"
                        )

                    vectors_to_upsert = []
                    vector_counter = 0
                    for i, document_chunk in enumerate(document_chunks):
                        prepared_vector = {
                            "id": f"id-{data_source.data_source_name}-{vector_counter}",
                            "values": dense_embeddings[i],
                            "metadata": document_chunk,
                        }
                        vector_counter += 1
                        vectors_to_upsert.append(prepared_vector)

                    self.log.print_and_log(f"Upserting {len(vectors_to_upsert)} vectors")
                    # data_source.vectorstore.upsert(
                    #     vectors=vectors_to_upsert,
                    #     namespace=self.deployment_name,
                    #     batch_size=self.config.index_vectorstore_upsert_batch_size,
                    #     show_progress=True,
                    # )

                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={"data_source_name": {"$eq": data_source.data_source_name}}
                    )
                    new_resource_vector_count = (
                        index_resource_stats.get("namespaces", {})
                        .get(self.deployment_name, {})
                        .get("vector_count", 0)
                    )
                    self.log.print_and_log(
                        f"Indexing complete for: {data_source.data_source_name}\nPrevious vector count: {existing_resource_vector_count}\nNew vector count: {new_resource_vector_count}\n"
                    )
                    # self.log.print_and_log(f'Post-upsert index stats: {index_resource_stats}\n')

                    data_source.preprocessor.write_chunks(data_source, document_chunks)

                    # If completed successfully, break the retry loop
                    break

                except Exception as error:
                    error_info = traceback.format_exc()
                    self.log.print_and_log(f"An error occurred: {error}\n{error_info}")
                    if i < retry_count - 1:  # i is zero indexed
                        continue  # this will start the next iteration of loop thus retrying your code block
                    else:
                        raise  # if exception in the last retry then raise it.

        self.log.print_and_log(f"Final index stats: {self.vectorstore.describe_index_stats()}")
