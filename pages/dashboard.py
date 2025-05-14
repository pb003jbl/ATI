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

st.set_page_config(
    page_title="Dashboard | ServiceNow Ticket Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("ServiceNow Ticket Dashboard")

# Check if data is available
if 'processed_data' not in st.session_state or st.session_state.processed_data is None:
    st.warning("Please upload ServiceNow ticket data on the home page first.")
    st.stop()

# Get data from session state
df = st.session_state.processed_data

# Header image
st.image("https://pixabay.com/get/g016c0c0b10bf6f695a5680ed6ceefc7010f9ecd783ad997c2574c1ec9f09005916bdbb9e2df1c3f26290a23a6c0ad6d9cc1b8bb55ec8d96b529e614a25be4ee1_1280.jpg", 
         caption="ServiceNow Ticket Analytics Dashboard", use_column_width=True)

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
            categories = ['All'] + sorted(filtered_df['category'].unique().tolist())
            selected_category = st.selectbox("Category", categories)
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # Priority filter
    if 'priority' in filtered_df.columns:
        with cols[1]:
            priorities = ['All'] + sorted(filtered_df['priority'].unique().tolist())
            selected_priority = st.selectbox("Priority", priorities)
            if selected_priority != 'All':
                filtered_df = filtered_df[filtered_df['priority'] == selected_priority]
    
    # Status filter
    if 'status' in filtered_df.columns:
        with cols[2]:
            statuses = ['All'] + sorted(filtered_df['status'].unique().tolist())
            selected_status = st.selectbox("Status", statuses)
            if selected_status != 'All':
                filtered_df = filtered_df[filtered_df['status'] == selected_status]

# Display summary metrics
metrics_container = st.container()

with metrics_container:
    st.subheader("Summary Metrics")
    cols = st.columns(4)
    
    # Total tickets
    with cols[0]:
        st.metric("Total Tickets", len(filtered_df))
    
    # Average resolution time
    if 'resolution_time_hours' in filtered_df.columns:
        with cols[1]:
            avg_resolution_time = filtered_df['resolution_time_hours'].mean()
            st.metric("Avg. Resolution Time", f"{avg_resolution_time:.1f} hrs")
    elif 'created_at' in filtered_df.columns and 'resolved_at' in filtered_df.columns:
        with cols[1]:
            filtered_df['created_at'] = pd.to_datetime(filtered_df['created_at'], errors='coerce')
            filtered_df['resolved_at'] = pd.to_datetime(filtered_df['resolved_at'], errors='coerce')
            valid_tickets = filtered_df.dropna(subset=['created_at', 'resolved_at'])
            if not valid_tickets.empty:
                resolution_time = (valid_tickets['resolved_at'] - valid_tickets['created_at']).dt.total_seconds() / 3600
                avg_resolution_time = resolution_time.mean()
                st.metric("Avg. Resolution Time", f"{avg_resolution_time:.1f} hrs")
            else:
                st.metric("Avg. Resolution Time", "N/A")
    
    # Open tickets
    if 'status' in filtered_df.columns:
        with cols[2]:
            open_tickets = filtered_df[filtered_df['status'].isin(['Open', 'In Progress'])].shape[0]
            st.metric("Open Tickets", open_tickets)
    
    # High priority tickets
    if 'priority' in filtered_df.columns:
        with cols[3]:
            # Try to handle both numeric and text priorities
            try:
                # If priority is numeric, assume lower numbers are higher priority
                priority_col = pd.to_numeric(filtered_df['priority'], errors='coerce')
                high_priority = filtered_df[priority_col <= 2].shape[0]
            except:
                # Otherwise look for common high priority labels
                high_priority = filtered_df[
                    filtered_df['priority'].str.lower().isin(['critical', 'high', '1', '2'])
                ].shape[0]
            
            st.metric("High Priority Tickets", high_priority)

# Charts section
st.header("Data Visualizations")

# First row of charts
chart_row1 = st.container()

with chart_row1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ticket Status Distribution")
        status_chart = create_ticket_overview_chart(filtered_df)
        st.plotly_chart(status_chart, use_container_width=True)
    
    with col2:
        st.subheader("Tickets Over Time")
        time_chart = create_tickets_over_time_chart(filtered_df)
        st.plotly_chart(time_chart, use_container_width=True)

# Second row of charts
chart_row2 = st.container()

with chart_row2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ticket Priority Distribution")
        priority_chart = create_priority_chart(filtered_df)
        st.plotly_chart(priority_chart, use_container_width=True)
    
    with col2:
        st.subheader("Top Categories")
        category_chart = create_category_chart(filtered_df)
        st.plotly_chart(category_chart, use_container_width=True)

# Third row of charts
chart_row3 = st.container()

with chart_row3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resolution Time Distribution")
        resolution_chart = create_resolution_time_chart(filtered_df)
        st.plotly_chart(resolution_chart, use_container_width=True)
    
    with col2:
        st.subheader("Top Assignees")
        assignee_chart = create_assignee_workload_chart(filtered_df)
        st.plotly_chart(assignee_chart, use_container_width=True)

# Heat map (full width)
heatmap_container = st.container()

with heatmap_container:
    st.subheader("Ticket Volume by Day and Hour")
    heatmap = create_heatmap_weekday_hour(filtered_df)
    st.plotly_chart(heatmap, use_container_width=True)

# Data table (expandable)
with st.expander("View Raw Data"):
    st.dataframe(filtered_df, use_container_width=True)
