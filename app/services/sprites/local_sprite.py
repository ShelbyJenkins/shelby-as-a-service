# region
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
import gradio as gr

from app.services.log_service import Logger
from app.services.deployment_service.deployment_management import DeploymentManager
from app.models.service_models import ServiceBase
from app.models.service_models import LocalModel
from app.services.ceq_agent import CEQAgent
from app.services.index_service import IndexService

# endregion

class LocalSprite(ServiceBase):
       
    model = LocalModel()
    
    def __init__(self):
        """ Sprites are initialized through a deployment.
        setup_config sets services as instance attrs.
        It uses their service_name from model.
        So CEQAgent can be accessed with self.ceq_agent.
        """
        super().__init__()
        self.required_services = [CEQAgent, IndexService]
        self.setup_config(has_children = True)
            
        self.log = Logger(
            self.deployment_name,
            "LocalSprite",
            "local_sprite.md",
            level="INFO",
        )
        self.existing_deployment_names = None
        self.local_ui_interface = None


    async def create_interface(self):
        """Creates gradio app."""
        try:
            with gr.Blocks() as local_client:
                with gr.Tab(label="Context Enhanced Querying"):
                    with gr.Column(variant="panel"):
                        ceq_chatbot = gr.Textbox(label="Chatbot", lines=20)
                        with gr.Group():
                            with gr.Row():
                                ceq_message_textbox = gr.Textbox(
                                    container=False,
                                    show_label=False,
                                    label="Message",
                                    placeholder="Type a message...",
                                    scale=7,
                                )
                            
                with gr.Tab(label="Config"):
                    config_status_textboxt = gr.Textbox(label="", value="A sprite is a wily interface for interacting with AI.")
                    with gr.Tab(label="Local App"):
                        save_deployment_btn = gr.Button(value="Save Config Changes")
                        undo_deployment_btn = gr.Button(value="Undo Config Change")
                        self.local_ui_interface.render()
                    with gr.Tab(label="Deployment Management"):
                        with gr.Group():
                            with gr.Row():
                                load_deployments_dropdown = gr.Dropdown(
                                    value=self.existing_deployment_names[0],
                                    multiselect=False,
                                    choices=self.existing_deployment_names,
                                    label="Existing Deployments:",
                                )
                            with gr.Row():
                                load_deployment_btn = gr.Button(value="Load Existing Deployment")
                        with gr.Group():
                            with gr.Row():
                                make_deployment_textbox = gr.Textbox(
                                    label="Enter new deployment name (new_deployment_name):"
                                )
                            with gr.Row():
                                make_deployment_btn = gr.Button(value="Make New Deployment")
                        with gr.Group():
                            with gr.Row():
                                delete_deployments_dropdown = gr.Dropdown(
                                    value="Danger!",
                                    multiselect=False,
                                    choices=self.existing_deployment_names,
                                    label="Existig Deployments:",
                                )
                            with gr.Row():
                                delete_deployment_radio = gr.Radio(value="Don't Delete", choices=["Don't Delete", "Check to Confirm Delete"])
                            with gr.Row():
                                delete_deployment_btn = gr.Button(value="Delete Existing Deployment")
                    with gr.Tab(label="Index Management"):
                        index_ingest_docs = gr.Button(value="ingest_docs")
                        index_delete_index = gr.Button(value="delete_index")
                        index_clear_index = gr.Button(value="clear_index")
                        index_create_index = gr.Button(value="create_index")
                    
                with gr.Tab(label="Logs", id="log"):
                    with gr.Row():
                        logs_output = gr.Textbox(
                            value="Logs will appear here...",
                            lines=30,
                            )

                ceq_message_textbox.submit(
                    fn=self._run_ceq_request,
                    inputs=ceq_message_textbox,
                    outputs=[ceq_message_textbox, ceq_chatbot],
                )
                index_ingest_docs.click(
                    fn=self.index_service.ingest_docs,
                    inputs=None,
                    outputs=None,
                )
                
                load_deployment_btn.click(
                    fn=self._load_new_deployment,
                    inputs=load_deployments_dropdown,
                    outputs=self.local_ui_interface,
                )
                make_deployment_btn.click(
                    fn=self._create_new_deployment,
                    inputs=make_deployment_textbox,
                    outputs=[
                        config_status_textboxt,
                        make_deployment_textbox,
                        load_deployments_dropdown,
                        delete_deployments_dropdown,
                    ],
                )
                delete_deployment_btn.click(
                    fn=self._delete_deployment,
                    inputs=[delete_deployments_dropdown, delete_deployment_radio],
                    outputs=[
                        config_status_textboxt,
                        load_deployments_dropdown,
                        delete_deployments_dropdown,
                        delete_deployment_radio,
                    ],
                )
                local_client.load(fn=self._gradio_logging, inputs=None, outputs=logs_output, every=3)
            
                self.log.print_and_log_gradio('LocalSprite launched')
                local_client.queue().launch()
                
        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)
        
        return local_client
               
    def _create_local_ui_interface(self):
        """Loads template interface config components and emits structured_config_components."""
        
        with gr.Blocks() as settings_interface:
            self._load_vars_from_classes(self.config, 'local_sprite', True)
            for service_class in self.services:
                with gr.Tab(label=service_class.config.service_name_, open=False, elem_id=f"{service_class.config.service_name_}_accordion"):
                    self._load_vars_from_classes(service_class.config, service_class.config.service_name_)

        return settings_interface
    
    def _load_vars_from_classes(self, class_config, class_name, secrets = False):

        with gr.Blocks(title=class_name) as settings_component:
            with gr.Group():
                with gr.Tab(label='Required Settings', open=True, elem_id=f"{class_name}_required_settings"):
                    for var in class_config.required_variables_:
                        req_var = getattr(class_config, var)
                        id = f"{class_name}_{var}"
                        gr.Textbox(value=req_var, label=var, elem_id=id, interactive=True)
                    if secrets:
                        with gr.Accordion(label='Required Secrets', open=True, elem_id=f"{class_name}_required_Secrets"):
                            pass
                with gr.Tab(label='Optional Settings', open=False, elem_id=f"{class_name}_optional_settings"):
                    for name, value in class_config.__dict__.items():
                        if not name.startswith("__") and not callable(value) and not name.endswith("_"):
                            if name not in class_config.required_variables_:
                                id = f"{class_name}_{name}"
                                gr.Textbox(value=value, label=name, elem_id=id, interactive=True)
                    
        return settings_component

    def _load_new_deployment(self, deployment_name):
        """Loads new deployment to deployment object."""
        
        self.existing_deployment_names = self._check_for_existing_deployments()
        
        if deployment_name not in self.existing_deployment_names:
            output_message = f"Can't find a deployment named: '{deployment_name}'"
            self.log.print_and_log_gradio(output_message)
            return None
        if deployment_name in self.deployment.deployment_name:
            output_message = f"Trying to load current deployment: '{deployment_name}'"
            self.log.print_and_log_gradio(output_message)
            return None
        
        self.deployment.load_deployment_from_file(deployment_name)
        
        interface_components_updated = []
        for sprite_name, sprite_class in self.deployment.sprites.items():
            attributes = {}
            
            try:
                type_annotations = sprite_class.__annotations__  # Get type annotations
            except AttributeError:
                type_annotations = {}
                
            for name, value in sprite_class.__dict__.items():
                if not name.startswith("__") and not callable(value) and not name.endswith("_"):
                    attr_type = type_annotations.get(name, None)
                    attributes[name] = (value, attr_type)
            for name, (value, attr_type) in attributes.items():
                for component in self.interface_config_components:
                    if attr_type == bool:
                        id = f"{sprite_name}_{name}_bool"
                    else:
                        id = f"{sprite_name}_{name}_str"
                    if component.elem_id == id:
                        if attr_type == bool:
                            component = gr.Checkbox.update(value=value)
                        else:
                            component = gr.Textbox.update(value=value)
                        interface_components_updated.append(component)
                        break
                        
        output_message = f"Deployment loaded: '{deployment_name}'"
        self.log.print_and_log_gradio(output_message)
        return interface_components_updated
    
    def _create_new_deployment(self, new_deployment_name):
        new_deployment_name = new_deployment_name.strip()
        if len(new_deployment_name) < 3:
            output_message = "Please enter a longer deployment name"
            self.log.print_and_log_gradio(output_message)
        elif not all(char.isalnum() or char == '_' for char in new_deployment_name):
            output_message = "Please only use alpha numeric chars and '_' chars."
            self.log.print_and_log_gradio(output_message)
        if not self.existing_deployment_names:
            self.existing_deployment_names = DeploymentManager.check_for_existing_deployments()
        if new_deployment_name in self.existing_deployment_names:
            output_message = "That deployment already exists. Please delete it first"
            self.log.print_and_log_gradio(output_message)
        else:
            DeploymentManager().create_deployment(deployment_instance=self.deployment, deployment_name=new_deployment_name)
            self.existing_deployment_names = DeploymentManager.check_for_existing_deployments()
            output_message = f" Deployment '{new_deployment_name}' created"
            self.log.print_and_log_gradio(output_message)
        
        return (
            output_message,
            gr.Textbox.update(value=""),
            gr.Dropdown.update(value=self.existing_deployment_names[0], choices=self.existing_deployment_names),
            gr.Dropdown.update(value="Danger!", choices=self.existing_deployment_names),
        )
        
    def _delete_deployment(self, delete_deployment_name, delete_deployment_radio):
        if delete_deployment_name == self.deployment.deployment_name:
            output_message = "Can't delete in use deployment. Please switch first."
            self.log.print_and_log_gradio(output_message)
        elif delete_deployment_radio != 'Check to Confirm Delete':
            output_message = "Please check the radio box to confirm delete"
            self.log.print_and_log_gradio(output_message)
        else:
            base_dir = "app/deployments"
        
            deployment_path = os.path.join(base_dir, delete_deployment_name)
            if os.path.exists(deployment_path):
                try:
                    shutil.rmtree(deployment_path)
                    output_message = f"Successfully deleted deployment: '{delete_deployment_name}'"
                    self.log.print_and_log_gradio(output_message)
                except Exception as error:
                    output_message = f"Error deleting deployment: '{delete_deployment_name}'. Error: {str(error)}"
                    self.log.print_and_log_gradio(output_message)
            else:
                output_message = f"Deployment: '{delete_deployment_name}' not found."
                self.log.print_and_log_gradio(output_message)

            self.existing_deployment_names = self._check_for_existing_deployments()
            
        return (
            output_message,
            gr.Dropdown.update(value=self.existing_deployment_names[0], choices=self.existing_deployment_names),
            gr.Dropdown.update(value="Danger!", choices=self.existing_deployment_names),
            gr.Radio.update(value = "Don't Delete", choices=["Don't Delete", "Check to Confirm Delete"]),
        )

    async def _run_ceq_request(self, request):
        # Required to run multiple requests at a time in async
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                executor, self.ceq_agent.request_thread, request
            )
            return '', response
    
    def _gradio_logging(self):
        return self.log.read_logs()

    
    def run_sprite(self):
        try:
            self.existing_deployment_names = DeploymentManager.check_for_existing_deployments()
            self.local_ui_interface = self._create_local_ui_interface()
            asyncio.run(self.create_interface())
        except Exception as error:
            output_message = f"Error: {error}"
            self.log.print_and_log_gradio(output_message)

