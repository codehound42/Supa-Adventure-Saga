import json

import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory, VectorStoreRetrieverMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

from dnd import CharacterNotebook, character_system_msg, gameplay_system_msg, StateNotebook, get_vectorstore


st.session_state["openai_api_key"] = st.secrets["OPENAI_API_KEY"]


def _maybe_update_character(message):
    args = json.loads(message.additional_kwargs["function_call"]["arguments"])
    st.session_state["name"] = args["name"]
    st.session_state["race"] = args["race"]
    st.session_state["class_"] = args["class_"]
    st.session_state["alignment"] = args["alignment"]
    st.session_state["completed"] = args["completed"]

    if st.session_state["completed"]:
        st.session_state[
            "player_info"
        ] = f"Name: {st.session_state['name']}\nRace: {st.session_state['race']}\nClass: {st.session_state['class_']}\nAlignment: {st.session_state['alignment']}"

        st.session_state["player_creation_end_idx"] = len(msgs.messages)


def _maybe_update_state(message: AnyMessage):
    if "function_call" in message.additional_kwargs:
        args = json.loads(message.additional_kwargs["function_call"]["arguments"])
        st.session_state["state"] = args["state"]
        st.session_state["is_quest_completed"] = args["is_quest_completed"]


def init_character_chain():
    llm = ChatOpenAI(api_key=st.session_state.openai_api_key)
    converted_openai_function = convert_pydantic_to_openai_function(CharacterNotebook)
    character_model = llm.bind(functions=[converted_openai_function])
    prompt_chat = ChatPromptTemplate.from_messages(
        [
            ("system", character_system_msg),
            MessagesPlaceholder(variable_name="history"),
            (
                "human",
                "If any updates to the character state are neccessary, please update the character notebook. If none are, just say no.",
            ),
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
                "If any updates to the game state are neccessary or if the current quest has been completed, please update the state notebook. If none are, just say no.",
            ),
        ]
    )

    state_model = llm.bind(
        functions=[convert_pydantic_to_openai_function(StateNotebook)],
        stream=False,
    )

    state_chain = (state_prompt | state_model | _maybe_update_state).with_config(run_name="StateChain")

    return state_chain


def init_character_response_chain():
    llm = ChatOpenAI(api_key=st.session_state.openai_api_key)
    response_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", character_system_msg),
            MessagesPlaceholder(variable_name="history"),
            (
                "human",
                "{prompt}",
            ),
        ]
    )

    character_response_chain = (response_prompt | llm | StrOutputParser()).with_config(
        run_name="CharacterResponseChain"
    )

    return character_response_chain


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
    st.session_state["step"] = "game"
    st.session_state["name"] = "Tom"
    st.session_state["race"] = "Elf"
    st.session_state["class_"] = "Cleric"
    st.session_state["alignment"] = "Neutral"
    st.session_state["completed"] = False
    st.session_state["is_quest_completed"] = False
    st.session_state["state"] = ""
    st.session_state[
        "story"
    ] = "In the small village of Eldenwood, you find yourself in the cozy Drunken Dragon Inn. A mysterious figure offers you a quest to investigate the haunted ruins of Graystone Castle, believed to be the source of recent villager disappearances. With a map and promise of gold, you set out to uncover the secrets lurking in the shadowy depths of the castle."
    st.session_state["quest"] = "Uncover the secrets lurking in the shadowy depths of the castle."
    st.write(st.session_state)


# init_sample_character()

msgs = StreamlitChatMessageHistory(key="messages")

memory_conversation = ConversationBufferWindowMemory(memory_key="history", chat_memory=msgs, return_messages=True, k=5)

vectorstore = get_vectorstore()
retriever = vectorstore.as_retriever()
memory_context = VectorStoreRetrieverMemory(retriever=retriever)


if "state" not in st.session_state:
    st.session_state[
        "story"
    ] = "In the small village of Eldenwood, you find yourself in the cozy Drunken Dragon Inn. A mysterious figure offers you a quest to investigate the haunted ruins of Graystone Castle, believed to be the source of recent villager disappearances. With a map and promise of gold, you set out to uncover the secrets lurking in the shadowy depths of the castle."
    st.session_state["quest"] = "Uncover the secrets lurking in the shadowy depths of the castle."
    st.session_state["state"] = ""
    st.session_state["is_quest_completed"] = False
    st.session_state["completed"] = False
    st.session_state["name"] = ""
    st.session_state["race"] = ""
    st.session_state["class_"] = ""
    st.session_state["alignment"] = ""

st.image("front_image.png")

if len(msgs.messages) == 0:
    msgs.add_ai_message("Hello and welcome to Supa Adventure Saga! A roleplaying game with me, GPT, as your DM. Let's start by making your character!")

for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if prompt := st.chat_input():
    if not st.session_state["openai_api_key"]:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    character_chain = init_character_chain()
    state_chain = init_state_chain()
    game_chain = init_game_chain()
    character_response_chain = init_character_response_chain()

    st.chat_message("human").write(prompt)

    if not st.session_state["completed"]:
        st.session_state["step"] = "character"
        response = character_response_chain.invoke(
            {"prompt": prompt, "history": memory_conversation.load_memory_variables({})["history"]}
        )
        memory_conversation.save_context({"input": prompt}, {"output": response})
        memory_context.save_context({"input": prompt}, {"output": response})

        character_chain.invoke({"history": memory_conversation.load_memory_variables({})["history"]})
    else:
        st.session_state["step"] = "game"

        history = memory_conversation.load_memory_variables({})["history"]
        extra_content = memory_context.load_memory_variables({"prompt": prompt})["history"]

        for i in range(len(history), 2):
            human_input = history[i].content
            ai_output = history[i + 1].content
            history_formatted = f"input: {human_input}\noutput: {ai_output}"
            extra_content = extra_content.replace(history_formatted, "")

        response = game_chain.invoke(
            {
                "prompt": prompt,
                "story": st.session_state["story"],
                "quest": st.session_state["quest"],
                "state": st.session_state["state"],
                "character": st.session_state["player_info"],
                "history": memory_conversation.load_memory_variables({})["history"],
                "extra_context": extra_content,
            }
        )
        memory_conversation.save_context({"input": prompt}, {"output": response})
        memory_context.save_context({"input": prompt}, {"output": response})
        state_chain.invoke(
            {
                "story": st.session_state["story"],
                "quest": st.session_state["quest"],
                "state": st.session_state["state"],
                "character": st.session_state["player_info"],
                "history": memory_conversation.load_memory_variables({})["history"],
                "extra_context": extra_content,
            }
        )

    st.chat_message("ai").write(response)


with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="openai_api_key", type="password")
    st.header("📝 Character Sheet")
    st.text(f"Name: {st.session_state.name}")
    st.text(f"Race: {st.session_state.race}")
    st.text(f"Class: {st.session_state.class_}")
    st.text(f"Alignment: {st.session_state.alignment}")
    st.header("Story")
    st.write(st.session_state.story)
    st.header("Quest")
    st.write(st.session_state.quest)
    st.header("State")
    st.write(st.session_state.state)
