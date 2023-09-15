import os, shutil
import json, yaml
import string, re
from urllib.parse import urlparse
from services.data_processing_service import TextProcessing


class OpenAPIMinifierService:
    def __init__(self, data_source_config):
        self.index_agent = data_source_config.index_agent
        self.config = data_source_config.index_agent.config
        self.data_source_config = data_source_config

        self.api_url_format = data_source_config.api_url_format

        self.tiktoken_len = TextProcessing.tiktoken_len

        self.operationID_counter = 0

        # Decide what fields you want to keep in the documents
        self.keys_to_keep = {
            # Root level keys to populate
            "parameters": True,
            "good_responses": True,
            "bad_responses": False,
            "request_bodies": True,
            "schemas": True,
            "endpoint_descriptions": True,
            "endpoint_summaries": True,
            # Keys to exclude
            "enums": False,
            "nested_descriptions": True,
            "examples": False,
            "tag_summaries": False,
            "deprecated": False,
        }
        self.methods_to_handle = {"get", "post", "patch", "delete"}
        # Saves tokens be abbreviating in a way understood by the LLM
        # Must be lowercase
        self.key_abbreviations = {
            "operationid": "opid",
            "parameters": "params",
            "requestbody": "reqBody",
            "properties": "props",
            "schemaname": "schName",
            "description": "desc",
            "summary": "sum",
            "string": "str",
            "number": "num",
            "object": "obj",
            "boolean": "bool",
            "array": "arr",
            "object": "obj",
        }

        self.key_abbreviations_enabled = True

    def run(self, open_api_specs):
        # Merge all specs and save a copy locally
        full_open_api_specs = self.create_full_spec(open_api_specs)

        # Create list of processed and parsed individual endpoints
        minified_endpoints = self.minify(full_open_api_specs)

        # Sort alphabetically by tag and then operation_id
        minified_endpoints = sorted(
            minified_endpoints, key=lambda x: (x["tag"], x["operation_id"])
        )

        minified_endpoints = self.create_endpoint_documents(
            minified_endpoints, full_open_api_specs
        )

        self.create_key_point_guide(minified_endpoints)

        return minified_endpoints

    def create_full_spec(self, open_api_specs):
        folder_path = f"{self.index_agent.index_dir}/outputs/{self.data_source_config.data_domain_name}/open_api_spec/full_spec"
        # Ensure output directory exists
        os.makedirs(folder_path, exist_ok=True)
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
        # Define output file path
        output_file_path = os.path.join(
            folder_path,
            f"{self.data_source_config.data_domain_name}_open_api_spec.json",
        )

        merged_open_api_spec = None

        for open_api_spec in open_api_specs:
            if merged_open_api_spec is None:
                merged_open_api_spec = open_api_spec
            else:
                # Merging the 'paths' assuming there are no overlapping paths
                merged_open_api_spec["paths"].update(open_api_spec["paths"])

                # Also merge 'components' if they exist
                if "components" in open_api_spec:
                    if "components" not in merged_open_api_spec:
                        merged_open_api_spec["components"] = {}
                    for component_type, components in open_api_spec[
                        "components"
                    ].items():
                        if component_type not in merged_open_api_spec["components"]:
                            merged_open_api_spec["components"][component_type] = {}
                        merged_open_api_spec["components"][component_type].update(
                            components
                        )

        merged_open_api_spec["paths"] = dict(
            sorted(merged_open_api_spec["paths"].items())
        )
        if "components" in merged_open_api_spec:
            for component_type in merged_open_api_spec["components"]:
                merged_open_api_spec["components"][component_type] = dict(
                    sorted(merged_open_api_spec["components"][component_type].items())
                )

        with open(output_file_path, "w") as output_file:
            json.dump(merged_open_api_spec, output_file, indent=4)

        return merged_open_api_spec

    def minify(self, open_api_spec):
        server_url = open_api_spec["servers"][0][
            "url"
        ]  # Fetch the server URL from the open_api_spec specification
        # server_url = urlparse(server_url)

        minified_endpoints = []
        with open(
            os.path.join(
                self.index_agent.prompt_template_path,
                "open_api_minifier_agent_endpoint_prompt_template.yaml",
            ),
            "r",
        ) as yaml_file:
            # Load the YAML data and print the result
            yaml_content = yaml.safe_load(yaml_file)

        prompt_template = yaml_content.get("prompt_template")

        for path, methods in open_api_spec["paths"].items():
            for method, endpoint in methods.items():
                if method not in self.methods_to_handle:
                    continue
                if (
                    endpoint.get("deprecated", False)
                    and not self.keys_to_keep["deprecated"]
                ):
                    continue

                # Adds schema to each endpoint
                if self.keys_to_keep["schemas"]:
                    extracted_endpoint_data = self.resolve_refs(open_api_spec, endpoint)
                else:
                    extracted_endpoint_data = endpoint

                # Populate output list with desired keys
                extracted_endpoint_data = self.populate_keys(
                    extracted_endpoint_data, path
                )

                # If key == None or key == ''
                extracted_endpoint_data = self.remove_empty_keys(
                    extracted_endpoint_data
                )

                # Remove unwanted keys
                extracted_endpoint_data = self.remove_unnecessary_keys(
                    extracted_endpoint_data
                )

                # Flattens to remove nested objects where the dict has only one key
                extracted_endpoint_data = self.flatten_endpoint(extracted_endpoint_data)

                if self.key_abbreviations_enabled:
                    # Replace common keys with abbreviations and sets all text to lower case
                    extracted_endpoint_data = self.abbreviate(
                        extracted_endpoint_data, self.key_abbreviations
                    )

                # Get the tag of the current endpoint
                tags = endpoint.get("tags", [])
                tag = tags[0] if tags else "default"

                operation_id = endpoint.get("operationId", "")
                processed_endpoint = self.write_dict_to_text(extracted_endpoint_data)
                content_string = f"{prompt_template} operationId: {operation_id} path: {server_url}{path} content: {processed_endpoint}"

                api_url = self.api_url_format.format(tag=tag, operationId=operation_id)

                endpoint_dict = {
                    "tag": tag,
                    "content": content_string,
                    "operation_id": operation_id,
                    "url": api_url,
                    "server_url": f"{server_url}{path}",
                    "content": content_string,
                }

                minified_endpoints.append(endpoint_dict)

        return minified_endpoints

    def resolve_refs(self, open_api_spec, endpoint):
        if isinstance(endpoint, dict):
            new_endpoint = {}
            for key, value in endpoint.items():
                if key == "$ref":
                    ref_path = value.split("/")[1:]
                    ref_object = open_api_spec
                    for p in ref_path:
                        ref_object = ref_object.get(p, {})

                    # Recursively resolve references inside the ref_object
                    ref_object = self.resolve_refs(open_api_spec, ref_object)

                    # Use the last part of the reference path as key
                    new_key = ref_path[-1]
                    new_endpoint[new_key] = ref_object
                else:
                    # Recursively search in nested dictionaries
                    new_endpoint[key] = self.resolve_refs(open_api_spec, value)
            return new_endpoint

        elif isinstance(endpoint, list):
            # Recursively search in lists
            return [self.resolve_refs(open_api_spec, item) for item in endpoint]

        else:
            # Base case: return the endpoint as is if it's neither a dictionary nor a list
            return endpoint

    def populate_keys(self, endpoint, path):
        # Gets the main keys from the specs
        extracted_endpoint_data = {}
        # extracted_endpoint_data['path'] = path
        # extracted_endpoint_data['operationId'] = endpoint.get('operationId')

        if self.keys_to_keep["parameters"]:
            extracted_endpoint_data["parameters"] = endpoint.get("parameters")

        if self.keys_to_keep["endpoint_summaries"]:
            extracted_endpoint_data["summary"] = endpoint.get("summary")

        if self.keys_to_keep["endpoint_descriptions"]:
            extracted_endpoint_data["description"] = endpoint.get("description")

        if self.keys_to_keep["request_bodies"]:
            extracted_endpoint_data["requestBody"] = endpoint.get("requestBody")

        if self.keys_to_keep["good_responses"] or self.keys_to_keep["bad_responses"]:
            extracted_endpoint_data["responses"] = {}

        if self.keys_to_keep["good_responses"]:
            if "responses" in endpoint and "200" in endpoint["responses"]:
                extracted_endpoint_data["responses"]["200"] = endpoint["responses"].get(
                    "200"
                )

        if self.keys_to_keep["bad_responses"]:
            if "responses" in endpoint:
                # Loop through all the responses
                for status_code, response in endpoint["responses"].items():
                    # Check if status_code starts with '4' or '5' (4xx or 5xx)
                    if (
                        status_code.startswith("4")
                        or status_code.startswith("5")
                        or "default" in status_code
                    ):
                        # Extract the schema or other relevant information from the response
                        bad_response_content = response
                        if bad_response_content is not None:
                            extracted_endpoint_data["responses"][
                                f"{status_code}"
                            ] = bad_response_content

        return extracted_endpoint_data

    def remove_empty_keys(self, endpoint):
        if isinstance(endpoint, dict):
            # Create a new dictionary without empty keys
            new_endpoint = {}
            for key, value in endpoint.items():
                if value is not None and value != "":
                    # Recursively call the function for nested dictionaries
                    cleaned_value = self.remove_empty_keys(value)
                    new_endpoint[key] = cleaned_value
            return new_endpoint
        elif isinstance(endpoint, list):
            # Recursively call the function for elements in a list
            return [self.remove_empty_keys(item) for item in endpoint]
        else:
            # Return the endpoint if it's not a dictionary or a list
            return endpoint

    def remove_unnecessary_keys(self, endpoint):
        # Stack for storing references to nested dictionaries/lists and their parent keys
        stack = [(endpoint, [])]

        # Continue until there is no more data to process
        while stack:
            current_data, parent_keys = stack.pop()

            # If current_data is a dictionary
            if isinstance(current_data, dict):
                # Iterate over a copy of the keys, as we may modify the dictionary during iteration
                for k in list(current_data.keys()):
                    # Check if this key should be removed based on settings and context
                    if k == "example" and not self.keys_to_keep["examples"]:
                        del current_data[k]
                    if k == "enum" and not self.keys_to_keep["enums"]:
                        del current_data[k]
                    elif (
                        k == "description"
                        and len(parent_keys) > 0
                        and not self.keys_to_keep["nested_descriptions"]
                    ):
                        del current_data[k]
                    # Otherwise, if the value is a dictionary or a list, add it to the stack for further processing
                    # Check if the key still exists before accessing it
                    if k in current_data and isinstance(current_data[k], (dict, list)):
                        stack.append((current_data[k], parent_keys + [k]))

            # If current_data is a list
            elif isinstance(current_data, list):
                # Add each item to the stack for further processing
                for item in current_data:
                    if isinstance(item, (dict, list)):
                        stack.append((item, parent_keys + ["list"]))

        return endpoint

    def flatten_endpoint(self, endpoint):
        if not isinstance(endpoint, dict):
            return endpoint

        flattened_endpoint = {}

        # Define the set of keys to keep without unwrapping
        keep_keys = {"responses", "default", "200"}

        for key, value in endpoint.items():
            if isinstance(value, dict):
                # Check if the dictionary has any of the keys that need to be kept
                if key in keep_keys or (
                    isinstance(key, str)
                    and (key.startswith("5") or key.startswith("4"))
                ):
                    # Keep the inner dictionaries but under the current key
                    flattened_endpoint[key] = self.flatten_endpoint(value)
                else:
                    # Keep unwrapping single-key dictionaries
                    while isinstance(value, dict) and len(value) == 1:
                        key, value = next(iter(value.items()))
                    # Recursively flatten the resulting value
                    flattened_endpoint[key] = self.flatten_endpoint(value)
            else:
                # If the value is not a dictionary, keep it as is
                flattened_endpoint[key] = value

        return flattened_endpoint

    def abbreviate(self, data, abbreviations):
        if isinstance(data, dict):
            # Lowercase keys, apply abbreviations and recursively process values
            return {
                abbreviations.get(key.lower(), key.lower()): self.abbreviate(
                    abbreviations.get(str(value).lower(), value), abbreviations
                )
                for key, value in data.items()
            }
        elif isinstance(data, list):
            # Recursively process list items
            return [self.abbreviate(item, abbreviations) for item in data]
        elif isinstance(data, str):
            # If the data is a string, convert it to lowercase and replace if abbreviation exists
            return abbreviations.get(data.lower(), data.lower())
        else:
            # Return data unchanged if it's not a dict, list or string
            return data

    def create_endpoint_documents(self, minified_endpoints, open_api_spec):
        tag_summaries = self.get_tag_summaries(minified_endpoints, open_api_spec)

        for endpoint in minified_endpoints:
            tag = endpoint.get("tag") or "default"

            # Get the corresponding tag summary and number
            tag_summary_list = [
                summary for summary in tag_summaries if summary["name"] == tag
            ]
            tag_summary = tag_summary_list[0]["summary"] if tag_summary_list else ""
            tag_number = tag_summary_list[0]["tag_number"] if tag_summary_list else 0

            endpoint["tag_summary"] = tag_summary
            endpoint["tag_number"] = tag_number

            endpoint["data_domain_name"] = self.data_source_config.data_domain_name
            endpoint["data_source_name"] = self.data_source_config.data_source_name
            endpoint["target_type"] = self.data_source_config.target_type
            endpoint["doc_type"] = self.data_source_config.doc_type

            endpoint["doc_number"] = self.operationID_counter

            parsed = urlparse(endpoint["server_url"])
            if parsed.scheme and parsed.netloc:
                # Strip away the https:// and main TLD portion
                endpoint["title"] = re.sub(
                    r"https?://[^/]+/", "", endpoint["server_url"]
                )

            else:
                endpoint["title"] = {endpoint["server_url"]}

            filename = f"{tag_number}_{endpoint['tag']}_{endpoint['operation_id']}_{self.operationID_counter}"
            endpoint["filename"] = filename

            self.operationID_counter += 1

        return minified_endpoints

    def get_tag_summaries(self, minified_endpoints, open_api_spec):
        tag_summaries = []

        # Handle root level tags
        root_tags = open_api_spec.get("tags")
        if root_tags:
            for tag in root_tags:
                if tag not in [t["name"] for t in tag_summaries]:
                    name = tag.get("name")
                    summary = tag.get("description")
                    if name and summary:
                        tag_summaries.append(
                            {"name": name, "summary": self.write_dict_to_text(summary)}
                        )
                    else:
                        tag_summaries.append({"name": name, "summary": ""})

        for endpoint in minified_endpoints:
            tag = endpoint.get("tag") or "default"
            # Only add tag if it is not already in tag_summaries
            if tag not in [t["name"] for t in tag_summaries]:
                tag_summaries.append({"name": tag, "summary": ""})

        tag_summaries = sorted(tag_summaries, key=lambda x: (x["name"]))

        for i, tag in enumerate(tag_summaries):
            tag["tag_number"] = i

        return tag_summaries

    def write_dict_to_text(self, data):
        def remove_html_tags_and_punctuation(input_str):
            # Strip HTML tags
            no_html_str = re.sub("<.*?>", "", input_str)
            # Define the characters that should be considered as punctuation
            modified_punctuation = set(string.punctuation) - {"/", "#"}
            # Remove punctuation characters
            return (
                "".join(ch for ch in no_html_str if ch not in modified_punctuation)
                .lower()
                .strip()
            )

        # List to accumulate the formatted text parts
        formatted_text_parts = []

        # Check if data is a dictionary
        if isinstance(data, dict):
            # Iterate over items in the dictionary
            for key, value in data.items():
                # Remove HTML tags and punctuation from key
                key = remove_html_tags_and_punctuation(key)

                # Depending on the data type, write the content
                if isinstance(value, (dict, list)):
                    # Append the key followed by its sub-elements
                    formatted_text_parts.append(key)
                    formatted_text_parts.append(self.write_dict_to_text(value))
                else:
                    # Remove HTML tags and punctuation from value
                    value = remove_html_tags_and_punctuation(str(value))
                    # Append the key-value pair
                    formatted_text_parts.append(f"{key} {value}")
        # Check if data is a list
        elif isinstance(data, list):
            # Append each element in the list
            for item in data:
                formatted_text_parts.append(self.write_dict_to_text(item))
        # If data is a string or other type
        else:
            # Remove HTML tags and punctuation from data
            data = remove_html_tags_and_punctuation(str(data))
            # Append the data directly
            formatted_text_parts.append(data)

        # Join the formatted text parts with a single newline character
        # but filter out any empty strings before joining
        return "\n".join(filter(lambda x: x.strip(), formatted_text_parts))

    def create_key_point_guide(self, minified_endpoints):
        with open(
            os.path.join(
                self.index_agent.prompt_template_path,
                "open_api_minifier_agent_keypoint_prompt_template.yaml",
            ),
            "r",
        ) as yaml_file:
            # Load the YAML data and print the result
            yaml_content = yaml.safe_load(yaml_file)
        prompt_template = yaml_content.get("prompt_template")
        folder_path = f"{self.index_agent.index_dir}/outputs/{self.data_source_config.data_domain_name}/open_api_spec/keypoint"
        # Ensure output directory exists
        os.makedirs(folder_path, exist_ok=True)
        # Define output file path
        output_file_path = f"{folder_path}/keypoint_guide_file.txt"

        output_string = f"{prompt_template}\n"
        current_tag_number = ""
        tag_string = ""

        for endpoint in minified_endpoints:
            if current_tag_number != endpoint.get("tag_number"):
                # New tag
                if tag_string != "":
                    output_string += f"{tag_string}\n"
                    tag_string = ""
                current_tag_number = endpoint.get("tag_number")
                # If we're adding tag descriptions and they exist they're added here.
                tag_summary = endpoint.get("tag_summary")
                if (
                    self.keys_to_keep["tag_summaries"]
                    and tag_summary is not None
                    and tag_summary != ""
                ):
                    tag_string = f"{endpoint.get('tag')}-{tag_summary}\n"
                else:
                    tag_string = f"{endpoint.get('tag')}-\n"

            doc_number = endpoint.get("doc_number")
            operation_id = endpoint.get("operation_id")

            tag_string += f"{operation_id}={doc_number}!"

        output_string += f"{tag_string}\n"

        # self.log_agent.print_and_log(f'keypoint file token count: {self.tiktoken_len(output_string)}')
        # Write sorted info_strings to the output file
        with open(output_file_path, "w") as output_file:
            output_file.write(output_string)

    def compare_chunks(self, data_source, document_chunks):
        folder_path = f"{self.index_agent.index_dir}/outputs/{self.data_source_config.data_domain_name}/open_api_spec/endpoints"
        # Create the directory if it does not exist
        os.makedirs(folder_path, exist_ok=True)
        existing_files = os.listdir(folder_path)
        has_changes = False
        # This will hold the titles of new or different chunks
        new_or_changed_chunks = []
        for document_chunk in document_chunks:
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            if (
                self.tiktoken_len(text_chunk)
                > self.config.index_text_splitter_max_length
            ):
                continue
            file_name = f"{document_chunk['title']}.txt"
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
        for document_chunk in document_chunks:
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # If chunk too big
            if (
                self.tiktoken_len(text_chunk)
                > self.config.index_text_splitter_max_length
            ):
                continue
            checked_document_chunks.append(document_chunk)
            checked_text_chunks.append(text_chunk.lower())

        return checked_text_chunks, checked_document_chunks

    def write_chunks(self, data_source, document_chunks):
        folder_path = f"{self.index_agent.index_dir}/outputs/{self.data_source_config.data_domain_name}/open_api_spec/endpoints"
        # Clear the folder first
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
        for document_chunk in document_chunks:
            text_chunk = f"{document_chunk['content']} title: {document_chunk['title']}"
            # Skip overly long chunks
            if (
                self.tiktoken_len(text_chunk)
                > self.config.index_text_splitter_max_length
            ):
                continue
            if "filename" in document_chunk:
                # Do something if 'filename' exists in the dictionary
                file_name = document_chunk["filename"]
                # Your code here
            else:
                # Handle the case where 'filename' does not exist
                file_name = document_chunk["title"]

            file_path = f"{folder_path}/{file_name}.txt"
            with open(file_path, "w") as f:
                json.dump(document_chunk, f, indent=4)
