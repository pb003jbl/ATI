import pandas as pd
import numpy as np
from io import BytesIO
import re
from datetime import datetime
import streamlit as st

def load_data(uploaded_file):
    """
    Load data from uploaded file (CSV or Excel)
    
    Args:
        uploaded_file: The file uploaded through Streamlit
        
    Returns:
        pandas DataFrame with the loaded data
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    if file_type == 'csv':
        df = pd.read_csv(uploaded_file)
    elif file_type in ['xlsx', 'xls']:
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported file format: {file_type}")
    
    return df

def standardize_priority(df, column_name='priority'):
    priority_mapping = {
        '1-critical': 1, '1': 1, 'critical': 1,
        '2-high': 2, '2': 2, 'high': 2,
        '3-moderate': 3, '3': 3, 'moderate': 3,
        '4-low': 4, '4': 4, 'low': 4
    }

    df[column_name] = df[column_name].astype(str).str.replace(' ', '').str.strip().str.lower()
    df[column_name] = df[column_name].apply(lambda x: priority_mapping.get(x, x))

    # try to convert to numeric
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
 
    return df

def preprocess_data(df):
    """
    Preprocess the ServiceNow ticket data
    
    Args:
        df: Raw dataframe with ServiceNow ticket data
        
    Returns:
        Processed dataframe
    """
    # Create a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Convert column names to lowercase and replace spaces with underscores
    processed_df.columns = [col.lower().replace(' ', '_') for col in processed_df.columns]
    
    # Standardize common column names
    column_mapping = {
        'incident_number': 'number',
        'ticket_number': 'number',
        'id': 'number',
        'summary': 'short_description',
        'title': 'short_description',
        'issue': 'short_description',
        'details': 'description',
        'state': 'status',
        'priority_level': 'priority',
        'urgency': 'priority',
        'issue_category': 'category',
        'type': 'category',
        'sub_category': 'subcategory',
        'assignee': 'assigned_to',
        'owner': 'assigned_to',
        'created_date': 'created_at',
        'opened_at': 'created_at',
        'open_time': 'created_at',
        'resolved_date': 'resolved_at',
        'closed_at': 'resolved_at',
        'close_time': 'resolved_at'
    }
    
    # Apply the column mapping where columns exist
    for old_col, new_col in column_mapping.items():
        if old_col in processed_df.columns and new_col not in processed_df.columns:
            processed_df = processed_df.rename(columns={old_col: new_col})
    
    # Handle date columns
    date_columns = ['created_at', 'resolved_at', 'updated_at', 'closed_at']
    for col in date_columns:
        if col in processed_df.columns:
            try:
                processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce')
            except:
                pass
    
    # Calculate resolution time if both created_at and resolved_at are present
    if 'created_at' in processed_df.columns and 'resolved_at' in processed_df.columns:
        valid_dates = ~processed_df['created_at'].isna() & ~processed_df['resolved_at'].isna()
        if valid_dates.any():
            processed_df.loc[valid_dates, 'resolution_time_hours'] = (
                processed_df.loc[valid_dates, 'resolved_at'] - 
                processed_df.loc[valid_dates, 'created_at']
            ).dt.total_seconds() / 3600
    
    # Standardize status values
    if 'status' in processed_df.columns:
        status_mapping = {
            'new': 'Open',
            'open': 'Open',
            'in progress': 'In Progress',
            'in-progress': 'In Progress',
            'pending': 'In Progress',
            'on hold': 'In Progress',
            'awaiting user info': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed',
            'cancelled': 'Closed',
            'canceled': 'Closed'
        }
        
        processed_df['status'] = processed_df['status'].astype(str).str.lower()
        processed_df['status'] = processed_df['status'].map(
            lambda x: status_mapping.get(x, x.capitalize())
        )
    
    # Standardize priority values
    if 'priority' in processed_df.columns:
        # Try to convert to numeric if possible
        try:
            processed_df = standardize_priority(processed_df, 'priority')
            # processed_df['priority'] = pd.to_numeric(processed_df['priority'], errors='coerce')
        except:
            pass
        
        # If the priority is not numeric, try to map common values
        # if processed_df['priority'].dtype == 'object':
        #     priority_mapping = {
        #         'critical': 1,
        #         'high': 2,
        #         'medium': 3,
        #         'normal': 3,
        #         'low': 4,
        #         'planning': 5
        #     }
            
        #     processed_df['priority'] = processed_df['priority'].astype(str).str.lower()
        #     processed_df['priority'] = processed_df['priority'].map(
        #         lambda x: priority_mapping.get(x, x)
        #     )
    
    return processed_df

def extract_keywords(df, text_column='short_description', n_keywords=20):
    """
    Extract common keywords from text columns
    
    Args:
        df: DataFrame with ticket data
        text_column: Column containing text to analyze
        n_keywords: Number of top keywords to return
        
    Returns:
        Dictionary with keywords and their frequencies
    """
    if text_column not in df.columns:
        return {}
    
    # Combine all text into a single string
    all_text = ' '.join(df[text_column].astype(str).tolist())
    
    # Basic preprocessing
    all_text = all_text.lower()
    # Remove special characters
    all_text = re.sub(r'[^\w\s]', ' ', all_text)
    
    # Split into words
    words = all_text.split()
    
    # Remove common stopwords
    stopwords = {'the', 'and', 'is', 'in', 'to', 'for', 'of', 'a', 'with', 'on', 'an', 'this', 'that', 
                'are', 'as', 'at', 'be', 'by', 'from', 'has', 'have', 'i', 'it', 'not', 'was', 'were'}
    
    filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
    
    # Count frequencies
    word_counts = {}
    for word in filtered_words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    
    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N keywords
    return dict(sorted_words[:n_keywords])

def get_time_metrics(df):
    """
    Calculate time-based metrics for tickets
    
    Args:
        df: DataFrame with processed ticket data
        
    Returns:
        Dictionary with time metrics
    """
    metrics = {}
    
    if 'created_at' not in df.columns:
        return metrics
    
    # Ensure date column is datetime
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    
    # Filter out rows with invalid dates
    valid_df = df.dropna(subset=['created_at'])
    
    if valid_df.empty:
        return metrics
    
    # Tickets per day
    valid_df['date'] = valid_df['created_at'].dt.date
    tickets_per_day = valid_df.groupby('date').size()
    metrics['avg_tickets_per_day'] = tickets_per_day.mean()
    
    # Resolution time metrics
    if 'resolution_time_hours' in valid_df.columns:
        resolution_times = valid_df.dropna(subset=['resolution_time_hours'])
        
        if not resolution_times.empty:
            metrics['avg_resolution_time'] = resolution_times['resolution_time_hours'].mean()
            metrics['median_resolution_time'] = resolution_times['resolution_time_hours'].median()
    
    # Tickets by weekday
    valid_df['weekday'] = valid_df['created_at'].dt.day_name()
    weekday_counts = valid_df.groupby('weekday').size()
    metrics['tickets_by_weekday'] = weekday_counts.to_dict()
    
    # Tickets by hour of day
    valid_df['hour'] = valid_df['created_at'].dt.hour
    hour_counts = valid_df.groupby('hour').size()
    metrics['tickets_by_hour'] = hour_counts.to_dict()
    
    return metrics

def get_category_metrics(df):
    """
    Calculate category-based metrics
    
    Args:
        df: DataFrame with processed ticket data
        
    Returns:
        Dictionary with category metrics
    """
    metrics = {}
    
    # Category distribution
    if 'category' in df.columns:
        category_counts = df['category'].value_counts().to_dict()
        metrics['category_distribution'] = category_counts
    
    # Priority distribution
    if 'priority' in df.columns:
        priority_counts = df['priority'].value_counts().to_dict()
        metrics['priority_distribution'] = priority_counts
    
    # Status distribution
    if 'status' in df.columns:
        status_counts = df['status'].value_counts().to_dict()
        metrics['status_distribution'] = status_counts
    
    # Cross-tabulation of category and priority
    if 'category' in df.columns and 'priority' in df.columns:
        crosstab = pd.crosstab(df['category'], df['priority']).to_dict()
        metrics['category_priority_distribution'] = crosstab
    
    return metrics

def prepare_data_for_agents(df):
    """
    Prepare data in a format suitable for agent processing
    
    Args:
        df: DataFrame with ticket data
        
    Returns:
        Dictionary with structured data that is JSON serializable
    """
    # Basic info
    data_dict = {
        'total_tickets': len(df),
        'columns': list(df.columns),
    }
    
    # Helper function to make values JSON serializable
    def make_json_serializable(obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return obj
    
    # Add sample of tickets (limit to 5 for performance)
    # Convert to dict and then make values JSON serializable
    sample_data = df.head(5).to_dict(orient='records')
    sample_data = make_json_serializable(sample_data)
    data_dict['sample_data'] = sample_data
    
    # Add metrics
    time_metrics = get_time_metrics(df)
    category_metrics = get_category_metrics(df)
    
    # Make sure all metrics are JSON serializable
    time_metrics = make_json_serializable(time_metrics)
    category_metrics = make_json_serializable(category_metrics)
    
    data_dict.update({
        'time_metrics': time_metrics,
        'category_metrics': category_metrics
    })
    
    # Extract keywords
    if 'short_description' in df.columns:
        keywords = extract_keywords(df, 'short_description')
        data_dict['common_keywords'] = keywords
    
    return data_dict
