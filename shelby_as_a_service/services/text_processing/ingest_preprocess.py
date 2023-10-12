class CEQPreprocess:
    def __init__(self, data_source_config):
        self.index_agent = data_source_config.index_agent
        self.config = data_source_config.index_agent.config
        self.data_source_config = data_source_config
        self.print_and_log = self.index_agent.log.print_and_log
        self.tiktoken_encoding_model = self.config.index_tiktoken_encoding_model

        self.tiktoken_len = TextProcessing.tiktoken_len

        self.dfs_splitter = DFSTextSplitter(
            goal_length=self.config.index_text_splitter_goal_length,
            overlap_percent=self.config.index_text_splitter_overlap_percent,
            print_and_log=self.index_agent.log.print_and_log,
        )

    def run(self, documents) -> []:
        processed_document_chunks = []
        processed_text_chunks = []

        for i, doc in enumerate(documents):
            # If no doc title use the url and the resource type
            if not doc.metadata.get("title"):
                parsed_url = urlparse(doc.metadata.get("loc"))
                _, tail = os.path.split(parsed_url.path)
                # Strip anything with "." like ".html"
                root, _ = os.path.splitext(tail)
                doc.metadata[
                    "title"
                ] = f"{self.data_source_config.data_source_name}: {root}"

            # Remove bad chars and extra whitespace chars
            doc.page_content = TextProcessing.strip_excess_whitespace(doc.page_content)
            doc.metadata["title"] = TextProcessing.strip_excess_whitespace(
                doc.metadata["title"]
            )

            self.print_and_log(f"Processing: {doc.metadata['title']}")

            if (
                self.tiktoken_len(doc.page_content)
                < self.data_source_config.config.index_preprocessor_min_length
            ):
                self.print_and_log(
                    f"🔴 Skipping doc because content length: {self.tiktoken_len(doc.page_content)} is shorter than minimum: { self.data_source_config.config.index_preprocessor_min_length}"
                )
                continue

            text_chunks = self.dfs_splitter.split_text(doc.page_content)
            if text_chunks is None:
                self.print_and_log("🔴 Something went wrong with the text splitter.")
                continue
            # If it's not a list, wrap it inside a list
            if not isinstance(text_chunks, list):
                text_chunks = [text_chunks]

            token_counts = [self.tiktoken_len(chunk) for chunk in text_chunks]
            self.print_and_log(
                f"🟢 Doc split into {len(text_chunks)} of averge length {int(sum(token_counts) / len(text_chunks))}"
            )

            for text_chunk in text_chunks:
                document_chunk, text_chunk = self.append_metadata(text_chunk, doc)
                processed_document_chunks.append(document_chunk)
                processed_text_chunks.append(text_chunk.lower())

        self.print_and_log(f"Total docs: {len(documents)}")
        self.print_and_log(f"Total chunks: {len(processed_document_chunks)}")
        if not processed_document_chunks:
            return
        token_counts = [self.tiktoken_len(chunk) for chunk in processed_text_chunks]
        self.print_and_log(f"Min: {min(token_counts)}")
        self.print_and_log(f"Avg: {int(sum(token_counts) / len(token_counts))}")
        self.print_and_log(f"Max: {max(token_counts)}")
        self.print_and_log(f"Total tokens: {int(sum(token_counts))}")

        return processed_document_chunks

    def append_metadata(self, text_chunk, page):
        # Document chunks are the metadata uploaded to vectorstore
        document_chunk = {
            "content": text_chunk,
            "url": page.metadata["source"].strip(),
            "title": page.metadata["title"],
            "data_domain_name": self.data_source_config.data_domain_name,
            "data_source_name": self.data_source_config.data_source_name,
            "target_type": self.data_source_config.target_type,
            "doc_type": self.data_source_config.doc_type,
        }
        # Text chunks here are used to create embeddings
        text_chunk = f"{text_chunk} title: {page.metadata['title']}"

        return document_chunk, text_chunk

    def compare_chunks(self, data_source, document_chunks):
        folder_path = f"{self.index_agent.index_dir}/outputs/{data_source.data_domain_name}/{data_source.data_source_name}"
        # Create the directory if it does not exist
        os.makedirs(folder_path, exist_ok=True)
        existing_files = os.listdir(folder_path)
        has_changes = False
        # This will keep track of the counts for each title
        title_counter = {}
        # This will hold the titles of new or different chunks
        new_or_changed_chunks = []
        for document_chunk in document_chunks:
            sanitized_title = re.sub(r"\W+", "_", document_chunk["title"])
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            # if (
            #     self.tiktoken_len(text_chunk)
            #     > self.config.index_text_splitter_max_length
            # ):
            #     continue
            # Check if we've seen this title before, if not initialize to 0
            if sanitized_title not in title_counter:
                title_counter[sanitized_title] = 0
            file_name = f"{sanitized_title}_{title_counter[sanitized_title]}.json"
            # Increment the counter for this title
            title_counter[sanitized_title] += 1
            if file_name not in existing_files:
                has_changes = True
                new_or_changed_chunks.append(document_chunk["title"])
            else:
                existing_file_path = os.path.join(folder_path, file_name)
                with open(existing_file_path, "r") as f:
                    existing_data = json.load(f)
                    if existing_data != document_chunk:
                        has_changes = True
                        new_or_changed_chunks.append(document_chunk["title"])

        return has_changes, new_or_changed_chunks

    def create_text_chunks(self, data_source, document_chunks):
        checked_document_chunks = []
        checked_text_chunks = []
        # This will keep track of the counts for each title
        title_counter = {}
        for document_chunk in document_chunks:
            sanitized_title = re.sub(r"\W+", "_", document_chunk["title"])
            # Check if we've seen this title before, if not initialize to 0
            if sanitized_title not in title_counter:
                title_counter[sanitized_title] = 0
            # Increment the counter for this title
            title_counter[sanitized_title] += 1
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            # if (
            #     self.tiktoken_len(text_chunk)
            #     > self.config.index_text_splitter_max_length
            # ):
            #     continue
            checked_document_chunks.append(document_chunk)
            checked_text_chunks.append(text_chunk.lower())

        return checked_text_chunks, checked_document_chunks

    def write_chunks(self, data_source, document_chunks):
        folder_path = f"{self.index_agent.index_dir}/outputs/{data_source.data_domain_name}/{data_source.data_source_name}"
        # Clear the folder first
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
        # This will keep track of the counts for each title
        title_counter = {}
        for document_chunk in document_chunks:
            sanitized_title = re.sub(r"\W+", "_", document_chunk["title"])
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            # if (
            #     self.tiktoken_len(text_chunk)
            #     > self.config.index_text_splitter_max_length
            # ):
            #     continue
            # Check if we've seen this title before, if not initialize to 0
            if sanitized_title not in title_counter:
                title_counter[sanitized_title] = 0
            file_name = f"{sanitized_title}_{title_counter[sanitized_title]}.json"
            # Increment the counter for this title
            title_counter[sanitized_title] += 1
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(document_chunk, f, indent=4)
