import streamlit as st
import pandas as pd
import json
from utils.data_processor import prepare_data_for_agents
from agents.agent_system import GroqLLMConfig, AgentSystem
import time

st.set_page_config(
    page_title="Advanced Analysis | ServiceNow Ticket Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Advanced Ticket Analysis")

# Check if data is available
if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
    st.warning("Please upload ServiceNow ticket data on the home page first.")
    st.stop()

# Check if API key is available
if 'groq_api_key' not in st.session_state or not st.session_state.groq_api_key:
    st.error("Please enter your GROQ API key on the home page to use the analysis features.")
    st.stop()

# Get data from session state
df = st.session_state.processed_data

# Header
st.image("https://pixabay.com/get/g7fb6024bedfe3638eb61c3b67870e27bdb8af6c28570c8ae2077160152f48e41e9c772c01e5345bdaa027faf951ec1af2dbdef80739427fb112e3cb832848a77_1280.jpg", 
         caption="Advanced ServiceNow Ticket Analysis", use_column_width=True)

# Initialize agent system if not already done
if 'agent_system' not in st.session_state:
    # Initialize Groq LLM config and agent system
    groq_config = GroqLLMConfig(st.session_state.groq_api_key)
    st.session_state.agent_system = AgentSystem(groq_config)

# Prepare ticket data for agents if not already done
if 'prepared_data' not in st.session_state:
    with st.spinner("Preparing data for AI analysis..."):
        st.session_state.prepared_data = prepare_data_for_agents(df)
        st.success("Data prepared for AI analysis!")

# Initialize session variables for analysis results
if 'general_analysis' not in st.session_state:
    st.session_state.general_analysis = None
if 'rca_report' not in st.session_state:
    st.session_state.rca_report = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None

# Tabs for different analysis types
tab1, tab2, tab3 = st.tabs(["General Analysis", "Root Cause Analysis", "Recommendations"])

# General Analysis Tab
with tab1:
    st.header("General Ticket Analysis")
    st.write("""
    Generate a comprehensive analysis of your ticket data to identify patterns, trends, and key insights.
    This analysis will help you understand the overall health of your service desk operations.
    """)
    
    if st.button("Generate General Analysis"):
        with st.spinner("Analyzing ticket data..."):
            try:
                # Run the analysis
                analysis_result = st.session_state.agent_system.analyze_data(
                    st.session_state.prepared_data
                )
                
                # Store the result
                st.session_state.general_analysis = analysis_result
                
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
    
    # Display analysis results if available
    if st.session_state.general_analysis:
        st.subheader("Analysis Results")
        st.markdown(st.session_state.general_analysis)
        
        # Download button for analysis report
        analysis_text = st.session_state.general_analysis
        st.download_button(
            label="Download Analysis Report",
            data=analysis_text,
            file_name="servicenow_ticket_analysis.txt",
            mime="text/plain"
        )

# Root Cause Analysis Tab
with tab2:
    st.header("Root Cause Analysis (RCA)")
    st.write("""
    Generate a detailed Root Cause Analysis report for specific incidents.
    Provide details about the incident to analyze, and the AI will generate a comprehensive RCA report.
    """)
    
    # Input for incident details
    incident_description = st.text_area(
        "Describe the incident for RCA:",
        height=150,
        placeholder="Example: On Monday, May 15th, between 9:00 AM and 11:30 AM, users experienced slow response times " +
                  "in the ServiceNow ticketing system. Approximately 50 users reported issues with ticket creation " +
                  "and updates. The system returned to normal operation after a server restart."
    )
    
    if st.button("Generate RCA Report") and incident_description:
        with st.spinner("Generating Root Cause Analysis..."):
            try:
                # Run the RCA
                rca_result = st.session_state.agent_system.generate_rca(
                    st.session_state.prepared_data,
                    incident_description
                )
                
                # Store the result
                st.session_state.rca_report = rca_result
                
                st.success("RCA report generated!")
            except Exception as e:
                st.error(f"Error during RCA generation: {str(e)}")
    
    # Display RCA results if available
    if st.session_state.rca_report:
        st.subheader("Root Cause Analysis Report")
        st.markdown(st.session_state.rca_report)
        
        # Download button for RCA report
        rca_text = st.session_state.rca_report
        st.download_button(
            label="Download RCA Report",
            data=rca_text,
            file_name="root_cause_analysis_report.txt",
            mime="text/plain"
        )

# Recommendations Tab
with tab3:
    st.header("Ticket Resolution Recommendations")
    st.write("""
    Generate smart recommendations for improving your service desk operations based on ticket data analysis.
    These recommendations will help reduce ticket volume and improve resolution times.
    """)
    
    # Check if general analysis is available
    if st.session_state.general_analysis is None:
        st.info("Please generate a General Analysis first to get better recommendations.")
    
    if st.button("Generate Recommendations"):
        with st.spinner("Generating recommendations..."):
            try:
                # Use general analysis if available, otherwise pass empty string
                analysis_results = st.session_state.general_analysis or ""
                
                # Run the recommendations generation
                recommendations_result = st.session_state.agent_system.generate_recommendations(
                    st.session_state.prepared_data,
                    analysis_results
                )
                
                # Store the result
                st.session_state.recommendations = recommendations_result
                
                st.success("Recommendations generated!")
            except Exception as e:
                st.error(f"Error during recommendations generation: {str(e)}")
    
    # Display recommendations if available
    if st.session_state.recommendations:
        st.subheader("Recommendations")
        st.markdown(st.session_state.recommendations)
        
        # Download button for recommendations
        recommendations_text = st.session_state.recommendations
        st.download_button(
            label="Download Recommendations",
            data=recommendations_text,
            file_name="servicenow_recommendations.txt",
            mime="text/plain"
        )

# Additional help information
with st.expander("Analysis Feature Guide"):
    st.markdown("""
    ### How to Use This Analysis Page
    
    #### General Analysis
    - Provides an overview of your ticket data
    - Identifies patterns, trends, and key metrics
    - Highlights areas for improvement
    
    #### Root Cause Analysis (RCA)
    - Enter a detailed description of the incident you want to analyze
    - The AI will generate a comprehensive RCA report
    - Include as much detail as possible for better results: dates, times, symptoms, affected systems, etc.
    
    #### Recommendations
    - Generates actionable suggestions based on your ticket data
    - For best results, run the General Analysis first
    - Recommendations are prioritized based on potential impact
    
    All reports can be downloaded as text files for sharing with your team or including in presentations.
    """)
