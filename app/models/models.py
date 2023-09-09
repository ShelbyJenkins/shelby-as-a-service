from dataclasses import dataclass, field
from typing import List

@dataclass
class IndexModel:
    service_name_: str = 'index_service'
    required_variables_ = ['index_name']
    secrets_ = ['openai_api_key', 'pinecone_api_key']
    
    index_name: str = None
    index_env: str = 'us-central1-gcp'
    index_embedding_model: str = 'text-embedding-ada-002'
    index_tiktoken_encoding_model: str = 'text-embedding-ada-002'
    index_embedding_max_chunk_size: int = 8191
    index_embedding_batch_size: int = 100
    index_vectorstore_dimension: int = 1536
    index_vectorstore_upsert_batch_size: int = 20
    index_vectorstore_metric: str = 'cosine'
    index_vectorstore_pod_type: str = 'p1'
    index_preprocessor_min_length: int = 150
    # index_text_splitter_goal_length: int = 500
    index_text_splitter_goal_length: int = 750
    index_text_splitter_overlap_percent: int = 15  # In percent
    index_openai_timeout_seconds: float = 180.0
    index_indexed_metadata = [
        'data_domain_name',
        'data_source_name',
        'doc_type',
        'target_type',
        'date_indexed',
    ]


@dataclass
class CEQModel:
    service_name_: str = 'ceq_service'
    secrets_ = ['openai_api_key', 'pinecone_api_key']

    # ActionAgent
    action_llm_model: str = 'gpt-4'
    # QueryAgent
    ceq_data_domain_constraints_enabled: bool = False
    ceq_data_domain_constraints_llm_model: str = 'gpt-4'
    ceq_data_domain_none_found_message: str = 'Query not related to any supported data domains (aka topics). Supported data domains are:'
    ceq_keyword_generator_enabled: bool = False
    ceq_keyword_generator_llm_model: str = 'gpt-4'
    ceq_doc_relevancy_check_enabled: bool = False
    ceq_doc_relevancy_check_llm_model: str = 'gpt-4'
    ceq_embedding_model: str = 'text-embedding-ada-002'
    ceq_tiktoken_encoding_model: str = 'text-embedding-ada-002'
    ceq_docs_to_retrieve: int = 5
    ceq_docs_max_token_length: int = 1200
    ceq_docs_max_total_tokens: int = 3500
    ceq_docs_max_used: int = 5
    ceq_main_prompt_llm_model: str = 'gpt-4'
    ceq_max_response_tokens: int = 300
    openai_timeout_seconds: float = 180.0
    # APIAgent
    api_agent_select_operation_id_llm_model: str = 'gpt-4'
    api_agent_create_function_llm_model: str = 'gpt-4'
    api_agent_populate_function_llm_model: str = 'gpt-4'
    
    required_variables_ = []


@dataclass
class DiscordModel:

    discord_enabled_servers = []
    discord_specific_channels_enabled: bool = False
    discord_specific_channel_ids = []
    discord_all_channels_enabled: bool = False
    discord_all_channels_excluded_channels = []
    discord_manual_requests_enabled: bool = True
    discord_auto_response_enabled: bool = False
    discord_auto_response_cooldown: int = 10
    discord_auto_respond_in_threads: bool = False
    discord_user_daily_token_limit: int = 30000
    discord_welcome_message: str = 'ima tell you about the {}.'
    discord_short_message: str = '<@{}>, brevity is the soul of wit, but not of good queries. Please provide more details in your request.'
    discord_message_start: str = 'Running request... relax, chill, and vibe a minute.'
    discord_message_end: str = 'Generated by: gpt-4. Memory not enabled. Has no knowledge of past or current queries. For code see https://github.com/shelby-as-a-service/shelby-as-a-service.'

    sprite_name_: str = 'discord_sprite'
    required_variables_ = ['discord_enabled_servers']
    secrets_ = ['discord_bot_token']

@dataclass
class SlackModel:

    slack_enabled_teams = []
    slack_welcome_message: str = 'ima tell you about the {}.'
    slack_short_message: str = '<@{}>, brevity is the soul of wit, but not of good queries. Please provide more details in your request.'
    slack_message_start: str = 'Relax and vibe while your query is embedded, documents are fetched, and the LLM is prompted.'
    slack_message_end: str = 'Generated by: gpt-4. Memory not enabled. Has no knowledge of past or current queries. For code see https://github.com/shelby-as-a-service/shelby-as-a-service.'

    sprite_name_: str = 'slack_sprite'
    required_variables_ = ['slack_enabled_teams']
    secrets_ = ['slack_app_token', 'slack_bot_token']

@dataclass
class LocalModel:

    default_deployment_enabled: bool = True
    default_local_deployment_name: str = None
    local_message_start: str = 'Running request... relax, chill, and vibe a minute.'
    local_message_end: str = 'Generated by: gpt-4. Memory not enabled. Has no knowledge of past or current queries. For code see https://github.com/shelby-as-a-service/shelby-as-a-service.'

    sprite_name_: str = 'local_sprite'
    required_variables_ = []
    secrets_ = []

@dataclass
class ContainerDeploymentModel:
    
    required_variables_ = ['docker_registry', 'docker_username', 'docker_repo']
    secrets_ = [
        'docker_token',
        'stackpath_stack_slug',
        'stackpath_client_id',
        'stackpath_api_client_secret',
    ]

    docker_registry: str = None
    docker_username: str = None
    docker_repo: str = None


@dataclass
class DeploymentModel:
    
    enabled_sprites: List[str] = field(default_factory=lambda: ['local_sprite'])

    required_variables_ = ['enabled_sprites']
    secrets_ = []
