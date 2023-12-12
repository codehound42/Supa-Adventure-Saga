from langchain.pydantic_v1 import BaseModel, Field


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

A summary of the game state is here:

{state}"""


class StateNotebook(BaseModel):
    """Notebook to write information to"""

    state: str = Field(description="Information about the current game state")


class CharacterNotebook(BaseModel):
    """Notebook to update with character information every time you get new information about the character."""

    name: str = Field(description="Information about the name of the player that you will remember over time")
    race: str = Field(description="Information about the race of the player that you will remember over time")
    class_: str = Field(description="Information about the class of the player that you will remember over time ")
    alignment: str = Field(description="Information about the alignment of the player that you will remember over time")
    completed: bool = Field(description="Whether the character creation is completed")
