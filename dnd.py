import json

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.pydantic_v1 import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from permchain import BaseCheckpointAdapter, Channel, Pregel
from permchain.channels import LastValue, Topic

character_system_msg = """You are a dungeon master for a game of dungeons and dragons.

You are interacting with the first (and only) player in the game. \
Your job is to collect all needed information about their character. This will be used in the quest. \
Feel free to ask them as many questions as needed to get to the relevant information.
The relevant information is:
- Character's name
- Character's race (or species)
- Character's class
- Character's alignment

Once you have gathered enough information, write that info to `notebook`."""


class CharacterNotebook(BaseModel):
    """Notebook to write information to"""

    player_info: str = Field(
        description="Information about a player that you will remember over time"
    )


character_prompt = ChatPromptTemplate.from_messages(
    [("system", character_system_msg), MessagesPlaceholder(variable_name="messages")]
)

def create_dnd_bot(llm: BaseChatModel, checkpoint: BaseCheckpointAdapter):
    character_model = llm.bind(
        functions=[convert_pydantic_to_openai_function(CharacterNotebook)],
    )

character_chain = (
    character_prompt
    | character_model
    | Channel.write_to("messages")
)

if __name__ == "__main__":
    character_chain.invoke()
