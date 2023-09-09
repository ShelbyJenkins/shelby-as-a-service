from models.models import DiscordModel, SlackModel, DeploymentModel

class DeploymentConfig:
    # Required #
    deployment_name: str = "tatum"
    docker_registry = 'docker.io'
    docker_username = 'shelbyjenkins'
    docker_repo = 'shelby-as-a-service'
    # Default
    model = DeploymentModel
    class MonikerConfigs:
        class TemplateName1:
            # Populates description at run from index_description.yaml
            # Required #
            enabled_data_domains: list = ["tatum"]
            enabled: bool = True
            class DiscordConfig:
                # Required #
                enabled: bool = True
                discord_enabled_servers: list[int] = [847940290903932939]
                # Optional #
                discord_specific_channels_enabled: bool = True
                discord_specific_channel_ids: list[int] = [1125934881206173766]
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
                model = DiscordModel
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
                ceq_max_response_tokens: int = 250
                openai_timeout_seconds: float = None
                # APIAgent
                api_agent_select_operation_id_llm_model: str = None
                api_agent_create_function_llm_model: str = None
                api_agent_populate_function_llm_model: str = None
            class SlackConfig:
                # Required #
                enabled: bool = True
                slack_enabled_teams: list[str] = ["TSVD5FHMM"]
                # Optional #
                slack_welcome_message: str = None
                slack_short_message: str = None
                slack_message_start: str = None
                slack_message_end: str = None
                model = SlackModel
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
                # APIAgent
                api_agent_select_operation_id_llm_model: str = None
                api_agent_create_function_llm_model: str = None
                api_agent_populate_function_llm_model: str = None
