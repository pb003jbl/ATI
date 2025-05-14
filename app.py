import os
import streamlit as st
import pandas as pd
from utils.data_processor import load_data, preprocess_data
from utils.visualization import create_ticket_overview_chart
import time

# Configure the page
st.set_page_config(
    page_title="ServiceNow Ticket Analyzer",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")

# Main header with styling
st.title("ServiceNow Ticket Analyzer")

# Header image
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://pixabay.com/get/g016c0c0b10bf6f695a5680ed6ceefc7010f9ecd783ad997c2574c1ec9f09005916bdbb9e2df1c3f26290a23a6c0ad6d9cc1b8bb55ec8d96b529e614a25be4ee1_1280.jpg", 
             caption="Intelligent Ticket Analysis Platform", use_column_width=True)

# Description
st.markdown("""
This platform helps you analyze your ServiceNow ticket data using advanced AI techniques.
Upload your ticket data and get intelligent insights, root cause analysis, and resolution recommendations.
""")

# Sidebar for data upload and configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key Input
    groq_api_key = st.text_input("GROQ API Key", value=st.session_state.groq_api_key, type="password")
    if groq_api_key != st.session_state.groq_api_key:
        st.session_state.groq_api_key = groq_api_key
    
    # File uploader
    st.subheader("Upload Data")
    uploaded_file = st.file_uploader("Upload ServiceNow ticket data", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            with st.spinner("Processing data..."):
                # Load and process the data
                raw_data = load_data(uploaded_file)
                processed_data = preprocess_data(raw_data)
                
                # Save to session state
                st.session_state.data = raw_data
                st.session_state.processed_data = processed_data
                st.session_state.file_uploaded = True
                
                st.success(f"Successfully loaded {len(raw_data)} tickets")
                
                # Show data info
                st.subheader("Data Summary")
                st.write(f"Total tickets: {len(raw_data)}")
                if 'priority' in processed_data.columns:
                    priority_counts = processed_data['priority'].value_counts()
                    st.write("Priority distribution:")
                    st.write(priority_counts)
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# Main content area
if st.session_state.file_uploaded:
    # Dashboard preview in the main area when data is loaded
    st.header("Quick Overview")
    col1, col2 = st.columns(2)
    
    with col1:
        # Basic ticket metrics
        st.subheader("Ticket Metrics")
        if 'status' in st.session_state.processed_data.columns:
            status_counts = st.session_state.processed_data['status'].value_counts()
            open_tickets = status_counts.get('Open', 0) + status_counts.get('In Progress', 0)
            closed_tickets = status_counts.get('Closed', 0) + status_counts.get('Resolved', 0)
            
            st.metric("Open Tickets", open_tickets)
            st.metric("Closed Tickets", closed_tickets)
            
            if 'created_at' in st.session_state.processed_data.columns:
                recent_tickets = st.session_state.processed_data[
                    pd.to_datetime(st.session_state.processed_data['created_at']) > 
                    pd.Timestamp.now() - pd.Timedelta(days=7)
                ].shape[0]
                st.metric("New Tickets (Last 7 Days)", recent_tickets)
    
    with col2:
        # Preview chart
        st.subheader("Ticket Status Overview")
        if 'status' in st.session_state.processed_data.columns:
            chart = create_ticket_overview_chart(st.session_state.processed_data)
            st.plotly_chart(chart, use_container_width=True)
    
    # Navigation instructions
    st.info("""
    Navigate to the pages in the sidebar to:
    - View the detailed Dashboard for more visualizations
    - Use the Chatbot to query your ticket data
    - Run deep Analysis for RCA and recommendations
    """)
    
else:
    # Welcome screen with features when no data is loaded
    st.header("Welcome to ServiceNow Ticket Analyzer")
    
    # Features introduction with images
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Interactive Dashboard")
        st.image("https://pixabay.com/get/gfed1b1e06e1c0ec3fadc15ac28ec70b253ab20f8a3b7706f00f46f69e10c89e3f0bc27d28485658c45f8d448fcb94dbfc25931ddc357178f853c0163cb1ce489_1280.jpg", 
                 use_column_width=True)
        st.markdown("""
        - Visualize ticket trends and patterns
        - Filter by various criteria
        - Interactive charts and reports
        """)
    
    with col2:
        st.subheader("AI-Powered Analysis")
        st.image("https://pixabay.com/get/g92ecc2931cf9c8dbae5069dab670036d19d630b4e7c0be9e64d35ac31ac9b9bd9ed5ec2daec47f5de8f8822c71aa4247049d75007d82f34fe5c8a1a35e793c1a_1280.jpg", 
                 use_column_width=True)
        st.markdown("""
        - Automated Root Cause Analysis
        - Smart resolution recommendations
        - Pattern recognition in ticket data
        """)
    
    # Get started instructions
    st.header("Getting Started")
    st.markdown("""
    1. Enter your GROQ API key in the sidebar
    2. Upload your ServiceNow ticket data (CSV or Excel format)
    3. Explore the dashboard and insights
    4. Use the AI chatbot to answer questions about your data
    """)
    
    # Sample data format information
    with st.expander("Expected Data Format"):
        st.markdown("""
        Your ServiceNow ticket data should include the following columns:
        - `number`: Ticket number/ID
        - `short_description`: Brief description of the issue
        - `description`: Detailed description of the issue
        - `status`: Current status (Open, In Progress, Resolved, Closed, etc.)
        - `priority`: Priority level (1-Critical, 2-High, 3-Moderate, 4-Low, etc.)
        - `category`: Issue category
        - `subcategory`: Issue subcategory
        - `assigned_to`: Person assigned to the ticket
        - `created_at`: Ticket creation timestamp
        - `resolved_at`: Ticket resolution timestamp (if resolved)
        
        Additional fields are welcome and will enhance the analysis.
        """)
