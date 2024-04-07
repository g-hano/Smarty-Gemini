#import asyncio
#from asyncio import WindowsSelectorEventLoopPolicy
#asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import streamlit as st

from READPDF import ASKPDF
from htmlTemplates import css, bot_template, user_template

#? LLM ve Agent
from langchain.memory import ConversationSummaryBufferMemory
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.agents import initialize_agent, load_tools
import langchain_google_genai as genai
#from dotenv import load_dotenv
import os

#load_dotenv()
api_key=os.environ.get("GOOGLE_API_KEY")
llm = genai.GoogleGenerativeAI(model="gemini-pro",
                               verbose=True, # to see what the Agent is thinking
                               temperature=0, # less creativity
                               google_api_key=api_key
                               )

# Tools that the Agent can use
tool_names = ["ddg-search",  # Duckduckgo search for getting current informations
              "google-scholar", # Google-Scholar search for research papers
              "wikipedia", # Wikipedia search for general knowledge
              "arxiv", # Arxiv search for research papers
              "pubmed"] # Pubmed search for searching medical informations

tools = load_tools(tool_names) + [ASKPDF()] # Also adding our custom defined tool

with open("Gemini/system_prompt.txt","r") as f:
    system_prompt = f.readlines()
chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                HumanMessagePromptTemplate.from_template("{text}")
            ]
        )

memory = ConversationSummaryBufferMemory(llm=llm)
agent = initialize_agent(tools, llm, verbose=True, memory=memory, agent="zero-shot-react-description", handle_parsing_errors=True)

#? Update chat_history
def get_conversation_chain(vectorstore):
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retrieval(),
        memory=memory
    )
    return conversation_chain

st.set_page_config(page_title="Smarty-Gemini",
                       page_icon="🧠")
st.header("Smartest Gemini in the World!")
st.write(css, unsafe_allow_html=True)

def main():
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Chat with Smarty-Gemini")

    if user_input:
        st.session_state.chat_history.append({"Human": user_input})    
        chat_message =  chat_template.format_messages(text=user_input)
        chat_message_text = "\n".join(["\n".join(msg.content) for msg in chat_message])
        agent_response = agent.invoke(chat_message_text)
        st.session_state.chat_history.append({"AI":agent_response["output"]})
    
    for message in st.session_state.chat_history:
        if "Human" in message:
            st.markdown(user_template.replace("{{MSG}}", message["Human"]), unsafe_allow_html=True)
        elif "AI" in message:
            st.markdown(bot_template.replace("{{MSG}}", message["AI"]), unsafe_allow_html=True)

    with st.sidebar:
        # Display Linkedin logo and link
        col1, col2 = st.columns([0.5, 4])
        with col1:
            st.image("doc/linkedin.png", width=30)
        with col2:
            st.markdown(
                "[Linkedin](https://www.linkedin.com/in/chanyalcin/)",
                unsafe_allow_html=True,
            )

        # Display Github logo and link
        col1, col2 = st.columns([0.5, 4])
        with col1:
            st.image("doc/github-sign.png", width=30)
        with col2:
            st.markdown(
                "[Github](https://github.com/g-hano)",
                unsafe_allow_html=True,
            )

        # Display X logo and link
        col1, col2 = st.columns([0.5, 4])
        with col1:
            st.image(r"doc/twitter.png", width=30)
        with col2:
            st.markdown(
                "[X](https://twitter.com/Chan__Ya)",
                unsafe_allow_html=True,
            )

    with st.expander("Memory"):
        for message in st.session_state.chat_history:
            if "Human" in message:
                st.markdown(f"<span style='color: green;'>Human: {message['Human']}</span>", unsafe_allow_html=True)
            elif "AI" in message:
                st.markdown(f"<span style='color: blue;'>AI: {message['AI']}</span>", unsafe_allow_html=True)
            elif "System" in message:
                st.write("System: " + message["System"])
                
if __name__ == '__main__':
    main()
