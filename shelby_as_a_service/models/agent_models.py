from dataclasses import dataclass, field
from typing import List


@dataclass
class ActionAgentModel:

    # ActionAgent
    action_llm_model: str = 'gpt-4'
    # QueryAgent
    
    ceq_data_domain_constraints_enabled: bool = False
    
    # APIAgent
    # api_agent_select_operation_id_llm_model: str = 'gpt-4'
    # api_agent_create_function_llm_model: str = 'gpt-4'
    # api_agent_populate_function_llm_model: str = 'gpt-4'
    
    service_name_: str = 'action_agent'
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=list) 
    
@dataclass
class CEQAgentModel:

    # ActionAgent
    action_llm_model: str = 'gpt-4'
    # QueryAgent
    
    query_embedding_model: str = 'text-embedding-ada-001'
    data_domain_constraints_enabled: bool = False
    data_domain_constraints_llm_model: str = 'gpt-4'
    data_domain_none_found_message: str = 'Query not related to any supported data domains (aka topics). Supported data domains are:'
    keyword_generator_enabled: bool = False
    keyword_generator_llm_model: str = 'gpt-4'
    doc_relevancy_check_enabled: bool = False
    doc_relevancy_check_llm_model: str = 'gpt-4'
    docs_to_retrieve: int = 5
    docs_max_token_length: int = 1200
    docs_max_total_tokens: int = 3500
    docs_max_used: int = 5
    main_prompt_llm_model: str = 'gpt-4'
    max_response_tokens: int = 300
    
    
    service_name_: str = 'ceq_agent'
    required_variables_: List[str] = field(default_factory=list) 
    required_secrets_: List[str] = field(default_factory=list) 



