from typing import Any, Dict, List, Optional, Type

# from modules.index.data_model import DataModels
from app.module_base import ModuleBase
from pydantic import BaseModel
from services.document_loading.document_loading_service import DocLoadingService


class IngestAgent(ModuleBase):
    CLASS_NAME: str = "ingest_agent"
    CLASS_UI_NAME: str = "ingest_agent"
    REQUIRED_CLASSES: List[Type] = [DocLoadingService]

    class ClassConfigModel(BaseModel):
        database_provider: str = "local_filestore_database"
        doc_loading_provider: str = "generic_web_scraper"

    config: ClassConfigModel
    list_of_class_instances: list[Any]
    list_of_class_ui_names: list[Any]
    doc_loading_service: DocLoadingService

    def __init__(self, config_file_dict={}, **kwargs):
        self.setup_class_instance(class_instance=self, config_file_dict=config_file_dict, **kwargs)

    def ingest_docs(self):
        # indexes = pinecone.list_indexes()
        # if self.index_name not in indexes:
        #     # create new index
        #     self.create_index()
        #     indexes = pinecone.list_indexes()
        #     self.log.info(f"Created index: {indexes}")
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
        #         self.log.info(f"Will index: {data_source_name}")
        self.log.info(f"Initial index stats: {self.vectorstore.describe_index_stats()}\n")

        for data_source in self.enabled_data_sources:
            # Retries if there is an error
            retry_count = 2
            for i in range(retry_count):
                try:
                    self.log.info(f"-----Now indexing: {data_source.data_source_name}\n")
                    # Get count of vectors in index matching the "resource" metadata field
                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={"data_source_name": {"$eq": data_source.data_source_name}}
                    )
                    existing_resource_vector_count = (
                        index_resource_stats.get("namespaces", {}).get(self.deployment_name, {}).get("vector_count", 0)
                    )
                    self.log.info(
                        f"Existing vector count for {data_source.data_source_name}: {existing_resource_vector_count}"
                    )

                    # Load documents
                    documents = data_source.scraper.load()
                    if not documents:
                        self.log.info(f"Skipping data_source: no data loaded for {data_source.data_source_name}")
                        break
                    self.log.info(f"Total documents loaded for indexing: {len(documents)}")

                    # Removes bad chars, and chunks text
                    document_chunks = data_source.preprocessor.run(documents)
                    if not document_chunks:
                        self.log.info(f"Skipping data_source: no data after preprocessing {data_source.data_source_name}")
                        break
                    self.log.info(f"Total document chunks after processing: {len(document_chunks)}")

                    # Checks against local docs if there are changes or new docs
                    (
                        has_changes,
                        new_or_changed_chunks,
                    ) = data_source.preprocessor.compare_chunks(data_source, document_chunks)
                    # If there are changes or new docs, delete existing local files and write new files
                    if not has_changes:
                        self.log.info(f"Skipping data_source: no new data found for {data_source.data_source_name}")
                        break
                    self.log.info(f"Found {len(new_or_changed_chunks)} new or changed documents")
                    (
                        text_chunks,
                        document_chunks,
                    ) = data_source.preprocessor.create_text_chunks(data_source, document_chunks)
                    self.log.info(f"Total document chunks after final check: {len(document_chunks)}")

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
                            index_resource_stats.get("namespaces", {}).get(self.deployment_name, {}).get("vector_count", 0)
                        )
                        self.log.info(
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

                    self.log.info(f"Upserting {len(vectors_to_upsert)} vectors")
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
                        index_resource_stats.get("namespaces", {}).get(self.deployment_name, {}).get("vector_count", 0)
                    )
                    self.log.info(
                        f"Indexing complete for: {data_source.data_source_name}\nPrevious vector count: {existing_resource_vector_count}\nNew vector count: {new_resource_vector_count}\n"
                    )
                    # self.log.info(f'Post-upsert index stats: {index_resource_stats}\n')

                    data_source.preprocessor.write_chunks(data_source, document_chunks)

                    # If completed successfully, break the retry loop
                    break

                except Exception as error:
                    error_info = traceback.format_exc()
                    self.log.info(f"An error occurred: {error}\n{error_info}")
                    if i < retry_count - 1:  # i is zero indexed
                        continue  # this will start the next iteration of loop thus retrying your code block
                    else:
                        raise  # if exception in the last retry then raise it.

        self.log.info(f"Final index stats: {self.vectorstore.describe_index_stats()}")

    def ingest_from_ui(self, components: Dict[str, Any], *values):
        ui_state = {k: v for k, v in zip(components.keys(), values)}
        data_domain = ui_state.get("data_domain_drp", None)
        data_source = ui_state.get("data_source_drp", None)
        url = ui_state.get("url_textbox", None)
        preset = ui_state.get("source_preset", None)
        # get data domain
        # get data source, if it doesn't exist create it
        # if use custom check box is not clicked
        # get source preset

        documents_list = []
        for data_source in data_domain.data_sources:
            documents_iterator = self.doc_loading_service.load(data_source)
            if documents_iterator is not None:
                try:
                    documents_list = list(documents_iterator)
                except TypeError:
                    print(f"Error: Object {documents_iterator} is not iterable")
            else:
                print("Error: documents_iterator is None")
            if documents_list:
                self.database_service.write_documents_to_database(documents_list, data_domain, data_source)
                return documents_list
