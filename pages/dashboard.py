import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.visualization import (
    create_ticket_overview_chart,
    create_tickets_over_time_chart,
    create_priority_chart,
    create_category_chart,
    create_resolution_time_chart,
    create_assignee_workload_chart,
    create_heatmap_weekday_hour
)
from components.dashboard_component import render_main_dashboard

st.set_page_config(
    page_title="Dashboard | ServiceNow Ticket Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("ServiceNow Ticket Advanced Dashboard")

# Check if data is available
if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
    st.warning("Please upload ServiceNow ticket data on the home page first.")
    st.stop()

# Get data from session state
df = st.session_state.processed_data

# Add date range filter if created_at column exists
date_filter_container = st.container()

with date_filter_container:
    if 'created_at' in df.columns:
        # Convert to datetime if not already
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # Get min and max dates
        min_date = df['created_at'].min().date()
        max_date = df['created_at'].max().date()
        
        # Create date filter
        st.subheader("Filter by Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
        
        # Filter data by date
        filtered_df = df[(df['created_at'].dt.date >= start_date) & (df['created_at'].dt.date <= end_date)]
    else:
        filtered_df = df
        st.info("Date filtering not available - no created_at column found in data.")

# Add category and priority filters if columns exist
filter_container = st.container()

with filter_container:
    st.subheader("Additional Filters")
    cols = st.columns(3)
    
    # Category filter
    if 'category' in filtered_df.columns:
        with cols[0]:
            # Handle mixed types in category column
            categories = filtered_df['category'].dropna().unique()
            categories_list = ['All'] + sorted([str(cat) for cat in categories])
            selected_category = st.selectbox("Category", categories_list)
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['category'].astype(str) == selected_category]
    
    # Priority filter
    if 'priority' in filtered_df.columns:
        with cols[1]:
            # Handle mixed types in priority column
            priorities = filtered_df['priority'].dropna().unique()
            priorities_list = ['All'] + sorted([str(pri) for pri in priorities])
            selected_priority = st.selectbox("Priority", priorities_list)
            if selected_priority != 'All':
                filtered_df = filtered_df[filtered_df['priority'].astype(str) == selected_priority]
    
    # Status filter
    if 'status' in filtered_df.columns:
        with cols[2]:
            # Handle mixed types in status column
            statuses = filtered_df['status'].dropna().unique()
            statuses_list = ['All'] + sorted([str(stat) for stat in statuses])
            selected_status = st.selectbox("Status", statuses_list)
            if selected_status != 'All':
                filtered_df = filtered_df[filtered_df['status'].astype(str) == selected_status]

# Render the enhanced dashboard with filtered data
render_main_dashboard(filtered_df)

# Data table (expandable)
with st.expander("View Raw Data"):
    st.dataframe(filtered_df, use_container_width=True)
