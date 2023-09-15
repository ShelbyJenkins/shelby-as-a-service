import os
import logging
import threading

class Logger:
    def __init__(self, deployment_name, logger_name, log_file, level="INFO"):
        self.log_file = log_file
        self.level = level
        self.lock = threading.Lock()
        self.log_dir = f"app/deployments/{deployment_name}/logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file_path = os.path.join(self.log_dir, log_file)
        self.logger = logging.getLogger(logger_name)
        self.formatter = logging.Formatter(
            "%(levelname)s: %(asctime)s %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p"
        )
        self.clear_and_set_handler(overwrite=True)
    
    def clear_and_set_handler(self, overwrite = False):
        # If the logger has handlers, remove them
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        if overwrite is True:
            fileHandler = logging.FileHandler(os.path.join(self.log_dir, self.log_file), mode="w")
        else:    
            fileHandler = logging.FileHandler(os.path.join(self.log_dir, self.log_file), mode="a")

        logging_level = logging._nameToLevel.get(self.level.upper(), logging.INFO)
        fileHandler.setFormatter(self.formatter)
        fileHandler.setLevel(logging_level)
        self.logger.setLevel(logging_level)
        self.logger.addHandler(fileHandler)
        self.logger.propagate = False

    def print_and_log(self, message):
        try:
            print(message)
            self.logger.info(message)
            for handler in self.logger.handlers:
                handler.flush()
                handler.close()
        except Exception as error:
            # Handle the error or print it out
            print(f"An error occurred while logging: {error}")
                
    def print_and_log_gradio(self, message):
        with self.lock:
            try:
                print(message)
                self.logger.info(message)
                for handler in self.logger.handlers:
                    handler.flush()
                    handler.close()
                    self.clear_and_set_handler()
            except Exception as error:
                # Handle the error or print it out
                print(f"An error occurred while logging: {error}")
            
    def read_logs(self):
        with self.lock:
            with open(self.log_file_path, 'r', encoding="utf-8") as file:
                return file.read()
