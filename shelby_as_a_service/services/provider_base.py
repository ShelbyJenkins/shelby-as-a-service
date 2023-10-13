from app_config.app_base import AppBase


class ProviderBase(AppBase):
    @staticmethod
    def get_model(provider_instance, requested_model_name=None):
        model_instance = None
        available_models = getattr(provider_instance, "AVAILABLE_MODELS", [])
        if requested_model_name:
            for model in available_models:
                if model.MODEL_NAME == requested_model_name:
                    model_instance = model
                    break
        if model_instance is None:
            for model in available_models:
                if model.MODEL_NAME == provider_instance.config.model:
                    model_instance = model
                    break
        if model_instance is None:
            raise ValueError("model_instance must not be None in ProviderBase")
        return model_instance
