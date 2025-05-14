"""
Root Cause Analysis (RCA) module for ServiceNow ticket data.
This module provides advanced RCA capabilities including:
- Incident pattern recognition
- Contributing factor analysis
- Timeline reconstruction
- Correlation analysis
- Recommendation generation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re
from collections import Counter, defaultdict

class RCAAnalyzer:
    """
    Root Cause Analysis engine for ServiceNow ticket data.
    """
    
    def __init__(self, ticket_data, llm_client=None):
        """
        Initialize the RCA analyzer with ticket data.
        
        Args:
            ticket_data: DataFrame containing the ServiceNow ticket data
            llm_client: Optional LLM client for advanced text analysis
        """
        self.ticket_data = ticket_data
        self.llm_client = llm_client
        self.original_columns = list(ticket_data.columns)
        
        # Ensure required date columns are datetime
        self._preprocess_data()
    
    def _preprocess_data(self):
        """Preprocess the ticket data for RCA analysis"""
        # Convert date columns to datetime
        date_columns = ['created_at', 'resolved_at', 'closed_at', 'updated_at']
        for col in date_columns:
            if col in self.ticket_data.columns:
                self.ticket_data[col] = pd.to_datetime(self.ticket_data[col], errors='coerce')
        
        # Create time-based features for analysis
        if 'created_at' in self.ticket_data.columns:
            # Extract time components
            self.ticket_data['created_hour'] = self.ticket_data['created_at'].dt.hour
            self.ticket_data['created_day'] = self.ticket_data['created_at'].dt.day_name()
            self.ticket_data['created_date'] = self.ticket_data['created_at'].dt.date
    
    def identify_related_tickets(self, incident_description, time_window=3, similarity_threshold=0.3):
        """
        Identify tickets related to the incident based on time proximity and content similarity.
        
        Args:
            incident_description: Description of the incident
            time_window: Number of days before and after to search
            similarity_threshold: Minimum text similarity threshold
            
        Returns:
            DataFrame with related tickets
        """
        # Extract potential date from incident description
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', incident_description)
        incident_date = None
        
        if date_match:
            # Try to parse the date from the description
            try:
                month, day, year = date_match.groups()
                if len(year) == 2:
                    year = '20' + year
                incident_date = pd.to_datetime(f"{year}-{month}-{day}")
            except:
                pass
        
        # If no valid date found, use text-based filtering
        if incident_date is None:
            # Extract key terms from incident description
            key_terms = self._extract_key_terms(incident_description)
            
            # Filter tickets based on key terms in description or short_description
            mask = pd.Series(False, index=self.ticket_data.index)
            
            if 'short_description' in self.ticket_data.columns:
                for term in key_terms:
                    mask |= self.ticket_data['short_description'].str.contains(term, case=False, na=False)
            
            if 'description' in self.ticket_data.columns:
                for term in key_terms:
                    mask |= self.ticket_data['description'].str.contains(term, case=False, na=False)
            
            related_tickets = self.ticket_data[mask].copy()
        else:
            # Use time-based filtering with the extracted date
            start_date = incident_date - timedelta(days=time_window)
            end_date = incident_date + timedelta(days=time_window)
            
            # Filter tickets by time window
            if 'created_at' in self.ticket_data.columns:
                time_mask = (
                    (self.ticket_data['created_at'] >= start_date) & 
                    (self.ticket_data['created_at'] <= end_date)
                )
                related_tickets = self.ticket_data[time_mask].copy()
            else:
                related_tickets = self.ticket_data.copy()
        
        # If we have the LLM client, use it for advanced filtering
        if self.llm_client and len(related_tickets) > 0 and 'description' in related_tickets.columns:
            # Further filter by semantic similarity if we have access to LLM
            # This would use the LLM to compute similarity between incident description
            # and ticket descriptions, but we'll skip the actual implementation here
            pass
        
        return related_tickets
    
    def _extract_key_terms(self, text):
        """Extract key terms from text for matching"""
        # Remove common words
        common_words = set(['the', 'and', 'is', 'in', 'to', 'a', 'for', 'of', 'on', 'with'])
        
        # Tokenize and clean text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Remove common words and keep terms with at least 4 characters
        key_terms = [word for word in words if word not in common_words and len(word) >= 4]
        
        # Count frequency
        word_counts = Counter(key_terms)
        
        # Return top terms
        return [word for word, _ in word_counts.most_common(10)]
    
    def analyze_incident_timeline(self, related_tickets):
        """
        Create a timeline of events related to the incident.
        
        Args:
            related_tickets: DataFrame containing related tickets
            
        Returns:
            Sorted list of timeline events
        """
        timeline = []
        
        # If we have ticket creation dates
        if 'created_at' in related_tickets.columns:
            for _, ticket in related_tickets.iterrows():
                event = {
                    'timestamp': ticket['created_at'],
                    'event_type': 'Ticket Created',
                    'ticket_id': ticket.get('number', ''),
                    'description': ticket.get('short_description', 'N/A')
                }
                timeline.append(event)
        
        # If we have ticket resolution dates
        if 'resolved_at' in related_tickets.columns:
            for _, ticket in related_tickets.iterrows():
                if pd.notna(ticket['resolved_at']):
                    event = {
                        'timestamp': ticket['resolved_at'],
                        'event_type': 'Ticket Resolved',
                        'ticket_id': ticket.get('number', ''),
                        'description': f"Resolution: {ticket.get('resolution', 'N/A')}"
                    }
                    timeline.append(event)
        
        # If we have ticket updates
        if 'updated_at' in related_tickets.columns:
            for _, ticket in related_tickets.iterrows():
                if pd.notna(ticket['updated_at']):
                    event = {
                        'timestamp': ticket['updated_at'],
                        'event_type': 'Ticket Updated',
                        'ticket_id': ticket.get('number', ''),
                        'description': f"Status: {ticket.get('status', 'N/A')}"
                    }
                    timeline.append(event)
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def identify_contributing_factors(self, related_tickets):
        """
        Identify potential contributing factors to the incident.
        
        Args:
            related_tickets: DataFrame containing related tickets
            
        Returns:
            Dictionary with contributing factors and their evidence
        """
        factors = {
            'time_patterns': self._analyze_time_patterns(related_tickets),
            'system_components': self._extract_system_components(related_tickets),
            'common_errors': self._extract_common_errors(related_tickets),
            'related_changes': self._identify_related_changes(related_tickets)
        }
        
        return factors
    
    def _analyze_time_patterns(self, tickets):
        """Analyze time-based patterns in the tickets"""
        patterns = {}
        
        if 'created_hour' in tickets.columns:
            # Analyze hour of day distribution
            hour_counts = tickets['created_hour'].value_counts()
            
            # Check for peak hours (hours with significantly more tickets)
            mean_tickets = hour_counts.mean()
            std_tickets = hour_counts.std()
            peak_hours = hour_counts[hour_counts > (mean_tickets + std_tickets)].to_dict()
            
            if peak_hours:
                patterns['peak_hours'] = {
                    'description': 'Hours with unusually high ticket volume',
                    'hours': peak_hours
                }
        
        if 'created_day' in tickets.columns:
            # Analyze day of week distribution
            day_counts = tickets['created_day'].value_counts().to_dict()
            patterns['day_distribution'] = day_counts
        
        return patterns
    
    def _extract_system_components(self, tickets):
        """Extract affected system components from tickets"""
        components = defaultdict(int)
        
        # Check for category field
        if 'category' in tickets.columns:
            category_counts = tickets['category'].value_counts().to_dict()
            for category, count in category_counts.items():
                components[f"Category: {category}"] = count
        
        # Check for subcategory field
        if 'subcategory' in tickets.columns:
            subcategory_counts = tickets['subcategory'].value_counts().to_dict()
            for subcategory, count in subcategory_counts.items():
                components[f"Subcategory: {subcategory}"] = count
        
        # Extract components from descriptions using regex patterns
        component_patterns = [
            r'(server|database|network|application|interface|API|service|cluster)',
            r'(authentication|authorization|login|access)',
            r'(timeout|latency|slow|performance)',
            r'(error|exception|failure|crash)'
        ]
        
        if 'description' in tickets.columns:
            for _, ticket in tickets.iterrows():
                desc = str(ticket.get('description', ''))
                for pattern in component_patterns:
                    matches = re.findall(pattern, desc, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, str):
                            components[match.capitalize()] += 1
        
        # Convert to sorted list of tuples
        sorted_components = sorted(components.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_components[:10])  # Return top 10
    
    def _extract_common_errors(self, tickets):
        """Extract common errors or issues from ticket descriptions"""
        error_patterns = {
            'timeouts': r'(timeout|timed? out)',
            'access_issues': r'(access denied|unauthorized|forbidden|permission)',
            'performance': r'(slow|performance|latency|delay)',
            'data_issues': r'(data (error|issue|problem|corrupt)|inconsistent data)',
            'crashes': r'(crash|abort|terminate|stop responding)',
            'connectivity': r'(connect(ion|ivity) (issue|problem|error)|unable to connect)',
            'authentication': r'(login|authentication|auth) (failed|issue|problem|error)'
        }
        
        errors = defaultdict(int)
        
        text_fields = ['short_description', 'description']
        for field in text_fields:
            if field in tickets.columns:
                for _, ticket in tickets.iterrows():
                    text = str(ticket.get(field, ''))
                    for error_type, pattern in error_patterns.items():
                        if re.search(pattern, text, re.IGNORECASE):
                            errors[error_type] += 1
        
        # Convert to dictionary
        return dict(errors)
    
    def _identify_related_changes(self, tickets):
        """Identify changes that might be related to the incident"""
        changes = []
        
        # Check for change tickets
        if 'category' in tickets.columns:
            change_tickets = tickets[tickets['category'].str.contains('change', case=False, na=False)]
            
            if not change_tickets.empty:
                for _, ticket in change_tickets.iterrows():
                    change = {
                        'ticket_id': ticket.get('number', ''),
                        'description': ticket.get('short_description', 'N/A'),
                        'date': ticket.get('created_at', None)
                    }
                    changes.append(change)
        
        # Also look for change-related words in descriptions
        change_patterns = [
            r'(after|following|recent) (upgrade|update|patch|deployment|release|change)',
            r'(implemented|installed|deployed|changed) (on|at)',
            r'(new version|release|build|deployment)'
        ]
        
        if 'description' in tickets.columns:
            for _, ticket in tickets.iterrows():
                desc = str(ticket.get('description', ''))
                for pattern in change_patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        change = {
                            'ticket_id': ticket.get('number', ''),
                            'description': ticket.get('short_description', 'N/A'),
                            'date': ticket.get('created_at', None),
                            'evidence': match.group(0) if match else "No evidence found"
                        }
                        changes.append(change)
        
        return changes
    
    def analyze_impact(self, related_tickets):
        """
        Analyze the impact of the incident.
        
        Args:
            related_tickets: DataFrame containing related tickets
            
        Returns:
            Dictionary with impact analysis
        """
        impact = {}
        
        # Ticket volume analysis
        impact['ticket_count'] = len(related_tickets)
        
        # Priority distribution
        if 'priority' in related_tickets.columns:
            impact['priority_distribution'] = related_tickets['priority'].value_counts().to_dict()
            
            # Calculate high priority percentage
            try:
                high_priority = related_tickets[related_tickets['priority'].isin([1, 2, '1', '2', 'Critical', 'High'])].shape[0]
                impact['high_priority_percentage'] = round((high_priority / len(related_tickets)) * 100, 2)
            except:
                pass
        
        # Affected users or systems
        if 'affected_user' in related_tickets.columns:
            impact['affected_user_count'] = related_tickets['affected_user'].nunique()
        
        # Resolution time
        if 'resolution_time_hours' in related_tickets.columns:
            resolution_times = related_tickets['resolution_time_hours'].dropna()
            if not resolution_times.empty:
                impact['avg_resolution_time'] = resolution_times.mean()
                impact['max_resolution_time'] = resolution_times.max()
        
        return impact
    
    def generate_rca_report(self, incident_description):
        """
        Generate a comprehensive RCA report for the given incident.
        
        Args:
            incident_description: Description of the incident
            
        Returns:
            Dictionary containing the full RCA report
        """
        # Step 1: Identify related tickets
        related_tickets = self.identify_related_tickets(incident_description)
        
        # Exit early if no related tickets found
        if len(related_tickets) == 0:
            return {
                "status": "insufficient_data",
                "message": "No related tickets found for this incident. Please provide more details or check the data."
            }
        
        # Step 2: Analyze the incident timeline
        timeline = self.analyze_incident_timeline(related_tickets)
        
        # Step 3: Identify contributing factors
        factors = self.identify_contributing_factors(related_tickets)
        
        # Step 4: Analyze impact
        impact = self.analyze_impact(related_tickets)
        
        # Step 5: Compile the report
        report = {
            "incident_description": incident_description,
            "related_tickets": len(related_tickets),
            "timeline": timeline,
            "contributing_factors": factors,
            "impact": impact,
            "sample_tickets": related_tickets.head(5).to_dict('records') if len(related_tickets) > 0 else []
        }
        
        return report

def format_rca_report_for_display(report):
    """
    Format the RCA report for display in Streamlit.
    
    Args:
        report: The RCA report dictionary
        
    Returns:
        Formatted markdown string for display
    """
    if report.get("status") == "insufficient_data":
        return f"## RCA Analysis: Insufficient Data\n\n{report['message']}"
    
    markdown = []
    
    # Header section
    markdown.append("# Root Cause Analysis Report")
    markdown.append(f"## Incident Overview")
    markdown.append(f"**Description:** {report['incident_description']}")
    markdown.append(f"**Related Tickets:** {report['related_tickets']}")
    
    # Impact section
    markdown.append(f"\n## Impact Analysis")
    impact = report['impact']
    markdown.append(f"**Total Tickets:** {impact['ticket_count']}")
    
    if 'high_priority_percentage' in impact:
        markdown.append(f"**High Priority Percentage:** {impact['high_priority_percentage']}%")
    
    if 'avg_resolution_time' in impact:
        markdown.append(f"**Average Resolution Time:** {impact['avg_resolution_time']:.2f} hours")
    
    if 'max_resolution_time' in impact:
        markdown.append(f"**Maximum Resolution Time:** {impact['max_resolution_time']:.2f} hours")
    
    # Timeline section
    markdown.append(f"\n## Incident Timeline")
    if report['timeline']:
        for event in report['timeline'][:10]:  # Limit to first 10 events
            timestamp = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(event['timestamp'], 'strftime') else event['timestamp']
            markdown.append(f"- **{timestamp}** - {event['event_type']}: {event['description']} ({event['ticket_id']})")
    else:
        markdown.append("No timeline data available")
    
    # Contributing Factors
    markdown.append(f"\n## Contributing Factors")
    
    # System Components
    markdown.append(f"\n### Affected System Components")
    components = report['contributing_factors']['system_components']
    if components:
        for component, count in components.items():
            markdown.append(f"- **{component}**: {count} tickets")
    else:
        markdown.append("No system component data available")
    
    # Time Patterns
    markdown.append(f"\n### Time Patterns")
    time_patterns = report['contributing_factors']['time_patterns']
    if 'peak_hours' in time_patterns:
        markdown.append(f"**Peak Hours:**")
        for hour, count in time_patterns['peak_hours']['hours'].items():
            markdown.append(f"- Hour {hour}: {count} tickets")
    
    # Common Errors
    markdown.append(f"\n### Common Errors")
    errors = report['contributing_factors']['common_errors']
    if errors:
        for error_type, count in errors.items():
            if count > 0:
                if isinstance(error_type, str):
                    error_display = error_type.replace('_', ' ').title()
                else:
                    error_display = str(error_type).title()
                markdown.append(f"- **{error_display}**: {count} tickets")
    else:
        markdown.append("No common error patterns detected")
    
    # Related Changes
    markdown.append(f"\n### Related Changes")
    changes = report['contributing_factors']['related_changes']
    if changes:
        for change in changes[:5]:  # Limit to 5 changes
            date = change['date'].strftime('%Y-%m-%d') if hasattr(change['date'], 'strftime') else change['date']
            markdown.append(f"- **{date}** - {change['description']} ({change['ticket_id']})")
            if 'evidence' in change:
                markdown.append(f"  - Evidence: \"{change['evidence']}\"")
    else:
        markdown.append("No related changes detected")
    
    # Root Cause Hypothesis
    markdown.append(f"\n## Root Cause Hypothesis")
    markdown.append("Based on the analysis of related tickets and contributing factors, the most likely root causes are:")
    
    # Generate hypotheses based on the common errors and affected components
    errors = report['contributing_factors']['common_errors']
    components = report['contributing_factors']['system_components']
    changes = report['contributing_factors']['related_changes']
    
    hypotheses = []
    
    # Create hypotheses based on errors and components
    if errors:
        top_error = max(errors.items(), key=lambda x: x[1]) if errors else (None, 0)
        if top_error[0] and top_error[1] > 0:
            if isinstance(top_error[0], str):
                error_name = top_error[0].replace('_', ' ').title()
            else:
                error_name = str(top_error[0]).title()
            hypotheses.append(f"**{error_name} Issues**: {top_error[1]} tickets reported problems related to {error_name.lower()}.")
    
    # Add component-related hypothesis
    if components:
        top_component = list(components.items())[0] if components else (None, 0)
        if top_component[0] and top_component[1] > 0:
            hypotheses.append(f"**{top_component[0]} Issues**: {top_component[1]} tickets were related to this component.")
    
    # Add change-related hypothesis
    if changes:
        hypotheses.append(f"**Recent Changes**: {len(changes)} potentially related changes were identified that may have contributed to the incident.")
    
    # Add time-based hypothesis
    if 'peak_hours' in time_patterns:
        peak_hours = time_patterns['peak_hours']['hours']
        peak_hour = max(peak_hours.items(), key=lambda x: x[1]) if peak_hours else (None, 0)
        if peak_hour[0] is not None:
            hypotheses.append(f"**Time-Based Pattern**: A significant number of tickets ({peak_hour[1]}) were created during hour {peak_hour[0]}, suggesting potential resource constraints or scheduled job issues.")
    
    # Add hypotheses to report
    if hypotheses:
        for hypothesis in hypotheses:
            markdown.append(f"- {hypothesis}")
    else:
        markdown.append("- Insufficient data to generate specific hypotheses")
    
    # Recommendations
    markdown.append(f"\n## Recommendations")
    
    # Generate recommendations based on the factors identified
    recommendations = [
        "**Review Recent Changes**: Investigate any recent changes or deployments that coincide with the incident timeframe.",
        "**Monitor System Components**: Implement enhanced monitoring for the affected system components.",
        "**Resource Allocation**: Evaluate resource allocation during peak hours to prevent similar incidents."
    ]
    
    # Add specific recommendations based on factors
    if errors and 'timeouts' in errors and errors['timeouts'] > 0:
        recommendations.append("**Connection Timeout Investigation**: Review connection timeout settings and network stability.")
    
    if errors and 'access_issues' in errors and errors['access_issues'] > 0:
        recommendations.append("**Access Control Review**: Audit authentication and authorization mechanisms.")
    
    for recommendation in recommendations:
        markdown.append(f"- {recommendation}")
    
    return "\n\n".join(markdown)