import os
import streamlit as st
import pandas as pd
from utils.data_processor import load_data, preprocess_data
from utils.visualization import create_ticket_overview_chart
from utils.field_mapper import create_field_mapping_ui, get_mapped_dataframe
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
if 'field_mapping_done' not in st.session_state:
    st.session_state.field_mapping_done = False
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

# Main header with styling
st.title("ServiceNow Ticket Analyzer")

# Header image
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://pixabay.com/get/g016c0c0b10bf6f695a5680ed6ceefc7010f9ecd783ad997c2574c1ec9f09005916bdbb9e2df1c3f26290a23a6c0ad6d9cc1b8bb55ec8d96b529e614a25be4ee1_1280.jpg", 
             caption="Intelligent Ticket Analysis Platform", use_container_width=True)

# Description
st.markdown("""
This platform helps you analyze your ServiceNow ticket data using advanced AI techniques.
Upload your ticket data and get intelligent insights, root cause analysis, and resolution recommendations.
""")

# Sidebar for data upload and configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Key Input
    api_tab1, api_tab2 = st.tabs(["GROQ API", "OpenAI API"])
    
    with api_tab1:
        groq_api_key = st.text_input("GROQ API Key", value=st.session_state.groq_api_key, type="password")
        if groq_api_key != st.session_state.groq_api_key:
            st.session_state.groq_api_key = groq_api_key
    
    with api_tab2:
        openai_api_key = st.text_input("OpenAI API Key", value=st.session_state.openai_api_key, type="password")
        if openai_api_key != st.session_state.openai_api_key:
            st.session_state.openai_api_key = openai_api_key
    
    # File uploader
    st.subheader("Upload Data")
    uploaded_file = st.file_uploader("Upload ServiceNow ticket data", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            with st.spinner("Loading data..."):
                # Load the raw data
                raw_data = load_data(uploaded_file)
                
                # Save to session state
                st.session_state.data = raw_data
                st.session_state.file_uploaded = True
                
                st.success(f"Successfully loaded {len(raw_data)} tickets")
                
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

# Main content area
if st.session_state.file_uploaded and not st.session_state.field_mapping_done:
    # Show field mapping UI if data is loaded but mapping isn't done
    st.header("Field Mapping")
    st.write("""
    Before analyzing your data, let's map your file's columns to standard field names.
    This ensures the application can correctly interpret your data, even if your column names differ from the expected format.
    """)
    
    # Raw data preview
    with st.expander("Preview Raw Data"):
        st.dataframe(st.session_state.data.head(5), use_container_width=True)
    
    # Field mapping UI
    field_mapping, mapping_complete = create_field_mapping_ui(st.session_state.data)
    
    if mapping_complete:
        if st.button("Apply Field Mapping and Continue"):
            # Apply the field mapping to the data
            mapped_data = get_mapped_dataframe(st.session_state.data)
            
            # Now process the mapped data
            with st.spinner("Processing mapped data..."):
                processed_data = preprocess_data(mapped_data)
                
                # Save to session state
                st.session_state.processed_data = processed_data
                st.session_state.field_mapping_done = True
                
                st.success("Field mapping applied successfully!")
                st.rerun()
    else:
        st.info("Please map at least the required fields (number, short_description, status, priority) to continue.")
        
elif st.session_state.file_uploaded and st.session_state.field_mapping_done:
    # Dashboard preview in the main area when data is loaded and mapped
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
    
    # Data and mapping summary
    with st.expander("Data and Field Mapping Summary"):
        st.subheader("Current Field Mapping")
        
        if "field_mapping" in st.session_state:
            mapping_df = pd.DataFrame(
                {"Standard Field": list(st.session_state.field_mapping.keys()),
                 "Mapped To": list(st.session_state.field_mapping.values())}
            )
            st.dataframe(mapping_df, use_container_width=True)
            
            # Button to reset mapping
            if st.button("Reset Field Mapping"):
                st.session_state.field_mapping_done = False
                st.rerun()
        
        st.subheader("Processed Data Preview")
        st.dataframe(st.session_state.processed_data.head(5), use_container_width=True)
        
        # Data stats
        st.subheader("Data Statistics")
        st.write(f"Total tickets: {len(st.session_state.processed_data)}")
        
        if 'priority' in st.session_state.processed_data.columns:
            priority_counts = st.session_state.processed_data['priority'].value_counts()
            st.write("Priority distribution:")
            st.write(priority_counts)
    
else:
    # Welcome screen with features when no data is loaded
    st.header("Welcome to ServiceNow Ticket Analyzer")
    
    # Features introduction with images
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Interactive Dashboard")
        st.image("https://pixabay.com/get/gfed1b1e06e1c0ec3fadc15ac28ec70b253ab20f8a3b7706f00f46f69e10c89e3f0bc27d28485658c45f8d448fcb94dbfc25931ddc357178f853c0163cb1ce489_1280.jpg", 
                 use_container_width=True)
        st.markdown("""
        - Visualize ticket trends and patterns
        - Filter by various criteria
        - Interactive charts and reports
        """)
    
    with col2:
        st.subheader("AI-Powered Analysis")
        st.image("https://pixabay.com/get/g92ecc2931cf9c8dbae5069dab670036d19d630b4e7c0be9e64d35ac31ac9b9bd9ed5ec2daec47f5de8f8822c71aa4247049d75007d82f34fe5c8a1a35e793c1a_1280.jpg", 
                 use_container_width=True)
        st.markdown("""
        - Automated Root Cause Analysis
        - Smart resolution recommendations
        - Pattern recognition in ticket data
        """)
    
    # Get started instructions
    st.header("Getting Started")
    st.markdown("""
    1. Enter your GROQ API key in the sidebar (or OpenAI API key)
    2. Upload your ServiceNow ticket data (CSV or Excel format)
    3. Map your data fields to standard field names
    4. Explore the dashboard and insights
    5. Use the AI chatbot to answer questions about your data
    """)
    
    # New feature highlight
    st.success("""
    **NEW FEATURE**: Flexible Field Mapping
    
    Our new field mapping system allows you to use data with any column naming convention. Simply map your fields once, 
    and the system will handle the rest. You can even save your mappings for future use!
    """)
    
    # Sample data format information
    with st.expander("Expected Data Format"):
        st.markdown("""
        Your ServiceNow ticket data should include some or all of these columns (exact names can vary and be mapped):
        
        **Required Fields:**
        - Ticket identifier (number, incident_number, id, etc.)
        - Short description (summary, title, etc.)
        - Status (state, ticket_state, etc.)
        - Priority (priority_level, urgency, etc.)
        
        **Recommended Fields for Better Analysis:**
        - Full description (description, details, etc.)
        - Category (issue_category, type, etc.)
        - Subcategory (subtype, sub_category, etc.)
        - Assignment (assigned_to, assignee, owner, etc.)
        - Assignment group (support_group, team, etc.)
        - Created date (created_at, created_date, open_time, etc.)
        - Resolved date (resolved_at, resolution_date, etc.)
        
        Don't worry if your column names don't match exactly - our field mapping system will help you map them correctly!
        """)
