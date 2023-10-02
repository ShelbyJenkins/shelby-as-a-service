import os

import modules.text_processing.text as TextProcess
import yaml


def create_openai_prompt(query: str, prompt_template: str, documents=None) -> list:
    document_string = create_document_string(documents)
    if document_string:
        user_content = "Documents: " + document_string + " Query: " + query
    else:
        user_content = "Query: " + query

    return [
        {"role": "system", "content": prompt_template},
        {"role": "user", "content": user_content},
    ]


def create_document_string(documents=None):
    if documents is None:
        return None

    if isinstance(documents, str):
        return TextProcess.clean_text_content(documents)

    content_strs = []

    for i, doc in enumerate(documents):
        if document_number := getattr(doc, "doc_num"):
            doc_num = document_number
        elif document_number := doc.get("doc_num"):
            doc_num = document_number
        else:
            doc_num = i
        document_content = TextProcess.get_document_content(doc)
        document_content = TextProcess.clean_text_content(document_content)

        content_strs.append(f"{document_content} doc_num: [{doc_num}]")

    return " ".join(content_strs)


def load_prompt_template(default_prompt_template_path, user_prompt_template_path=None):
    if user_prompt_template_path:
        template_path = user_prompt_template_path
    else:
        template_path = default_prompt_template_path
    with open(
        os.path.join("shelby_as_a_service/modules/prompt_templates/", template_path),
        "r",
        encoding="utf-8",
    ) as stream:
        # Load the YAML data and print the result
        return yaml.safe_load(stream)
