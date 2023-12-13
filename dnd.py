from langchain.pydantic_v1 import BaseModel, Field
import os
import os
from supabase.client import Client, create_client
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.supabase import SupabaseVectorStore

character_system_msg = """You are a dungeon master for a game of dungeons and dragons.

You are interacting with the first (and only) player in the game. \
Your job is to collect all needed information about their character. This will be used in the quest. \
Feel free to ask them as many questions as needed to get to the relevant information.
The relevant information is:
- Character's name
- Character's race (or species)
- Character's class
- Character's alignment"""


gameplay_system_msg = """You are a dungeon master for a game of dungeons and dragons.

You are leading a quest of one person. Their character description is here:

{character}

The story is:

{story}

The current quest is:

{quest}

A summary of the game state is here:

{state}

Relevant pieces of previous conversation (if applicable):
{extra_context}

(You do not need to use these pieces of information if not relevant)"""


class StateNotebook(BaseModel):
    """Notebook to write information to"""

    state: str = Field(description="Information about the current game state")
    is_quest_completed: bool = Field(description="Whether the quest has been completed")


class CharacterNotebook(BaseModel):
    """Notebook to update with character information every time you get new information about the character."""

    name: str = Field(description="Information about the name of the player that you will remember over time")
    race: str = Field(description="Information about the race of the player that you will remember over time")
    class_: str = Field(description="Information about the class of the player that you will remember over time ")
    alignment: str = Field(description="Information about the alignment of the player that you will remember over time")
    completed: bool = Field(description="Whether the character creation is completed")


def get_vectorstore():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)

    vectorstore = SupabaseVectorStore(
        embedding=OpenAIEmbeddings(),
        client=supabase,
        table_name="documents_supa_adventure_saga",
        query_name="match_documents_supa_adventure_saga",
    )
    return vectorstore
