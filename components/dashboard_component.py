"""
Dashboard component for ServiceNow Ticket Analyzer.
This module provides enhanced dashboard visualizations for the main app.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from utils.visualization import (
    create_ticket_overview_chart,
    create_tickets_over_time_chart,
    create_priority_chart,
    create_category_chart,
    create_resolution_time_chart,
    create_assignee_workload_chart,
    create_heatmap_weekday_hour
)

def calculate_ticket_metrics(df):
    """
    Calculate key ticket metrics for dashboard display.
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Dictionary with ticket metrics
    """
    metrics = {
        "total_tickets": len(df),
        "open_tickets": 0,
        "in_progress_tickets": 0,
        "resolved_tickets": 0,
        "closed_tickets": 0,
        "recent_tickets": 0,
        "high_priority_tickets": 0,
        "avg_resolution_time": None,
        "oldest_open_ticket": None,
        "unassigned_tickets": 0
    }
    
    # Count tickets by status
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        metrics["open_tickets"] = status_counts.get('Open', 0)
        metrics["in_progress_tickets"] = status_counts.get('In Progress', 0) 
        metrics["resolved_tickets"] = status_counts.get('Resolved', 0)
        metrics["closed_tickets"] = status_counts.get('Closed', 0)
    
    # Recent tickets (last 7 days)
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        recent_tickets = df[
            df['created_at'] > (datetime.now() - timedelta(days=7))
        ]
        metrics["recent_tickets"] = len(recent_tickets)
    
    # High priority tickets
    if 'priority' in df.columns:
        # Try to handle both numeric and text priorities
        try:
            # If priority is numeric, assume lower numbers are higher priority
            priority_col = pd.to_numeric(df['priority'], errors='coerce')
            high_priority = df[priority_col <= 2].shape[0]
        except:
            # Otherwise look for common high priority labels
            high_priority = df[
                df['priority'].astype(str).str.lower().isin(['critical', 'high', '1', '2'])
            ].shape[0]
        
        metrics["high_priority_tickets"] = high_priority
    
    # Average resolution time
    if 'resolution_time_hours' in df.columns:
        resolution_times = df['resolution_time_hours'].dropna()
        if len(resolution_times) > 0:
            metrics["avg_resolution_time"] = round(resolution_times.mean(), 1)
    
    # Oldest open ticket
    if 'created_at' in df.columns and 'status' in df.columns:
        open_tickets = df[df['status'].isin(['Open', 'In Progress'])]
        if not open_tickets.empty:
            oldest_date = open_tickets['created_at'].min()
            if pd.notna(oldest_date):
                metrics["oldest_open_ticket"] = (datetime.now() - oldest_date).days
    
    # Unassigned tickets
    if 'assigned_to' in df.columns:
        unassigned = df['assigned_to'].isna().sum()
        metrics["unassigned_tickets"] = unassigned
    
    return metrics

def render_main_dashboard(df):
    """
    Render enhanced dashboard for the main app page.
    
    Args:
        df: Processed dataframe with ticket data
    """
    # Calculate metrics
    metrics = calculate_ticket_metrics(df)
    
    # Create dashboard layout
    st.header("ServiceNow Ticket Dashboard")
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tickets", metrics["total_tickets"])
    
    with col2:
        open_progress = metrics["open_tickets"] + metrics["in_progress_tickets"]
        st.metric("Open & In Progress", open_progress)
    
    with col3:
        resolved_closed = metrics["resolved_tickets"] + metrics["closed_tickets"]
        st.metric("Resolved & Closed", resolved_closed)
    
    with col4:
        st.metric("New (Last 7 Days)", metrics["recent_tickets"])
    
    # Second metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("High Priority Tickets", metrics["high_priority_tickets"])
    
    with col2:
        avg_time = metrics["avg_resolution_time"] if metrics["avg_resolution_time"] is not None else "N/A"
        st.metric("Avg. Resolution Time", f"{avg_time} hrs" if avg_time != "N/A" else "N/A")
    
    with col3:
        oldest = metrics["oldest_open_ticket"] if metrics["oldest_open_ticket"] is not None else "N/A"
        st.metric("Oldest Open Ticket", f"{oldest} days" if oldest != "N/A" else "N/A")
    
    with col4:
        st.metric("Unassigned Tickets", metrics["unassigned_tickets"])
    
    # Chart section
    st.subheader("Ticket Analysis")
    
    # First row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Ticket Status")
        status_chart = create_ticket_overview_chart(df)
        st.plotly_chart(status_chart, use_container_width=True)
    
    with col2:
        st.write("#### Tickets Over Time")
        time_chart = create_tickets_over_time_chart(df)
        st.plotly_chart(time_chart, use_container_width=True)
    
    # Second row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Ticket Priority")
        priority_chart = create_priority_chart(df)
        st.plotly_chart(priority_chart, use_container_width=True)
    
    with col2:
        st.write("#### Top Categories")
        category_chart = create_category_chart(df)
        st.plotly_chart(category_chart, use_container_width=True)
    
    # Performance indicators
    st.subheader("Performance Indicators")
    
    # SLA performance section
    col1, col2 = st.columns(2)
    
    with col1:
        if 'resolution_time_hours' in df.columns and 'priority' in df.columns:
            # Create SLA performance chart
            df['resolution_time_hours'] = pd.to_numeric(df['resolution_time_hours'], errors='coerce')
            df['priority'] = pd.to_numeric(df['priority'], errors='coerce')
            
            # Define SLA thresholds by priority (hours)
            sla_thresholds = {
                1: 4,    # Critical: 4 hours
                2: 8,    # High: 8 hours
                3: 24,   # Medium: 24 hours
                4: 48,   # Low: 48 hours
                5: 72    # Planning: 72 hours
            }
            
            # Calculate SLA compliance
            df_with_sla = df.dropna(subset=['resolution_time_hours', 'priority'])
            if not df_with_sla.empty:
                df_with_sla['sla_threshold'] = df_with_sla['priority'].map(sla_thresholds)
                df_with_sla['within_sla'] = df_with_sla['resolution_time_hours'] <= df_with_sla['sla_threshold']
                
                # Overall SLA compliance
                overall_compliance = (df_with_sla['within_sla'].sum() / len(df_with_sla)) * 100
                
                # Create gauge chart for SLA compliance
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = overall_compliance,
                    title = {'text': "SLA Compliance"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#2196F3"},
                        'steps': [
                            {'range': [0, 60], 'color': "#FF5252"},
                            {'range': [60, 80], 'color': "#FFC107"},
                            {'range': [80, 100], 'color': "#4CAF50"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 80
                        }
                    }
                ))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to calculate SLA compliance")
        else:
            st.info("Resolution time or priority data missing for SLA analysis")
    
    with col2:
        # Ticket volume by weekday and hour (heatmap)
        st.write("#### Ticket Volume by Weekday and Hour")
        heatmap = create_heatmap_weekday_hour(df)
        st.plotly_chart(heatmap, use_container_width=True)
    
    # Additional analysis section
    st.subheader("Additional Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Resolution Time Distribution")
        resolution_chart = create_resolution_time_chart(df)
        st.plotly_chart(resolution_chart, use_container_width=True)
    
    with col2:
        st.write("#### Top Assignees")
        assignee_chart = create_assignee_workload_chart(df)
        st.plotly_chart(assignee_chart, use_container_width=True)
    
    # Trend analysis
    if 'created_at' in df.columns and 'status' in df.columns:
        st.subheader("Trend Analysis")
        
        # Group tickets by month
        df['month'] = df['created_at'].dt.strftime('%Y-%m')
        monthly_tickets = df.groupby('month').size().reset_index(name='count')
        
        if len(monthly_tickets) > 1:
            # Create trend line
            fig = px.line(
                monthly_tickets, 
                x='month', 
                y='count',
                title='Monthly Ticket Volume Trend',
                markers=True
            )
            
            # Add trendline
            fig.add_traces(
                px.scatter(
                    monthly_tickets, 
                    x='month', 
                    y='count', 
                    trendline='ols'
                ).data[1]
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Ticket Count",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("More time-series data needed for trend analysis")
    
    # Data quality section
    st.subheader("Data Quality Summary")
    
    # Calculate completeness for key fields
    key_fields = ['number', 'short_description', 'status', 'priority', 
                 'category', 'assigned_to', 'created_at', 'resolved_at']
    
    data_quality = {}
    for field in key_fields:
        if field in df.columns:
            completeness = (1 - (df[field].isna().sum() / len(df))) * 100
            data_quality[field] = round(completeness, 1)
        else:
            data_quality[field] = 0
    
    # Create data quality chart
    quality_df = pd.DataFrame({
        "Field": list(data_quality.keys()),
        "Completeness (%)": list(data_quality.values())
    })
    
    fig = px.bar(
        quality_df, 
        x='Field', 
        y='Completeness (%)',
        title='Data Completeness by Field',
        color='Completeness (%)',
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto='.1f'
    )
    
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)