import os, traceback
from typing import Iterator
import yaml, json
import pinecone
from langchain.schema import Document
from langchain.document_loaders import GitbookLoader, SitemapLoader, RecursiveUrlLoader
from langchain.embeddings import OpenAIEmbeddings
from bs4 import BeautifulSoup

from modules.utils.log_service import Logger
from shelby_as_a_service.modules.app_base import AppBase
from modules.data_processing.open_api_minifier_service import OpenAPIMinifierService
from modules.data_processing.data_processing_service import CEQTextPreProcessor


class IngestService(AppBase):
    
    model_ = IngestServiceModel()
    required_services_ = []
    
    def __init__(self):
        super().__init__()
        
        # self.deployment_name = deployment_instance.deployment_name
        # self.deployment = deployment_instance
        # self.config = service_model
        # self.index_env = self.config.index_env
        # self.index_name = self.config.index_name
        
        # self.log = Logger(
        #     self.deployment_name,
        #     f"{self.deployment_name}_index_agent",
        #     f"{self.deployment_name}_index_agent.md",
        #     level="INFO",
        # )
        
        # self.secrets = deployment_instance.secrets
        # if not self.deployment.check_secrets(IngestServiceModel.secrets_):
        #     return 
        
        # self.prompt_template_path = "shelby_as_a_service/prompt_templates"
        # self.index_dir = f"deployments/{self.deployment_name}/index"
        # # Loads data sources from file
        # with open(
        #     f"deployments/{self.deployment_name}/index_description.yaml",
        #     "r",
        #     encoding="utf-8",
        # ) as stream:
        #     self.index_description_file = yaml.safe_load(stream)

        # if self.index_description_file["index_name"] != self.index_name:
        #     # raise ValueError(
        #     #     "Index name in index_description.yaml does not match index from deployment.env!"
        #     # )
        #     self.index_name = self.index_description_file["index_name"]

        # pinecone.init(
        #     environment=self.index_env,
        #     api_key=self.secrets["pinecone_api_key"],
        # )

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

    def ingest_docs(self):
        self.log.print_and_log(
            f"Initial index stats: {self.vectorstore.describe_index_stats()}\n"
        )

        for data_source in self.enabled_data_sources:
            # Retries if there is an error
            retry_count = 2
            for i in range(retry_count):
                try:
                    self.log.print_and_log(
                        f"-----Now indexing: {data_source.data_source_name}\n"
                    )
                    # Get count of vectors in index matching the "resource" metadata field
                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={
                            "data_source_name": {"$eq": data_source.data_source_name}
                        }
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
                    self.log.print_and_log(
                        f"Total documents loaded for indexing: {len(documents)}"
                    )

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
                    ) = data_source.preprocessor.compare_chunks(
                        data_source, document_chunks
                    )
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
                    ) = data_source.preprocessor.create_text_chunks(
                        data_source, document_chunks
                    )
                    self.log.print_and_log(
                        f"Total document chunks after final check: {len(document_chunks)}"
                    )

                    # Get dense_embeddings
                    dense_embeddings = data_source.embedding_retriever.embed_documents(
                        text_chunks
                    )

                    # If the "resource" already has vectors delete the existing vectors before upserting new vectors
                    # We have to delete all because the difficulty in specifying specific documents in pinecone
                    if existing_resource_vector_count != 0:
                        self._clear_data_source(data_source)
                        index_resource_stats = (
                            data_source.vectorstore.describe_index_stats(
                                filter={
                                    "data_source_name": {
                                        "$eq": data_source.data_source_name
                                    }
                                }
                            )
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

                    self.log.print_and_log(
                        f"Upserting {len(vectors_to_upsert)} vectors"
                    )
                    # data_source.vectorstore.upsert(
                    #     vectors=vectors_to_upsert,
                    #     namespace=self.deployment_name,
                    #     batch_size=self.config.index_vectorstore_upsert_batch_size,
                    #     show_progress=True,
                    # )

                    index_resource_stats = data_source.vectorstore.describe_index_stats(
                        filter={
                            "data_source_name": {"$eq": data_source.data_source_name}
                        }
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

        self.log.print_and_log(
            f"Final index stats: {self.vectorstore.describe_index_stats()}"
        )



class DataSourceConfig:
    ### DataSourceConfig loads all configs for all datasources ###

    def __init__(
        self,
        index_agent: IngestService,
        data_domain_name,
        domain_description,
        data_source_name,
        source,
    ):
        self.index_agent = index_agent
        self.vectorstore = index_agent.vectorstore
        self.config = index_agent.config
        self.log = index_agent.log

        # From document_sources.yaml
        self.data_domain_name: str = data_domain_name
        self.domain_description: str = domain_description
        self.data_source_name: str = data_source_name
        self.filter_url: str = source.get("filter_url")
        self.update_enabled: bool = source.get("update_enabled")
        self.load_all_paths: bool = source.get("load_all_paths")
        self.skip_paths: bool = source.get("skip_paths")
        self.target_url: str = source.get("target_url")
        self.target_type: str = source.get("target_type")
        self.doc_type: str = source.get("doc_type")
        self.api_url_format: str = source.get("api_url_format")

        # Check if any value is None
        attributes = [
            self.data_domain_name,
            self.data_source_name,
            self.update_enabled,
            self.target_url,
            self.target_type,
            self.doc_type,
        ]
        if not all(attr is not None and attr != "" for attr in attributes):
            raise ValueError("Some required fields are missing or have no value.")

        match self.target_type:
            case "gitbook":
                self.scraper = GitbookLoader(
                    web_page=self.target_url, load_all_paths=self.load_all_paths
                )
                self.content_type = "text"

            case "sitemap":
                # May need to change for specific websites
                def parse_content_by_id(content):
                    # Attempt to find element by 'content-container' ID
                    content_element = content.find(id="content-container")
                    if not content_element:
                        # If 'content-container' not found, attempt to find 'content'
                        content_element = content.find(id="content")
                    if not content_element:
                        # If neither found, return an empty string
                        return ""
                    # Find all elements with "visibility: hidden" style and class containing "toc"
                    unwanted_elements = content_element.select(
                        '[style*="visibility: hidden"], [class*="toc"]'
                    )
                    # Remove unwanted elements from content_element
                    for element in unwanted_elements:
                        element.decompose()
                    # Remove header tags
                    for header in content_element.find_all("header"):
                        header.decompose()
                    # Extract text from the remaining content
                    text = content_element.get_text(separator=" ")

                    return text

                self.scraper = SitemapLoader(
                    self.target_url,
                    filter_urls=[self.filter_url],
                    parsing_function=parse_content_by_id,
                )
                self.content_type = "text"

            case "generic":
                self.scraper = CustomScraper(self)
                self.content_type = "text"

            case "open_api_spec":
                self.scraper = OpenAPILoader(self)
                self.content_type = "open_api_spec"
                
            case "local_text":
                self.scraper = LoadTextFromFile(self)
                self.content_type = "text"

            case _:
                raise ValueError(f"Invalid target type: {self.target_type}")

        match self.content_type:
            case "text":
                self.preprocessor = CEQTextPreProcessor(self)
            case "open_api_spec":
                self.preprocessor = OpenAPIMinifierService(self)
            case _:
                raise ValueError("Invalid target type: should be text, html, or code.")

        self.embedding_retriever = OpenAIEmbeddings(
            model=self.config.index_embedding_model,
            embedding_ctx_length=self.config.index_embedding_max_chunk_size,
            openai_api_key=self.index_agent.secrets["openai_api_key"],
            chunk_size=self.config.index_embedding_batch_size,
            request_timeout=self.config.index_openai_timeout_seconds,
        )


class CustomScraper:
    ### CustomScraper is a generic web scraper ###

    def __init__(self, data_source_config: DataSourceConfig):
        self.data_source_config = data_source_config
        self.load_urls = RecursiveUrlLoader(
            url=self.data_source_config.target_url, extractor=self.custom_extractor
        )

    @staticmethod
    def custom_extractor(html_text: str) -> str:
        soup = BeautifulSoup(html_text, "html.parser")
        text_element = soup.find(id="content")
        if text_element:
            return text_element.get_text()
        return ""

    def load(self) -> Iterator[Document]:
        documents = self.load_urls.load()

        return [
            Document(page_content=doc.page_content, metadata=doc.metadata)
            for doc in documents
        ]


class OpenAPILoader:
    def __init__(self, data_source_config: DataSourceConfig):
        self.index_agent = data_source_config.index_agent
        self.config = data_source_config
        self.data_source_config = data_source_config

    def load(self):
        open_api_specs = self.load_spec()

        return open_api_specs

    def load_spec(self):
        """Load YAML or JSON files."""
        open_api_specs = []
        file_extension = None
        for filename in os.listdir(self.data_source_config.target_url):
            if file_extension is None:
                if filename.endswith(".yaml"):
                    file_extension = ".yaml"
                elif filename.endswith(".json"):
                    file_extension = ".json"
                else:
                    # self.data_source_config.index_agent.log_agent.print_and_log(f"Unsupported file format: {filename}")
                    continue
            elif not filename.endswith(file_extension):
                # self.data_source_config.index_agent.log_agent.print_and_log(f"Inconsistent file formats in directory: {filename}")
                continue
            file_path = os.path.join(self.data_source_config.target_url, filename)
            with open(file_path, "r") as file:
                if file_extension == ".yaml":
                    open_api_specs.append(yaml.safe_load(file))
                elif file_extension == ".json":
                    open_api_specs.append(json.load(file))

        return open_api_specs



class LoadTextFromFile:
    def __init__(self, data_source_config):
        self.config = data_source_config
        self.data_source_config = data_source_config

    def load(self):
        text_documents = self.load_texts()
        return text_documents

    # def load_texts(self):
    #     """Load text files and structure them in the desired format."""
    #     text_documents = []
    #     file_extension = ".txt"
    #     for filename in os.listdir(self.data_source_config.target_url):
    #         if not filename.endswith(file_extension):
    #             # Uncomment the line below if you wish to log unsupported file formats
    #             # self.data_source_config.index_agent.log_agent.print_and_log(f"Unsupported file format: {filename}")
    #             continue
            
    #         file_path = os.path.join(self.data_source_config.target_url, filename)
    #         title = os.path.splitext(filename)[0]
    #         with open(file_path, "r", encoding="utf-8") as file:
    #             document_metadata = {
    #                 "loc": file_path,
    #                 "source": file_path,
    #                 "title": title
    #             }
    #             document = Document(page_content=file.read(), metadata=document_metadata)
    #             text_documents.append(document)

    #     return text_documents




    def load_texts(self):
        """Load text and JSON files and structure them in the desired format."""
        text_documents = []
        allowed_extensions = [".txt", ".json"]

        for filename in os.listdir(self.data_source_config.target_url):
            file_extension = os.path.splitext(filename)[1]
            
            if file_extension not in allowed_extensions:
                # Uncomment the line below if you wish to log unsupported file formats
                # self.data_source_config.index_agent.log_agent.print_and_log(f"Unsupported file format: {filename}")
                continue

            file_path = os.path.join(self.data_source_config.target_url, filename)
            title = os.path.splitext(filename)[0]

            with open(file_path, "r", encoding="utf-8") as file:
                if file_extension == ".txt":
                    content = file.read()
                    # You might want to adapt the following based on how you wish to represent JSON content
                    document_metadata = {
                        "loc": file_path,
                        "source": file_path,
                        "title": title
                    }
                    document = Document(page_content=content, metadata=document_metadata)
                elif file_extension == ".json":
                    content = json.load(file)  # Now content is a dictionary
                    
                    # You might want to adapt the following based on how you wish to represent JSON content
                    document_metadata = {
                        "loc": file_path,
                        "source": file_path,
                        "title": title
                    }
                    document = Document(page_content=content['content'], metadata=document_metadata)
                text_documents.append(document)

        return text_documents



