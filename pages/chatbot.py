import streamlit as st
import pandas as pd
from utils.data_processor import prepare_data_for_agents
from agents.agent_system import GroqLLMConfig, AgentSystem
import time
import os

st.set_page_config(
    page_title="AI Chatbot | ServiceNow Ticket Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AI Chatbot for Ticket Analysis")

# Check if data is available
if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
    st.warning("Please upload ServiceNow ticket data on the home page first.")
    st.stop()

# Check if API key is available
if 'groq_api_key' not in st.session_state or not st.session_state.groq_api_key:
    st.error("Please enter your GROQ API key on the home page to use the chatbot.")
    st.stop()

# Get data from session state
df = st.session_state.processed_data

# Header
st.image("https://pixabay.com/get/g92ecc2931cf9c8dbae5069dab670036d19d630b4e7c0be9e64d35ac31ac9b9bd9ed5ec2daec47f5de8f8822c71aa4247049d75007d82f34fe5c8a1a35e793c1a_1280.jpg", 
         caption="AI-Powered Ticket Analysis Assistant", use_column_width=True)

# Initialize session variables for chat
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'agent_system' not in st.session_state:
    # Initialize Groq LLM config and agent system
    groq_config = GroqLLMConfig(st.session_state.groq_api_key)
    st.session_state.agent_system = AgentSystem(groq_config)

# Prepare ticket data for agents if not already done
if 'prepared_data' not in st.session_state:
    with st.spinner("Preparing data for AI analysis..."):
        st.session_state.prepared_data = prepare_data_for_agents(df)
        st.success("Data prepared for AI analysis!")

# Chat container
st.subheader("ServiceNow Ticket Analysis Chat")

st.markdown("""
Ask questions about your ticket data and get AI-powered insights. Examples:
- What are the most common issues in our tickets?
- Which category has the longest resolution time?
- What are the trends in high priority tickets?
- Can you identify any patterns in recurring incidents?
- Which team members have the highest workload?
""")

# Display chat history
chat_container = st.container()

with chat_container:
    for i, message in enumerate(st.session_state.chat_history):
        if message['role'] == 'user':
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown(f"**AI Assistant:** {message['content']}")
        
        # Add a separator between messages except after the last one
        if i < len(st.session_state.chat_history) - 1:
            st.markdown("---")

# User input
user_input = st.text_input("Type your question here:", key="user_question")

# Query mode selection
query_mode = st.radio(
    "Select query mode:",
    ["Direct Query (Faster)", "Multi-Agent Analysis (More Comprehensive)"],
    index=0,
    horizontal=True
)

# Process user input
if st.button("Send") and user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Show processing message
    with st.spinner("Analyzing your question..."):
        try:
            if query_mode == "Direct Query (Faster)":
                # Use direct query for faster response
                response = st.session_state.agent_system.direct_query(
                    user_input,
                    st.session_state.prepared_data
                )
            else:
                # Use multi-agent system for more comprehensive analysis
                response = st.session_state.agent_system.multi_agent_chat(
                    user_input,
                    st.session_state.prepared_data
                )
            
            # Add response to chat history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            
        except Exception as e:
            # Handle errors
            error_msg = f"Error processing your request: {str(e)}"
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': error_msg
            })
    
    # Rerun to show the updated chat
    st.rerun()

# Clear chat button
if st.button("Clear Chat") and st.session_state.chat_history:
    st.session_state.chat_history = []
    st.rerun()

# Additional information about the data
st.subheader("Data Overview")
col1, col2 = st.columns(2)

with col1:
    st.write(f"Total tickets: {len(df)}")
    
    if 'priority' in df.columns:
        priority_counts = df['priority'].value_counts()
        st.write("Priority distribution:")
        st.write(priority_counts)

with col2:
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        st.write("Status distribution:")
        st.write(status_counts)
    
    if 'category' in df.columns:
        top_categories = df['category'].value_counts().head(5)
        st.write("Top 5 categories:")
        st.write(top_categories)

# Information about the AI assistant
with st.expander("About this AI Assistant"):
    st.markdown("""
    This AI assistant uses:
    - **GROQ LLM**: A powerful language model for understanding and analyzing your ticket data
    - **AutoGen**: A multi-agent framework that enables collaborative problem-solving
    
    The assistant can:
    - Answer questions about your ticket data
    - Identify patterns and trends
    - Suggest improvements for service management
    - Generate insights about resolution times, priorities, and categories
    
    For more detailed analysis, check out the Analysis page where you can generate complete reports.
    """)
