from models.models import DiscordModel, SlackModel, LocalModel, IndexModel

class IndexConfig:
    index_name: str = None
    index_env: str = "us-central1-gcp"
    # Optional #
    index_embedding_model: str = "text-embedding-ada-002"
    index_tiktoken_encoding_model: str = "text-embedding-ada-002"
    index_embedding_max_chunk_size: int = 8191
    index_embedding_batch_size: int = 100
    index_vectorstore_dimension: int = 1536
    index_vectorstore_upsert_batch_size: int = 20
    index_vectorstore_metric: str = "cosine"
    index_vectorstore_pod_type: str = "p1"
    index_preprocessor_min_length: int = 150
    # index_text_splitter_goal_length: int = 500
    index_text_splitter_goal_length: int = 750
    index_text_splitter_overlap_percent: int = 15 # In percent
    index_openai_timeout_seconds: float = 180.0
    index_indexed_metadata = [
        "data_domain_name",
        "data_source_name",
        "doc_type",
        "target_type",
        "date_indexed",
    ]
    model = IndexModel
class Sprites:
    class LocalConfig:
        # Required #
        default_deployment_enabled: bool = True
        default_local_deployment_name: str = None
        model_ = LocalModel
        ### ShelbyAgent Settings - Optional ###
        # action_llm_model: str = 'gpt-3.5-turbo'
        action_llm_model: str = None
        # QueryAgent
        ceq_data_domain_constraints_enabled: bool = False
        ceq_data_domain_constraints_llm_model: str = None
        ceq_data_domain_none_found_message: str = None
        ceq_keyword_generator_enabled: bool = False
        ceq_keyword_generator_llm_model: str = None
        ceq_doc_relevancy_check_enabled: bool = True
        ceq_doc_relevancy_check_llm_model: str = None
        ceq_embedding_model: str = None
        ceq_tiktoken_encoding_model: str = None
        ceq_docs_to_retrieve: int = None
        ceq_docs_max_token_length: int = None
        ceq_docs_max_total_tokens: int = None
        ceq_docs_max_used: int = None
        ceq_main_prompt_llm_model: str = None
        ceq_max_response_tokens: int = None
        openai_timeout_seconds: float = None
    class DiscordConfig:
        # Required #
        discord_enabled_servers: list[int] = None
        # Optional #
        discord_specific_channels_enabled: bool = True
        discord_specific_channel_ids: list[int] = None
        discord_all_channels_enabled: bool = None
        discord_all_channels_excluded_channels: list[int] = None
        discord_manual_requests_enabled: bool = None
        discord_auto_response_enabled: bool = None
        discord_auto_response_cooldown: int = 11
        discord_auto_respond_in_threads: bool = None
        discord_user_daily_token_limit: int = None
        discord_welcome_message: str = None
        discord_short_message: str = None
        discord_message_start: str = None
        discord_message_end: str = None
        model_ = DiscordModel
        ### ShelbyAgent Settings - Optional ###
        # action_llm_model: str = 'gpt-3.5-turbo'
        action_llm_model: str = None
        # QueryAgent
        ceq_data_domain_constraints_enabled: bool = True
        ceq_data_domain_constraints_llm_model: str = None
        ceq_data_domain_none_found_message: str = None
        ceq_keyword_generator_enabled: bool = True
        ceq_keyword_generator_llm_model: str = None
        ceq_doc_relevancy_check_enabled: bool = True
        ceq_doc_relevancy_check_llm_model: str = None
        ceq_embedding_model: str = None
        ceq_tiktoken_encoding_model: str = None
        ceq_docs_to_retrieve: int = None
        ceq_docs_max_token_length: int = None
        ceq_docs_max_total_tokens: int = None
        ceq_docs_max_used: int = None
        ceq_main_prompt_llm_model: str = None
        ceq_max_response_tokens: int = None
        openai_timeout_seconds: float = None
    class SlackConfig:
        # Required #
        slack_enabled_teams: list[str] = None
        # Optional #
        slack_welcome_message: str = None
        slack_short_message: str = None
        slack_message_start: str = None
        slack_message_end: str = None
        model = SlackModel
        ### ShelbyAgent Settings - Optional ###
        # action_llm_model: str = 'gpt-3.5-turbo'
        action_llm_model: str = None
        # QueryAgent
        ceq_data_domain_constraints_enabled: bool = True
        ceq_data_domain_constraints_llm_model: str = None
        ceq_data_domain_none_found_message: str = None
        ceq_keyword_generator_enabled: bool = True
        ceq_keyword_generator_llm_model: str = None
        ceq_doc_relevancy_check_enabled: bool = True
        ceq_doc_relevancy_check_llm_model: str = None
        ceq_embedding_model: str = None
        ceq_tiktoken_encoding_model: str = None
        ceq_docs_to_retrieve: int = None
        ceq_docs_max_token_length: int = None
        ceq_docs_max_total_tokens: int = None
        ceq_docs_max_used: int = None
        ceq_main_prompt_llm_model: str = None
        ceq_max_response_tokens: int = None
        openai_timeout_seconds: float = None
class DevOpsConfig:
    # Required #
    discord_sprite_enabled: bool = False
    slack_sprite_enabled: bool = False
    docker_registry: str = 'docker.io'
    docker_username: str = 'username'
    docker_repo: str = 'repo'
    enabled_data_domains: list[str] = None