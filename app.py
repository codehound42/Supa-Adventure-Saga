import json

import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from dnd import CharacterNotebook, character_system_msg, gameplay_system_msg, StateNotebook


def _maybe_update_character(message):
    if "function_call" in message.additional_kwargs:
        args = json.loads(message.additional_kwargs["function_call"]["arguments"])
        st.session_state["player_info"] = args["player_info"]
        st.session_state["player_creation_end_idx"] = len(msgs.messages)
        return "Great! Let's get started with the quest."
    return message.content


def _maybe_update_state(message: AnyMessage):
    if "function_call" in message.additional_kwargs:
        args = json.loads(message.additional_kwargs["function_call"]["arguments"])
        st.session_state["state"] = args["state"]


def init_character_chain():
    llm = ChatOpenAI(api_key=st.session_state.openai_api_key)
    converted_openai_function = convert_pydantic_to_openai_function(CharacterNotebook)
    character_model = llm.bind(functions=[converted_openai_function])
    prompt_chat = ChatPromptTemplate.from_messages(
        [
            ("system", character_system_msg),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{prompt}"),
        ]
    )

    character_chain = (prompt_chat | character_model | _maybe_update_character).with_config(run_name="CharacterChain")
    return character_chain


def init_state_chain():
    llm = ChatOpenAI(api_key=st.session_state.openai_api_key)

    state_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", gameplay_system_msg),
            MessagesPlaceholder(variable_name="history"),
            (
                "human",
                "If any updates to the game state are neccessary, please update the state notebook. If none are, just say no.",
            ),
        ]
    )

    state_model = llm.bind(
        functions=[convert_pydantic_to_openai_function(StateNotebook)],
        stream=False,
    )

    state_chain = (state_prompt | state_model | _maybe_update_state).with_config(run_name="StateChain")

    return state_chain


def init_game_chain():
    llm = ChatOpenAI(api_key=st.session_state.openai_api_key)
    prompt_chat = ChatPromptTemplate.from_messages(
        [
            ("system", gameplay_system_msg),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{prompt}"),
        ]
    )
    game_chain = (prompt_chat | llm | StrOutputParser()).with_config(run_name="GameChain")
    return game_chain


def init_sample_character():
    st.session_state["messages"] = [
        AIMessage(content="Hello! Are you ready to create your character for the game of Dungeons and Dragons?"),
        HumanMessage(content="Yes"),
        AIMessage(content="Great! Let's start with the basics. What is your character's name?"),
        HumanMessage(content="Tom"),
        AIMessage(
            content="Nice to meet you, Tom! Now, what race or species is your character? Some options include human, elf, dwarf, gnome, and halfling, among others."
        ),
        HumanMessage(content="Elf"),
        AIMessage(
            content="Excellent choice, Tom! Now, let's move on to your character's class. The class determines the abilities and skills your character will have. Some options include warrior, mage, rogue, and cleric, among others. What class would you like your character to be?"
        ),
        HumanMessage(content="Cleric"),
        AIMessage(
            content="Great choice, Tom! Lastly, we need to determine your character's alignment. Alignment represents your character's moral and ethical outlook. Some options include lawful good, neutral good, chaotic good, lawful neutral, true neutral, chaotic neutral, lawful evil, neutral evil, and chaotic evil. Which alignment resonates with your character?"
        ),
        HumanMessage(content="Neutral"),
        AIMessage(
            content="Thank you, Tom! I have all the information I need to proceed with the quest. I will write down your character's details in my notebook. Please give me a moment.\n\n```\nName: Tom\nRace: Elf\nClass: Cleric\nAlignment: Neutral\n```\n\nIs there anything else you would like to add or ask before we begin the game?"
        ),
    ]
    st.session_state["player_creation_end_idx"] = 11
    st.session_state["step"] = "character"
    st.session_state[
        "player_info"
    ] = """Name: Tom
Race: Elf
Class: Cleric
Alignment: Neutral"""


if "messages" not in st.session_state:
    init_sample_character()


msgs = StreamlitChatMessageHistory(key="messages")

memory = ConversationBufferMemory(memory_key="history", chat_memory=msgs, return_messages=True)

with st.sidebar:
    openai_api_key = st.text_input(
        "OpenAI API Key",
        key="openai_api_key",
        type="password",
        value=st.secrets["OPENAI_API_KEY"],
    )

st.title("💬 Chatbot")

if "state" not in st.session_state:
    st.session_state[
        "state"
    ] = "In the small village of Eldenwood, you find yourself in the cozy Drunken Dragon Inn. A mysterious figure offers you a quest to investigate the haunted ruins of Graystone Castle, believed to be the source of recent villager disappearances. With a map and promise of gold, you set out to uncover the secrets lurking in the shadowy depths of the castle."

if len(msgs.messages) == 0:
    msgs.add_ai_message("Hello! Are you ready to create your character for the game of Dungeons and Dragons?")

for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    character_chain = init_character_chain()
    state_chain = init_state_chain()
    game_chain = init_game_chain()

    st.chat_message("human").write(prompt)

    if not "player_info" in st.session_state:
        st.session_state["step"] = "character"
        response = character_chain.invoke({"prompt": prompt, "history": memory.load_memory_variables({})["history"]})
        memory.save_context({"input": prompt}, {"output": response})
    else:
        st.session_state["step"] = "game"
        response = game_chain.invoke(
            {
                "prompt": prompt,
                "state": st.session_state["state"],
                "character": st.session_state["player_info"],
                "history": memory.load_memory_variables({})["history"][
                    st.session_state["player_creation_end_idx"] - 1 :
                ],
            }
        )
        memory.save_context({"input": prompt}, {"output": response})
        state_chain.invoke(
            {
                "state": st.session_state["state"],
                "character": st.session_state["player_info"],
                "history": memory.load_memory_variables({})["history"][
                    st.session_state["player_creation_end_idx"] - 1 :
                ],
            }
        )

    st.chat_message("ai").write(response)

    st.write(st.session_state)
