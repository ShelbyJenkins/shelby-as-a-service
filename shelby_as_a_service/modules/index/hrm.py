import modules.index.data_source_loaders as loaders


class DataModels:
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
            self.scraper = loaders.GitbookLoader(
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
