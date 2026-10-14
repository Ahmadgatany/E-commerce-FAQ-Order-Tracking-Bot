"""Minimal Streamlit chat UI for the local Rasa REST channel."""

import uuid

import streamlit as st

from rasa_rest_client import RasaRestClient, RasaRestError


st.set_page_config(page_title="Store Assistant", page_icon="🛍️")
st.title("E-commerce Store Assistant")
st.caption("Ask a store question or track an order using its order number.")

if "chat_sender" not in st.session_state:
    st.session_state.chat_sender = uuid.uuid4().hex
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["text"])
        else:
            st.markdown(message["text"])

prompt = st.chat_input("Type your message")
if prompt and prompt.strip():
    st.session_state.chat_messages.append({"role": "user", "text": prompt.strip()})
    try:
        replies = RasaRestClient().send_message(st.session_state.chat_sender, prompt)
        st.session_state.chat_messages.extend(
            {"role": "assistant", "text": reply} for reply in replies
        )
    except RasaRestError as error:
        st.session_state.chat_messages.append(
            {"role": "assistant", "text": str(error), "error": True}
        )
    st.rerun()
