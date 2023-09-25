from decimal import Decimal
from langchain.embeddings import OpenAIEmbeddings
from models.app_base import AppBase
from models.embedding_models import OpenAIEmbeddingModel
from services.data_processing.data_processing_service import TextProcessing

class OpenAIEmbeddingService(AppBase):
    
    embedding_model = None
    
    model_ = OpenAIEmbeddingModel()
    required_services_ = None
    
    def __init__(self, config, sprite_name):
        """
        """
        super().__init__()
        self.setup_config(config, sprite_name)
    
    def set_embedding_model(self, encoding_model):
        for model in self.model_.available_models:
            if model.model_name == self.default_embedding_model:
                self.embedding_model = model
            if model.model_name == encoding_model:
                self.embedding_model = model
                break
        
    def get_query_embedding(self, query):
        
        token_count = TextProcessing.tiktoken_len(query, self.embedding_model.model_name)
        
        self.calculate_cost(token_count)
        
        embedding_retriever = OpenAIEmbeddings(
            # Note that this is openai_api_key and not api_key
            openai_api_key=self.secrets["openai_api_key"],
            model=self.embedding_model.model_name,
            request_timeout=self.openai_timeout_seconds,
        )
        dense_embedding = embedding_retriever.embed_query(query)
       
        return dense_embedding
    
    def calculate_cost(self, token_count):
        # Convert numbers to Decimal
        cost_per_k_decimal = Decimal(self.embedding_model.cost_per_k)
        token_count_decimal = Decimal(token_count)

        # Perform the calculation using Decimal objects
        request_cost = cost_per_k_decimal * (token_count_decimal / 1000)
        
        # If you still wish to round (even though Decimal is precise), you can do so
        request_cost = round(request_cost, 10)
        print(f"Request cost: ${format(request_cost, 'f')}")
        # Ensure total_cost is a Decimal as well; if it's not already, convert it
        if not isinstance(AppBase.total_cost, Decimal):
            AppBase.total_cost = Decimal(AppBase.total_cost)
        
        AppBase.total_cost += request_cost
        print(f"Total cost: ${format(AppBase.total_cost, 'f')}")
        