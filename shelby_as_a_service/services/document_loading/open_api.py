# class OpenAPILoader(DocLoadingBase):
#     def __init__(self, data_source_config: DataSourceConfig):
#         self.index_agent = data_source_config.index_agent
#         self.config = data_source_config
#         self.data_source_config = data_source_config

#     def load(self):
#         open_api_specs = self.load_spec()

#         return open_api_specs

#     def load_spec(self):
#         """Load YAML or JSON files."""
#         open_api_specs = []
#         file_extension = None
#         for filename in os.listdir(self.data_source_config.target_url):
#             if file_extension is None:
#                 if filename.endswith(".yaml"):
#                     file_extension = ".yaml"
#                 elif filename.endswith(".json"):
#                     file_extension = ".json"
#                 else:
#                     # self.data_source_config.index_agent.log_agent.info(f"Unsupported file format: {filename}")
#                     continue
#             elif not filename.endswith(file_extension):
#                 # self.data_source_config.index_agent.log_agent.info(f"Inconsistent file formats in directory: {filename}")
#                 continue
#             file_path = os.path.join(self.data_source_config.target_url, filename)
#             with open(file_path, "r") as file:
#                 if file_extension == ".yaml":
#                     open_api_specs.append(yaml.safe_load(file))
#                 elif file_extension == ".json":
#                     open_api_specs.append(json.load(file))

#         return open_api_specs

# class LoadTextFromFile(ServiceBase):
#     def __init__(self, data_source_config):
#         self.config = data_source_config
#         self.data_source_config = data_source_config

#     def load(self):
#         text_documents = self.load_texts()
#         return text_documents

# def load_texts(self):
#     """Load text files and structure them in the desired format."""
#     text_documents = []
#     file_extension = ".txt"
#     for filename in os.listdir(self.data_source_config.target_url):
#         if not filename.endswith(file_extension):
#             # Uncomment the line below if you wish to log unsupported file formats
#             # self.data_source_config.index_agent.log_agent.info(f"Unsupported file format: {filename}")
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
