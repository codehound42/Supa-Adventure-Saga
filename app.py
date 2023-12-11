import streamlit as st
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from dnd import character_system_msg, CharacterNotebook
from langchain.utils.openai_functions import convert_pydantic_to_openai_function


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

if len(msgs.messages) == 0:
    msgs.add_ai_message("Hello! Are you ready to create your character for the game of Dungeons and Dragons?")

for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    llm = ChatOpenAI(api_key=st.session_state.openai_api_key)
    character_model = llm.bind(
        functions=[convert_pydantic_to_openai_function(CharacterNotebook)],
    )
    prompt_chat = ChatPromptTemplate.from_messages(
        [
            ("system", character_system_msg),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{prompt}"),
        ]
    )
    llm_chain = LLMChain(
        llm=character_model,
        memory=memory,
        prompt=prompt_chat,
    )

    st.chat_message("human").write(prompt)
    response = llm_chain({"prompt": prompt})
    st.write("response", response)
    st.chat_message("ai").write(response["text"])
