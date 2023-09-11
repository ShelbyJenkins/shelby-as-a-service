from dataclasses import asdict


class ServiceBase:
    model = None
    shared_data = 1
    
    def __init__(self):
        self.something = 1
        self.something1 = 12
            
    def setup_config(self, config_from_file: dict, **kwargs):
        if self.model is None:
            raise ValueError(f"No model defined for {self.__class__.__name__}")
        merged_config = {**asdict(self.model), **config_from_file, **kwargs}
        for key, value in merged_config.items():
            setattr(self, key, value)
        self.shared_data = ServiceBase.shared_data