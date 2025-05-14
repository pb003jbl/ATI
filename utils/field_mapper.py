"""
Field mapping module for ServiceNow ticket data.
This module handles the mapping between uploaded data fields and standard fields
required for analysis.
"""

import pandas as pd
import streamlit as st
import json
from typing import Dict, List, Optional, Tuple

# Define the standard fields required for different analysis features
STANDARD_FIELDS = {
    "basic": [
        "number", 
        "short_description",
        "status",
        "priority"
    ],
    "time_analysis": [
        "created_at",
        "resolved_at"
    ],
    "categorization": [
        "category",
        "subcategory"
    ],
    "assignment": [
        "assigned_to",
        "assignment_group"
    ],
    "description": [
        "description"
    ]
}

# Define field descriptions for the UI
FIELD_DESCRIPTIONS = {
    "number": "Unique ticket identifier (INC123456, etc.)",
    "short_description": "Brief summary of the ticket",
    "description": "Detailed description of the issue",
    "status": "Current ticket status (Open, In Progress, Closed, etc.)",
    "priority": "Ticket priority level (1-Critical, 2-High, etc.)",
    "category": "Main issue category",
    "subcategory": "Subcategory or more specific issue type",
    "assigned_to": "Person assigned to the ticket",
    "assignment_group": "Team or group assigned to the ticket",
    "created_at": "Date and time the ticket was created",
    "resolved_at": "Date and time the ticket was resolved",
    "closed_at": "Date and time the ticket was closed"
}

# Define suggested mappings for common ServiceNow variations
SUGGESTED_MAPPINGS = {
    "incident_number": "number",
    "ticket_number": "number",
    "id": "number",
    "summary": "short_description",
    "title": "short_description",
    "issue": "short_description",
    "details": "description",
    "state": "status",
    "ticket_state": "status",
    "priority_level": "priority",
    "urgency": "priority",
    "issue_category": "category",
    "type": "category",
    "subtype": "subcategory",
    "sub_category": "subcategory",
    "assignee": "assigned_to",
    "owner": "assigned_to",
    "assigned_group": "assignment_group",
    "support_group": "assignment_group",
    "team": "assignment_group",
    "created_date": "created_at", 
    "opened_at": "created_at",
    "open_time": "created_at",
    "creation_date": "created_at",
    "resolved_date": "resolved_at",
    "resolution_date": "resolved_at",
    "closed_date": "closed_at",
    "close_time": "closed_at"
}

def get_required_fields_by_feature(feature: str = "all") -> List[str]:
    """
    Get the list of required fields for a specific analysis feature.
    
    Args:
        feature: The analysis feature name (basic, time_analysis, etc.) or "all"
        
    Returns:
        List of required fields for the specified feature
    """
    if feature == "all":
        # Combine all field lists without duplicates
        all_fields = []
        for field_list in STANDARD_FIELDS.values():
            for field in field_list:
                if field not in all_fields:
                    all_fields.append(field)
        return all_fields
    elif feature in STANDARD_FIELDS:
        return STANDARD_FIELDS[feature]
    else:
        return []

def analyze_dataframe_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Analyze a dataframe to categorize its columns and suggest mappings.
    
    Args:
        df: Dataframe to analyze
        
    Returns:
        Dictionary with column categories and mapping suggestions
    """
    # Initialize result container
    result = {
        "available_columns": list(df.columns),
        "suggested_mappings": {},
        "mapped_fields": {},
        "missing_fields": []
    }
    
    # Convert column names to lowercase for case-insensitive matching
    lowercase_columns = {col.lower(): col for col in df.columns}
    
    # First pass: match exact column names with standard fields
    standard_fields = get_required_fields_by_feature("all")
    for field in standard_fields:
        if field in df.columns:
            result["mapped_fields"][field] = field
        elif field.lower() in lowercase_columns:
            result["mapped_fields"][field] = lowercase_columns[field.lower()]
    
    # Second pass: suggest mappings based on known variations
    for col in df.columns:
        col_lower = col.lower()
        # Check if this column name is in our suggested mappings list
        if col_lower in SUGGESTED_MAPPINGS:
            standard_field = SUGGESTED_MAPPINGS[col_lower]
            if standard_field not in result["mapped_fields"]:
                result["suggested_mappings"][col] = standard_field
    
    # Third pass: identify missing required fields
    for field in standard_fields:
        if field not in result["mapped_fields"] and field not in [v for _, v in result["suggested_mappings"].items()]:
            result["missing_fields"].append(field)
    
    return result

def apply_field_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Apply field mapping to a dataframe, renaming columns according to the mapping.
    
    Args:
        df: Original dataframe
        mapping: Dictionary mapping original column names to standard field names
        
    Returns:
        Dataframe with renamed columns
    """
    # Create a copy of the dataframe to avoid modifying the original
    mapped_df = df.copy()
    
    # Create a reverse mapping (standard field name -> original column)
    reverse_mapping = {v: k for k, v in mapping.items()}
    
    # Rename columns based on the mapping
    mapped_df.rename(columns=reverse_mapping, inplace=True)
    
    return mapped_df

def create_field_mapping_ui(df: pd.DataFrame) -> Tuple[Dict[str, str], bool]:
    """
    Create a Streamlit UI for mapping data fields.
    
    Args:
        df: Dataframe containing uploaded data
        
    Returns:
        Dictionary mapping standard fields to original columns, and a boolean indicating if mapping is complete
    """
    # Analyze the dataframe
    analysis = analyze_dataframe_columns(df)
    
    st.subheader("Field Mapping")
    st.write("Map your data fields to the standard fields required for analysis.")
    
    # Show automatically mapped fields
    if analysis["mapped_fields"]:
        st.write("#### Automatically Detected Fields")
        auto_mapped = ", ".join([f"{v} → {k}" for k, v in analysis["mapped_fields"].items()])
        st.success(f"The following fields were automatically detected: {auto_mapped}")
    
    # Initialize mapping in session state if not already there
    if "field_mapping" not in st.session_state:
        # Start with automatically mapped fields
        st.session_state.field_mapping = analysis["mapped_fields"].copy()
        # Add suggested mappings
        for orig_col, std_field in analysis["suggested_mappings"].items():
            if std_field not in st.session_state.field_mapping:
                st.session_state.field_mapping[std_field] = orig_col
    
    # Create UI for required fields
    st.write("#### Required Fields Mapping")
    st.write("These fields are essential for core functionality:")
    
    # Group fields by feature for better organization
    mapping_complete = True
    
    # First, handle the most critical fields
    basic_fields = get_required_fields_by_feature("basic")
    for field in basic_fields:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(f"**{field}**")
            st.caption(FIELD_DESCRIPTIONS.get(field, ""))
        with col2:
            default_value = st.session_state.field_mapping.get(field, "")
            available_columns = [""] + list(df.columns)
            selected_column = st.selectbox(
                f"Map to column for {field}",
                available_columns,
                index=available_columns.index(default_value) if default_value in available_columns else 0,
                key=f"mapping_{field}"
            )
            if selected_column:
                st.session_state.field_mapping[field] = selected_column
            elif field in st.session_state.field_mapping:
                del st.session_state.field_mapping[field]
            
            # Check if this required field is mapped
            if not selected_column:
                mapping_complete = False
    
    # Create expandable sections for other field groups
    with st.expander("Time-Based Analysis Fields", expanded=False):
        st.write("These fields are used for time-based analysis and resolution metrics:")
        time_fields = get_required_fields_by_feature("time_analysis")
        for field in time_fields:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**{field}**")
                st.caption(FIELD_DESCRIPTIONS.get(field, ""))
            with col2:
                default_value = st.session_state.field_mapping.get(field, "")
                available_columns = [""] + list(df.columns)
                selected_column = st.selectbox(
                    f"Map to column for {field}",
                    available_columns,
                    index=available_columns.index(default_value) if default_value in available_columns else 0,
                    key=f"mapping_{field}"
                )
                if selected_column:
                    st.session_state.field_mapping[field] = selected_column
                elif field in st.session_state.field_mapping:
                    del st.session_state.field_mapping[field]
    
    with st.expander("Categorization Fields", expanded=False):
        st.write("These fields are used for categorizing and grouping tickets:")
        cat_fields = get_required_fields_by_feature("categorization")
        for field in cat_fields:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**{field}**")
                st.caption(FIELD_DESCRIPTIONS.get(field, ""))
            with col2:
                default_value = st.session_state.field_mapping.get(field, "")
                available_columns = [""] + list(df.columns)
                selected_column = st.selectbox(
                    f"Map to column for {field}",
                    available_columns,
                    index=available_columns.index(default_value) if default_value in available_columns else 0,
                    key=f"mapping_{field}"
                )
                if selected_column:
                    st.session_state.field_mapping[field] = selected_column
                elif field in st.session_state.field_mapping:
                    del st.session_state.field_mapping[field]
    
    with st.expander("Assignment Fields", expanded=False):
        st.write("These fields are used for analyzing assignment patterns:")
        assign_fields = get_required_fields_by_feature("assignment")
        for field in assign_fields:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**{field}**")
                st.caption(FIELD_DESCRIPTIONS.get(field, ""))
            with col2:
                default_value = st.session_state.field_mapping.get(field, "")
                available_columns = [""] + list(df.columns)
                selected_column = st.selectbox(
                    f"Map to column for {field}",
                    available_columns,
                    index=available_columns.index(default_value) if default_value in available_columns else 0,
                    key=f"mapping_{field}"
                )
                if selected_column:
                    st.session_state.field_mapping[field] = selected_column
                elif field in st.session_state.field_mapping:
                    del st.session_state.field_mapping[field]
    
    with st.expander("Description Fields", expanded=False):
        st.write("These fields are used for text analysis and keyword extraction:")
        desc_fields = get_required_fields_by_feature("description")
        for field in desc_fields:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write(f"**{field}**")
                st.caption(FIELD_DESCRIPTIONS.get(field, ""))
            with col2:
                default_value = st.session_state.field_mapping.get(field, "")
                available_columns = [""] + list(df.columns)
                selected_column = st.selectbox(
                    f"Map to column for {field}",
                    available_columns,
                    index=available_columns.index(default_value) if default_value in available_columns else 0,
                    key=f"mapping_{field}"
                )
                if selected_column:
                    st.session_state.field_mapping[field] = selected_column
                elif field in st.session_state.field_mapping:
                    del st.session_state.field_mapping[field]
    
    # Create field for saving/loading mappings
    with st.expander("Save/Load Mapping Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Save Current Mapping")
            mapping_name = st.text_input("Mapping Name", value="My ServiceNow Mapping")
            if st.button("Save Mapping"):
                if "saved_mappings" not in st.session_state:
                    st.session_state.saved_mappings = {}
                
                st.session_state.saved_mappings[mapping_name] = st.session_state.field_mapping.copy()
                st.success(f"Mapping '{mapping_name}' saved!")
        
        with col2:
            st.write("#### Load Saved Mapping")
            if "saved_mappings" in st.session_state and st.session_state.saved_mappings:
                selected_mapping = st.selectbox(
                    "Select a saved mapping",
                    options=list(st.session_state.saved_mappings.keys())
                )
                
                if st.button("Load Mapping"):
                    st.session_state.field_mapping = st.session_state.saved_mappings[selected_mapping].copy()
                    st.success(f"Mapping '{selected_mapping}' loaded!")
            else:
                st.info("No saved mappings yet.")
        
        # Option to export mapping as JSON
        if "field_mapping" in st.session_state and st.session_state.field_mapping:
            mapping_json = json.dumps(st.session_state.field_mapping, indent=2)
            st.download_button(
                label="Download Mapping as JSON",
                data=mapping_json,
                file_name="servicenow_field_mapping.json",
                mime="application/json"
            )
    
    return st.session_state.field_mapping, mapping_complete

def get_mapped_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the mapping from session state to a dataframe
    
    Args:
        df: Original dataframe
        
    Returns:
        Dataframe with standard field names
    """
    # Create a copy of the dataframe
    result_df = df.copy()
    
    # If we have field mappings in the session state
    if "field_mapping" in st.session_state:
        # Rename columns based on the field mappings (reversed)
        column_renames = {}
        for std_field, orig_col in st.session_state.field_mapping.items():
            # Make sure the original column exists in the dataframe
            if orig_col in df.columns:
                column_renames[orig_col] = std_field
        
        # Apply the renames
        if column_renames:
            result_df = result_df.rename(columns=column_renames)
    
    return result_df