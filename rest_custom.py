from rasa.core.channels.channel import InputChannel
from rasa.core.channels.rest import RestInput
from sanic.request import Request
from typing import (
    Text,
    Dict,
    Any,
    Optional,
)

class RestCustom(RestInput):

    @classmethod
    def name(cls) -> Text:
        return "rest_custom"

    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        return request.json.get("metadata") or self.name()
    