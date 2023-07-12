from pydantic import BaseModel
from typing import Dict, Optional
import os
import json
import yaml

from dotenv import load_dotenv
load_dotenv()

### Configuration Guide ###

# Set your services in the DeploymentConfig class
# These are used to create the github action workflows
# When deployed with the github actions script these are injected into the container as env vars


# Vars set here will be loaded into github actions workflow and deployed into the container env overriding defaults
class DeploymentConfig(BaseModel):
    ### Name your bot/sprite/service ###
    service_name: str = 'personal'

    document_sources_filename: str = 'personal_document_sources.yaml'
    
    ### Services ###
    docker_registry: str = 'docker.io'
    docker_username: str = 'shelbyjenkins'
    docker_repo: str = 'shelby-as-a-service'
    stackpath_stack_id: str = 'shelby-stack-327b67'
    vectorstore_index: str = 'shelby-as-a-service'
    vectorstore_environment: str = 'us-central1-gcp'
    # The secrets for these services (API keys) must be set:
    # 1. Local use: n your .env file at project root
    # 2. Deployed: as github secrets (see .github/workflows/*.yaml for list of required secrets)
    
    ### Below here are optional settings that can be left on their defaults ### 
    
    # Discord Sprite
    discord_welcome_message = '"ima tell you about the {}."'
    discord_short_message = '"<@{}>, brevity is the soul of wit, but not of good queries. Please provide more details in your request."'
    discord_message_start = '"Running request... relax, chill, and vibe a minute."'
    discord_message_end = '"Generated by: gpt-4. Memory not enabled. Has no knowledge of past or current queries. For code see https://github.com/ShelbyJenkins/shelby-as-a-service."'
    
    # ActionAgent
    action_llm_model: str = 'gpt-4'
    
    # QueryAgent
    # pre_query_llm_model: str = 'gpt-4'
    pre_query_llm_model: str = 'gpt-3.5-turbo'
    query_llm_model: str = 'gpt-4'
    vectorstore_top_k: int = 5
    max_docs_tokens: int = 3500
    max_docs_used: int = 5
    max_response_tokens: int = 300
    openai_timeout_seconds: float = 180.0
    
    # APIAgent
    select_operationID_llm_model: str = 'gpt-4'
    create_function_llm_model: str = 'gpt-4'
    populate_function_llm_model: str = 'gpt-4'
    
    # IndexAgent
    preprocessor_separators: Optional[str] = None
    embedding_model: Optional[str] = "text-embedding-ada-002"
    embedding_max_chunk_size: int = 8191
    embedding_batch_size: int = 100
    vectorstore_dimension: int = 1536
    vectorstore_upsert_batch_size: int = 20
    vectorstore_metric: str = "dotproduct"
    vectorstore_pod_type: str = "p1"
    preprocessor_min_length: int = 300
    text_splitter_goal_length: int = 1500
    text_splitter_max_length: int = 2000
    text_splitter_chunk_overlap: int = 100
    indexed_metadata: list[str] = ["data_source", "doc_type", "target_type", "resource_name"]
        
### Nothing needs to be manually set in this class ###
class AppConfig():
    def __init__(self, deployment_target: Optional[str] = None):
        ### AppConfig loads variables from the env or falls to defaults set in DeploymentConfig ###
        self.deployment_config: DeploymentConfig = DeploymentConfig()

        self.deployment_targets: list = ['discord', 'slack']
        
        self.service_name: str = os.getenv('NAME', self.deployment_config.service_name)
        self.deployment_target: str = os.getenv('DEPLOYMENT_TARGET', deployment_target) 
        
        ### services ###
        self.docker_registry: str = os.getenv('DOCKER_REGISTRY', self.deployment_config.docker_registry)
        self.docker_username: str = os.getenv('DOCKER_USERNAME', self.deployment_config.docker_username)
        self.docker_repo: str = os.getenv('DOCKER_REPO', self.deployment_config.docker_repo)
        self.stackpath_stack_id: str = os.getenv('STACKPATH_STACK_ID', self.deployment_config.stackpath_stack_id)
        self.vectorstore_index: str = os.getenv('VECTORSTORE_INDEX', self.deployment_config.vectorstore_index)
        self.vectorstore_environment: str = os.getenv('VECTORSTORE_ENVIRONMENT', self.deployment_config.vectorstore_environment)
        
        ### services secrets ###
        # For local development set private vars in .env
        # For deployment use github secrets which will be loaded into the container at deployment
        self.stackpath_api_client_secret: str = os.getenv('STACKPATH_API_CLIENT_SECRET')
        self.openai_api_key: str = os.getenv('OPENAI_API_KEY') 
        self.pinecone_api_key: str = os.getenv('PINECONE_API_KEY') 
        self.docker_token: str = os.getenv('DOCKER_TOKEN')

        match deployment_target:
            case 'discord':
                self.discord_token: str = os.getenv('DISCORD_TOKEN') 
                self.discord_channel_ids: list[int] = [int(id) for id in os.getenv('DISCORD_CHANNEL_IDS').split(',')]
                # "" are required for formating in github actions workflow, but they need to be removed for use by discord sprite
                self.discord_welcome_message: str = os.getenv('DISCORD_WELCOME_MESSAGE', self.deployment_config.discord_welcome_message).strip('"')
                self.discord_short_message: str = os.getenv('DISCORD_SHORT_MESSAGE', self.deployment_config.discord_short_message).strip('"')
                self.discord_message_start: str = os.getenv('DISCORD_MESSAGE_START', self.deployment_config.discord_message_start).strip('"')
                self.discord_message_end: str = os.getenv('DISCORD_MESSAGE_END', self.deployment_config.discord_message_end).strip('"')
            
            case 'slack':
                self.slack_bot_token: str = os.getenv('SLACK_BOT_TOKEN') 
                self.slack_app_token: str = os.getenv('SLACK_APP_TOKEN')
        
        # ActionAgent
        self.action_llm_model: str = os.getenv('ACTION_LLM_MODEL', self.deployment_config.action_llm_model)
        
        # QueryAgent
        self.pre_query_llm_model: str = os.getenv('PRE_QUERY_LLM_MODEL', self.deployment_config.pre_query_llm_model)
        self.query_llm_model: str = os.getenv('QUERY_LLM_MODEL', self.deployment_config.query_llm_model)
        self.vectorstore_top_k: int = int(os.getenv('VECTORSTORE_TOP_K', self.deployment_config.vectorstore_top_k))
        self.max_docs_tokens: int = int(os.getenv('MAX_DOCS_TOKENS', self.deployment_config.max_docs_tokens))
        self.max_docs_used: int = int(os.getenv('MAX_DOCS_USED', self.deployment_config.max_docs_used))
        self.max_response_tokens: int = int(os.getenv('MAX_RESPONSE_TOKENS', self.deployment_config.max_response_tokens))
        self.openai_timeout_seconds: float = float(os.getenv('OPENAI_TIMEOUT_SECONDS', self.deployment_config.openai_timeout_seconds))
        
        # APIAgent
        self.select_operationID_llm_model: str = os.getenv('SELECT_OPERATIONID_LLM_MODEL', self.deployment_config.select_operationID_llm_model)
        self.create_function_llm_model: str = os.getenv('CREATE_FUNCTION_LLM_MODEL', self.deployment_config.create_function_llm_model)
        self.populate_function_llm_model: str = os.getenv('POPULATE_FUNCTION_LLM_MODEL', self.deployment_config.populate_function_llm_model)
        
        # IndexAgent
        self.preprocessor_separators: Optional[str] = self.deployment_config.preprocessor_separators
        self.embedding_model: Optional[str] = self.deployment_config.embedding_model
        self.embedding_max_chunk_size: int = self.deployment_config.embedding_max_chunk_size
        self.embedding_batch_size: int = self.deployment_config.embedding_batch_size
        self.vectorstore_dimension: int = self.deployment_config.vectorstore_dimension
        self.vectorstore_upsert_batch_size: int = self.deployment_config.vectorstore_upsert_batch_size
        self.vectorstore_metric: str = self.deployment_config.vectorstore_metric
        self.vectorstore_pod_type: str = self.deployment_config.vectorstore_pod_type
        self.preprocessor_min_length: int = self.deployment_config.preprocessor_min_length
        self.text_splitter_goal_length: int = self.deployment_config.text_splitter_goal_length
        self.text_splitter_max_length: int = self.deployment_config.text_splitter_max_length
        self.text_splitter_chunk_overlap: int = self.deployment_config.text_splitter_chunk_overlap
        self.indexed_metadata: list[str] = self.deployment_config.indexed_metadata
        
        # Don't touch these
        self.tiktoken_encoding_model: Optional[str] = 'text-embedding-ada-002'
        self.prompt_template_path: Optional[str] = os.getenv('PROMPT_TEMPLATE_PATH', 'app/prompt_templates/')
        self.API_spec_path: str = os.getenv('API_SPEC_PATH', 'data/minified_openAPI_specs/')
        
        ### Generated with automation ###
        if deployment_target:
            self.docker_server: str = f'docker.io/{self.docker_username}/{self.docker_repo}'
            self.docker_image_path: str = f'{self.docker_username}/{self.docker_repo}:{deployment_target}-latest'
            self.github_action_workflow_name: str = f'{self.service_name.lower()}_{deployment_target.lower()}_build_deploy'
            self.workload_name: str = f'shelby-as-a-service-{self.service_name.lower()}-{deployment_target.lower()}-sprite'
            self. workload_slug: str = f'{self.service_name.lower()}-{self.deployment_target.lower()}-sprite'

        # Loads from document sources config file or env
        self.document_sources_filepath = os.path.join('app/configuration', self.deployment_config.document_sources_filename)
        with open(self.document_sources_filepath, 'r') as stream:
            data_sources = yaml.safe_load(stream)
        
        self.namespaces_from_file = {key: value['description'] for key, value in data_sources.items()}
        
        if os.getenv('VECTORSTORE_NAMESPACES') is not None:
            self.vectorstore_namespaces = json.loads(os.getenv('VECTORSTORE_NAMESPACES'))
        else:
            self.vectorstore_namespaces = self.namespaces_from_file

    
    

    
    
