    def load_texts(self):
        """Load text and JSON files and structure them in the desired format."""
        text_documents = []
        allowed_extensions = [".txt", ".json"]

        for filename in os.listdir(self.data_source_config.target_url):
            file_extension = os.path.splitext(filename)[1]

            if file_extension not in allowed_extensions:
                # Uncomment the line below if you wish to log unsupported file formats
                # self.data_source_config.index_agent.log_agent.info(f"Unsupported file format: {filename}")
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
                        "title": title,
                    }
                    document = Document(page_content=content, metadata=document_metadata)
                elif file_extension == ".json":
                    content = json.load(file)  # Now content is a dictionary

                    # You might want to adapt the following based on how you wish to represent JSON content
                    document_metadata = {
                        "loc": file_path,
                        "source": file_path,
                        "title": title,
                    }
                    document = Document(page_content=content["content"], metadata=document_metadata)
                text_documents.append(document)

        return text_documents
