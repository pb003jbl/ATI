import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import streamlit as st

def create_ticket_overview_chart(df):
    """
    Create an overview chart showing ticket status distribution
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'status' not in df.columns:
        # Create a placeholder chart if status column doesn't exist
        fig = go.Figure()
        fig.add_annotation(
            text="Status data not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Count tickets by status
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Create color mapping for statuses
    status_colors = {
        'Open': '#FF9800',         # Orange
        'In Progress': '#2196F3',  # Blue
        'Resolved': '#4CAF50',     # Green
        'Closed': '#9E9E9E'        # Grey
    }
    
    # Create the pie chart
    fig = px.pie(
        status_counts, 
        values='Count', 
        names='Status',
        title='Ticket Status Distribution',
        color='Status',
        color_discrete_map=status_colors
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(t=50, b=50, l=10, r=10)
    )
    
    return fig

def create_tickets_over_time_chart(df):
    """
    Create a line chart showing tickets created over time
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'created_at' not in df.columns:
        # Create a placeholder chart if created_at column doesn't exist
        fig = go.Figure()
        fig.add_annotation(
            text="Creation date data not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Ensure created_at is datetime
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    
    # Filter out rows with invalid dates
    valid_df = df.dropna(subset=['created_at'])
    
    if valid_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid dates available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Group by date and count
    valid_df['date'] = valid_df['created_at'].dt.date
    daily_counts = valid_df.groupby('date').size().reset_index()
    daily_counts.columns = ['Date', 'Count']
    
    # Create the line chart
    fig = px.line(
        daily_counts, 
        x='Date', 
        y='Count',
        title='Tickets Created Over Time',
        labels={'Count': 'Number of Tickets', 'Date': 'Date'},
    )
    
    fig.update_layout(
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        margin=dict(t=50, b=50, l=10, r=10)
    )
    
    return fig

def create_priority_chart(df):
    """
    Create a bar chart showing ticket distribution by priority
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'priority' not in df.columns:
        # Create a placeholder chart if priority column doesn't exist
        fig = go.Figure()
        fig.add_annotation(
            text="Priority data not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    num_priority_colors = [
    "rgb(255,0,0)",  # Critical
    "rgb(255,128,0)",  # High
    "rgb(255,255,0)",  # Moderate
    "rgb(0,255,0)",  # Low
    ]
    
    # Count tickets by priority
    priority_counts = df['priority'].value_counts().reset_index()
    priority_counts.columns = ['Priority', 'Count']
    
    # Sort by priority if numeric
    try:
        priority_counts['Priority'] = pd.to_numeric(priority_counts['Priority'])
        priority_counts = priority_counts.sort_values('Priority')
    except:
        # If not numeric, sort by count instead
        priority_counts = priority_counts.sort_values('Count', ascending=False)
    
    # Create color scale based on priority (red for high priority, green for low)
    if priority_counts['Priority'].dtype in [np.int64, np.float64]:
        # Use a color scale for numeric priorities
        # color_scale = px.colors.diverging.RdYlGn_r
        color_scale = num_priority_colors
    else:
        # Use a discrete color map for non-numeric priorities
        color_scale = px.colors.qualitative.Set1
    
    # Create the bar chart
    fig = px.bar(
        priority_counts, 
        x='Priority', 
        y='Count',
        title='Ticket Distribution by Priority',
        labels={'Count': 'Number of Tickets', 'Priority': 'Priority'},
        color='Priority',
        color_continuous_scale=color_scale if priority_counts['Priority'].dtype in [np.int64, np.float64] else None,
    )
    
    fig.update_layout(
        xaxis=dict(type='category'),
        yaxis=dict(showgrid=True),
        margin=dict(t=50, b=50, l=10, r=10)
    )
    
    return fig

def create_category_chart(df):
    """
    Create a horizontal bar chart showing ticket distribution by category
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'category' not in df.columns:
        # Create a placeholder chart if category column doesn't exist
        fig = go.Figure()
        fig.add_annotation(
            text="Category data not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Count tickets by category
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']
    
    # Sort by count and take top 10
    category_counts = category_counts.sort_values('Count', ascending=False).head(10)
    
    # Create the horizontal bar chart
    fig = px.bar(
        category_counts, 
        y='Category', 
        x='Count',
        title='Top 10 Ticket Categories',
        labels={'Count': 'Number of Tickets', 'Category': 'Category'},
        orientation='h',
        color='Count',
        color_continuous_scale=px.colors.sequential.Blues,
    )
    
    fig.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        xaxis=dict(showgrid=True),
        margin=dict(t=50, b=50, l=150, r=10)
    )
    
    return fig

def create_resolution_time_chart(df):
    """
    Create a histogram showing ticket resolution times
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'resolution_time_hours' not in df.columns:
        # Check if we can calculate resolution time
        if 'created_at' in df.columns and 'resolved_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
            df['resolved_at'] = pd.to_datetime(df['resolved_at'], errors='coerce')
            
            # Calculate resolution time
            valid_dates = ~df['created_at'].isna() & ~df['resolved_at'].isna()
            if valid_dates.any():
                df.loc[valid_dates, 'resolution_time_hours'] = (
                    df.loc[valid_dates, 'resolved_at'] - 
                    df.loc[valid_dates, 'created_at']
                ).dt.total_seconds() / 3600
            else:
                # Create a placeholder chart if no valid resolution times
                fig = go.Figure()
                fig.add_annotation(
                    text="Resolution time data not available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                return fig
        else:
            # Create a placeholder chart if required columns don't exist
            fig = go.Figure()
            fig.add_annotation(
                text="Resolution time data not available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
    
    # Filter tickets with valid resolution times
    valid_df = df.dropna(subset=['resolution_time_hours'])
    
    if valid_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid resolution time data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Create the histogram
    fig = px.histogram(
        valid_df, 
        x='resolution_time_hours',
        title='Ticket Resolution Time Distribution',
        labels={'resolution_time_hours': 'Resolution Time (hours)'},
        nbins=20,
        color_discrete_sequence=['#2196F3']
    )
    
    # Add a vertical line for the median resolution time
    median_time = valid_df['resolution_time_hours'].median()
    fig.add_vline(
        x=median_time,
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Median: {median_time:.1f} hours",
        annotation_position="top right"
    )
    
    fig.update_layout(
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True, title="Number of Tickets"),
        margin=dict(t=50, b=50, l=10, r=10)
    )
    
    return fig

def create_assignee_workload_chart(df):
    """
    Create a bar chart showing workload by assignee
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'assigned_to' not in df.columns:
        # Create a placeholder chart if assigned_to column doesn't exist
        fig = go.Figure()
        fig.add_annotation(
            text="Assignee data not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Count tickets by assignee
    assignee_counts = df['assigned_to'].value_counts().reset_index()
    assignee_counts.columns = ['Assignee', 'Count']
    
    # Get top 10 assignees
    top_assignees = assignee_counts.head(10)
    
    # Create the bar chart
    fig = px.bar(
        top_assignees, 
        x='Assignee', 
        y='Count',
        title='Top 10 Assignees by Ticket Volume',
        labels={'Count': 'Number of Tickets', 'Assignee': 'Assigned To'},
        color='Count',
        color_continuous_scale=px.colors.sequential.Viridis,
    )
    
    fig.update_layout(
        xaxis=dict(tickangle=45),
        yaxis=dict(showgrid=True),
        margin=dict(t=50, b=100, l=10, r=10)
    )
    
    return fig

def create_heatmap_weekday_hour(df):
    """
    Create a heatmap showing ticket volume by weekday and hour
    
    Args:
        df: Processed dataframe with ticket data
        
    Returns:
        Plotly figure object
    """
    if 'created_at' not in df.columns:
        # Create a placeholder chart if created_at column doesn't exist
        fig = go.Figure()
        fig.add_annotation(
            text="Creation date data not available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Ensure created_at is datetime
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    
    # Filter out rows with invalid dates
    valid_df = df.dropna(subset=['created_at'])
    
    if valid_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No valid dates available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Extract weekday and hour
    valid_df['weekday'] = valid_df['created_at'].dt.day_name()
    valid_df['hour'] = valid_df['created_at'].dt.hour
    
    # Count tickets by weekday and hour
    weekday_hour_counts = valid_df.groupby(['weekday', 'hour']).size().reset_index()
    weekday_hour_counts.columns = ['Weekday', 'Hour', 'Count']
    
    # Create a pivot table
    pivot_table = weekday_hour_counts.pivot(index='Weekday', columns='Hour', values='Count')
    
    # Order weekdays correctly
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot_table = pivot_table.reindex(weekday_order)
    
    # Fill NaN with zeros
    pivot_table = pivot_table.fillna(0)
    
    # Create the heatmap
    fig = px.imshow(
        pivot_table,
        labels=dict(x="Hour of Day", y="Day of Week", color="Ticket Count"),
        x=pivot_table.columns,
        y=pivot_table.index,
        title="Ticket Volume by Day and Hour",
        color_continuous_scale="Viridis"
    )
    
    fig.update_layout(
        xaxis=dict(tickvals=list(range(24))),
        margin=dict(t=50, b=50, l=100, r=10)
    )
    
    return fig
