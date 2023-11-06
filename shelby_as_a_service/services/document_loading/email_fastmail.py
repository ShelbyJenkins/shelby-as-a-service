import json
import types
import typing
from typing import Any, Dict, Final, Generator, Iterator, Literal, Optional, Type, Union

import gradio as gr
import requests
from app.module_base import ModuleBase
from langchain.schema import Document
from pydantic import BaseModel


class EmailFastmail(ModuleBase):
    """The tiniest JMAP client you can imagine.
    From: https://github.com/fastmail/JMAP-Samples/blob/main/python3/tiny_jmap_library.py"""

    CLASS_NAME: Final[str] = "email_fastmail"
    class_name = Literal["email_fastmail"]
    CLASS_UI_NAME: Final[str] = "Email: Fastmail"
    # For intialization
    REQUIRED_SECRETS: list[str] = [
        "JMAP_USERNAME",
        "JMAP_TOKEN",
    ]

    class ClassConfigModel(BaseModel):
        hostname: str = "api.fastmail.com"
        username: Optional[str] = None

    class Config:
        extra = "ignore"

    config: ClassConfigModel

    token: str
    api_url: str

    def __init__(self, config_file_dict: dict[str, typing.Any] = {}, **kwargs):
        super().__init__(config_file_dict=config_file_dict, **kwargs)
        """Initialize using a hostname, username and bearer token"""
        self.session = None
        self.account_id = None
        self.identity_id = None

    def _load(self, uri) -> Iterator[Document]:
        documents = []
        return (Document(page_content="Hello World!", metadata={"uri": uri}) for doc in documents)

    def get_session(self):
        self.username = self.secrets["JMAP_USERNAME"]
        self.token = self.secrets["JMAP_TOKEN"]

        """Return the JMAP Session Resource as a Python dict"""
        if self.session:
            return self.session
        r = requests.get(
            "https://" + self.config.hostname + "/.well-known/jmap",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        r.raise_for_status()
        self.session = session = r.json()
        self.api_url = session["apiUrl"]
        return session

    def get_account_id(self):
        """Return the accountId for the account matching self.username"""
        if self.account_id:
            return self.account_id

        session = self.get_session()

        account_id = session["primaryAccounts"]["urn:ietf:params:jmap:mail"]
        self.account_id = account_id
        return account_id

    def get_identity_id(self):
        """Return the identityId for an address matching self.username"""
        if self.identity_id:
            return self.identity_id

        identity_res = self.make_jmap_call(
            {
                "using": [
                    "urn:ietf:params:jmap:core",
                    "urn:ietf:params:jmap:submission",
                ],
                "methodCalls": [["Identity/get", {"accountId": self.get_account_id()}, "i"]],
            }
        )

        identity_id = next(
            filter(
                lambda i: i["email"] == self.username,
                identity_res["methodResponses"][0][1]["list"],
            )
        )["id"]

        self.identity_id = str(identity_id)
        return self.identity_id

    def make_jmap_call(self, call):
        """Make a JMAP POST request to the API, returning the response as a
        Python data structure."""
        res = requests.post(
            self.api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            data=json.dumps(call),
        )
        res.raise_for_status()
        return res.json()

    def create_provider_ui_components(self, visibility: bool = True):
        ui_components = {}

        ui_components["hostname"] = gr.Textbox(
            label="Hostname",
            value=self.config.hostname,
            visible=visibility,
        )
        ui_components["username"] = gr.Textbox(
            label="Username",
            value=self.config.username,
            visible=visibility,
        )

        return ui_components
