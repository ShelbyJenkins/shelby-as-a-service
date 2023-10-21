from typing import Any

import services.text_processing.text as TextProcessing


def parse_retrieved_docs(
    retrieved_documents: list[dict], doc_max_tokens: float = 0, max_total_tokens: float = 0, docs_max_count: float = 0
) -> list[Any]:
    """
    Parses a list of retrieved documents, filtering them based on their token count and/or total token count,
    and optionally limiting the number of documents to retrieve.

    Args:
        retrieved_documents (list[dict]): A list of retrieved documents, each represented as a dictionary with at least
            a 'content' key containing the document text and a 'score' key containing the retrieval score.
        doc_max_tokens (int, optional): The maximum number of tokens allowed for a single document. Documents with
            more tokens will be filtered out. Defaults to 0, which means no filtering based on token count.
        max_total_tokens (int, optional): The maximum total number of tokens allowed for all documents. Documents
            that exceed this limit will be filtered out. Defaults to 0, which means no filtering based on total token count.
        retrieve_n_docs (int, optional): The maximum number of documents to retrieve. If set to a positive integer, only
            the top N documents will be returned, sorted by score. Defaults to 0, which means no limit on the number of documents.

    Returns:
        List[dict]: A list of retrieved documents, sorted by score and optionally limited by token count and/or total token count.
    """
    if len(retrieved_documents) < 1:
        return []

    # Sort the list by score
    sorted_documents = sorted(retrieved_documents, key=lambda x: x["score"], reverse=True)

    docs_total_tokens = 0
    for document in sorted_documents:
        token_count = TextProcessing.tiktoken_len(document["content"])
        document["token_count"] = token_count
        docs_total_tokens += token_count

    sorted_documents = [doc for doc in sorted_documents if doc["token_count"] <= doc_max_tokens]

    if len(retrieved_documents) == 1:
        retrieved_documents[0]["doc_num"] = 1
        return retrieved_documents

    if max_total_tokens > 0:
        iterations = 0
        original_documents_count = len(sorted_documents)
        while docs_total_tokens > max_total_tokens:
            if iterations >= original_documents_count:
                break

            # Find the index of the document with the highest token_count that exceeds max_total_tokens
            max_token_count_idx = max(
                (idx for idx, document in enumerate(sorted_documents) if document["token_count"] > max_total_tokens),
                key=lambda idx: sorted_documents[idx]["token_count"],
                default=None,
            )
            # If a document was found that meets the conditions, remove it from the list
            if max_token_count_idx is not None:
                sorted_documents.pop(max_token_count_idx)
            else:
                # Find the index of the document with the highest token_count
                max_token_count_idx = max(
                    range(len(sorted_documents)),
                    key=lambda idx: sorted_documents[idx]["token_count"],
                )
                # Remove the document with the highest token_count from the list
                sorted_documents.pop(max_token_count_idx)

            docs_total_tokens = sum(document["token_count"] for document in sorted_documents)
            iterations += 1

    if docs_max_count > 1:
        # Same as above but removes based on total count of docs instead of token count.
        while len(sorted_documents) > docs_max_count:
            max_token_count_idx = max(enumerate(sorted_documents), key=lambda x: x[1]["token_count"])[0]
            sorted_documents.pop(max_token_count_idx)

        for i, document in enumerate(sorted_documents, start=1):
            document["doc_num"] = i

    return sorted_documents


# def old_parse_retrieved_docs(retrieved_documents=None):
#     if not retrieved_documents:
#         return None

#     # Count the number of 'hard' and 'soft' documents
#     hard_count = sum(1 for doc in retrieved_documents if doc["doc_type"] == "hard")
#     soft_count = sum(1 for doc in retrieved_documents if doc["doc_type"] == "soft")

#     # Sort the list by score
#     sorted_documents = sorted(retrieved_documents, key=lambda x: x["score"], reverse=True)

#     for i, document in enumerate(sorted_documents, start=1):
#         token_count = text.tiktoken_len(document["content"])
#         if token_count > self.max_total_tokens:
#             sorted_documents.pop(i - 1)
#             continue
#         document["token_count"] = token_count
#         document["doc_num"] = i

#     docs_total_tokens = _docs_tiktoken_len(sorted_documents)

#     # self.log.info(f"context docs token count: {docs_total_tokens}")
#     iterations = 0
#     original_documents_count = len(sorted_documents)
#     while docs_total_tokens > self.max_total_tokens:
#         if iterations >= original_documents_count:
#             break
#         # Find the index of the document with the highest token_count that exceeds ceq_docs_max_token_length
#         max_token_count_idx = max(
#             (idx for idx, document in enumerate(sorted_documents) if document["token_count"] > self.docs_max_token_length),
#             key=lambda idx: sorted_documents[idx]["token_count"],
#             default=None,
#         )
#         # If a document was found that meets the conditions, remove it from the list
#         if max_token_count_idx is not None:
#             doc_type = sorted_documents[max_token_count_idx]["doc_type"]

#             if doc_type == "soft":
#                 soft_count -= 1
#             else:
#                 hard_count -= 1
#             sorted_documents.pop(max_token_count_idx)
#             # break ?
#         # Remove the lowest scoring 'soft' document if there is more than one,
#         elif soft_count > 1:
#             for idx, document in reversed(list(enumerate(sorted_documents))):
#                 if document["doc_type"] == "soft":
#                     sorted_documents.pop(idx)
#                     soft_count -= 1
#                     break
#         # otherwise remove the lowest scoring 'hard' document
#         elif hard_count > 1:
#             for idx, document in reversed(list(enumerate(sorted_documents))):
#                 if document["doc_type"] == "hard":
#                     sorted_documents.pop(idx)
#                     hard_count -= 1
#                     break
#         else:
#             # Find the index of the document with the highest token_count
#             max_token_count_idx = max(
#                 range(len(sorted_documents)),
#                 key=lambda idx: sorted_documents[idx]["token_count"],
#             )
#             # Remove the document with the highest token_count from the list
#             sorted_documents.pop(max_token_count_idx)

#         docs_total_tokens = _docs_tiktoken_len(sorted_documents)
#         # self.log.info("removed lowest scoring embedding doc .")
#         # self.log.info(f"context docs token count: {docs_total_tokens}")
#         iterations += 1
#     # self.log.info(f"number of context docs now: {len(sorted_documents)}")

#     # Same as above but removes based on total count of docs instead of token count.
#     while len(sorted_documents) > self.docs_max_used:
#         if soft_count > 1:
#             for idx, document in reversed(list(enumerate(sorted_documents))):
#                 if document["doc_type"] == "soft":
#                     sorted_documents.pop(idx)
#                     soft_count -= 1
#                     break
#         elif hard_count > 1:
#             for idx, document in reversed(list(enumerate(sorted_documents))):
#                 if document["doc_type"] == "hard":
#                     sorted_documents.pop(idx)
#                     hard_count -= 1
#                     break
#         # sself.log.info("removed lowest scoring embedding doc.")

#     for i, document in enumerate(sorted_documents, start=1):
#         document["doc_num"] = i

#     final_documents_list = []
#     for parsed_document in sorted_documents:
#         final_documents_list.append(parsed_document["url"])
#     # self.log.info(f"{len(sorted_documents)} documents returned after parsing: {final_documents_list}")

#     if not sorted_documents:
#         # self.log.info("No supporting documents after parsing!")
#         return None

#     return sorted_documents
