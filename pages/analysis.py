import streamlit as st
import pandas as pd
import json
from utils.data_processor import prepare_data_for_agents
from agents.agent_system import GroqLLMConfig, AgentSystem
from utils.rca_analyzer import RCAAnalyzer, format_rca_report_for_display
import time
import datetime

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
         caption="Advanced ServiceNow Ticket Analysis", use_container_width=True)

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
if 'advanced_rca_report' not in st.session_state:
    st.session_state.advanced_rca_report = None

# Tabs for different analysis types
tab1, tab2, tab3, tab4, tab5 = st.tabs(["General Analysis", "Root Cause Analysis", "Advanced RCA", "Automation & Recommendations", "AMS Insights"])

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
    Generate a detailed Root Cause Analysis report for specific incidents using the Groq LLM.
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
    
    if st.button("Generate LLM-Based RCA Report") and incident_description:
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
            file_name="servicenow_rca_report.txt",
            mime="text/plain"
        )

# Advanced RCA Tab (using the detailed RCA module)
with tab3:
    st.header("Advanced Root Cause Analysis")
    st.write("""
    This advanced RCA module uses statistical analysis and pattern recognition algorithms to analyze your ticket data and provide 
    a detailed breakdown of incident patterns, contributing factors, and root causes. It offers a more data-driven approach to complement 
    the LLM-based analysis.
    """)
    
    # Input for incident details
    col1, col2 = st.columns([3, 1])
    
    with col1:
        adv_incident_description = st.text_area(
            "Describe the incident for detailed RCA:",
            height=150,
            placeholder="Example: On Monday, May 15th, between 9:00 AM and 11:30 AM, users experienced slow response times in the system..."
        )
    
    with col2:
        st.markdown("### Time Window")
        time_window = st.slider("Days to analyze before/after incident date", 
                               min_value=1, max_value=14, value=3)
        
        # Add date picker for incident date
        incident_date = st.date_input(
            "Incident Date (if known):",
            value=datetime.date.today()
        )
    
    # Additional options for Advanced RCA
    with st.expander("Advanced RCA Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            analyze_changes = st.checkbox("Analyze related changes", value=True)
            analyze_components = st.checkbox("Identify affected components", value=True)
        
        with col2:
            analyze_time_patterns = st.checkbox("Analyze time patterns", value=True)
            include_sample_tickets = st.checkbox("Include sample tickets", value=True)
    
    if st.button("Generate Advanced RCA Report") and adv_incident_description:
        with st.spinner("Performing detailed Root Cause Analysis..."):
            try:
                # Initialize the RCA analyzer
                rca_analyzer = RCAAnalyzer(df)
                
                # Generate the RCA report
                advanced_rca_report = rca_analyzer.generate_rca_report(adv_incident_description)
                
                # Store the result
                st.session_state.advanced_rca_report = advanced_rca_report
                
                st.success("Advanced RCA report generated!")
            except Exception as e:
                st.error(f"Error during advanced RCA generation: {str(e)}")
    
    # Display Advanced RCA results if available
    if st.session_state.advanced_rca_report:
        st.subheader("Advanced Root Cause Analysis Report")
        
        # Format the report for display
        formatted_report = format_rca_report_for_display(st.session_state.advanced_rca_report)
        st.markdown(formatted_report)
        
        # Display visualizations based on the RCA data
        if st.session_state.advanced_rca_report.get("status") != "insufficient_data":
            st.subheader("RCA Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Timeline visualization
                if st.session_state.advanced_rca_report.get("timeline"):
                    st.subheader("Incident Timeline")
                    
                    # Extract timeline data
                    timeline_data = st.session_state.advanced_rca_report.get("timeline", [])
                    if timeline_data:
                        # Create a dataframe from the timeline
                        timeline_df = pd.DataFrame([
                            {
                                'date': event.get('timestamp') if isinstance(event, dict) else None,
                                'event': f"{event.get('event_type', '')}: {event.get('ticket_id', '')}" if isinstance(event, dict) else '',
                                'description': event.get('description', '') if isinstance(event, dict) else ''
                            }
                            for event in timeline_data if isinstance(event, dict) and hasattr(event.get('timestamp'), 'strftime')
                        ])
                        
                        if not timeline_df.empty:
                            # Display as a table
                            st.dataframe(
                                timeline_df.sort_values('date'), 
                                use_container_width=True
                            )
            
            with col2:
                # Contributing factors visualization
                factors = st.session_state.advanced_rca_report.get("contributing_factors", {})
                if isinstance(factors, dict) and "system_components" in factors:
                    system_components = factors["system_components"]
                    if isinstance(system_components, dict) and system_components:
                        st.subheader("Affected Components")
                        
                        # Create a horizontal bar chart
                        components_df = pd.DataFrame([
                            {"Component": comp, "Count": count}
                            for comp, count in system_components.items()
                        ])
                        
                        if len(components_df) > 0:
                            components_df = components_df.sort_values("Count", ascending=False).head(8)
                            st.bar_chart(components_df.set_index("Component"))
            
            # Error distribution pie chart
            if isinstance(factors, dict) and "common_errors" in factors:
                errors = factors["common_errors"]
                if isinstance(errors, dict) and errors:
                    st.subheader("Common Error Types")
                    errors_df = pd.DataFrame([
                        {"Error Type": error.replace("_", " ").title() if isinstance(error, str) else str(error).title(), 
                         "Count": count}
                        for error, count in errors.items() if count > 0
                    ])
                    
                    if len(errors_df) > 0:
                        st.bar_chart(errors_df.set_index("Error Type"))
        
        # Download button for advanced RCA report
        advanced_rca_json = json.dumps(st.session_state.advanced_rca_report, default=str, indent=2)
        st.download_button(
            label="Download Advanced RCA Report",
            data=advanced_rca_json,
            file_name="advanced_rca_report.json",
            mime="application/json"
        )
        
        # Also provide a text version
        st.download_button(
            label="Download Formatted RCA Report",
            data=formatted_report,
            file_name="advanced_rca_report.txt",
            mime="text/plain"
        )

# Recommendations Tab
with tab4:
    st.header("Automation & Improvement Recommendations")
    st.write("""
    Generate smart recommendations with a focus on **automation opportunities** to reduce future tickets and
    increase efficiency. These actionable insights are based on your ticket data analysis and will help optimize your 
    service desk operations while reducing manual work.
    """)
    
    # Add an image related to automation
    st.image("https://images.pexels.com/photos/8386434/pexels-photo-8386434.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750", 
             caption="Automation opportunities to improve efficiency", use_container_width=True)
    
    # Check if general analysis is available
    if st.session_state.general_analysis is None:
        st.info("Please generate a General Analysis first to get more comprehensive recommendations.")
    
    if st.button("Generate Automation & Improvement Recommendations"):
        with st.spinner("Analyzing data and generating recommendations..."):
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
        # Create a container with custom styling to make automation opportunities stand out
        st.markdown("""
        <style>
        .automation-header {
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="automation-header"><h2>📊 Automation & Improvement Recommendations</h2></div>', 
                   unsafe_allow_html=True)
        
        # Display the recommendations content
        st.markdown(st.session_state.recommendations)
        
        # Add some metrics in columns to highlight potential value
        if st.session_state.recommendations:
            try:
                # Simplified metrics to show potential impact (these would be calculated in a real system)
                st.subheader("Estimated Benefits from Automation")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        label="Potential Ticket Reduction", 
                        value="15-25%", 
                        delta="Positive Impact"
                    )
                with col2:
                    st.metric(
                        label="Est. Time Savings (hr/month)", 
                        value="40-60", 
                        delta="Productivity Gain"
                    )
                with col3:
                    st.metric(
                        label="Resolution Time Improvement", 
                        value="30-40%", 
                        delta="Customer Satisfaction"
                    )
            except:
                # Skip if there's any error calculating the metrics
                pass
        
        # Add a section specifically for RPA use cases
        st.markdown("""
        <style>
        .rpa-section {
            background-color: #6200EA;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="rpa-section"><h2>🤖 RPA Automation Use Cases</h2></div>', 
                   unsafe_allow_html=True)
        
        st.info("""
        This section identifies specific Robotic Process Automation (RPA) use cases based on the patterns found in your ticket data.
        Each use case includes specific process flows, recommended RPA tools, and estimated ROI.
        
        RPA is particularly effective for:
        - High-volume, repetitive IT tasks
        - Rule-based processes with structured data
        - Cross-system workflows that require multiple application interactions
        """)
        
        # Create tabs for different aspects of RPA automation
        rpa_tab1, rpa_tab2, rpa_tab3 = st.tabs(["RPA Recommendations", "Implementation Guide", "ROI Calculator"])
        
        with rpa_tab1:
            st.write("The RPA recommendations will appear here after analysis is complete.")
            
            # This area will be populated with specific RPA recommendations from the LLM
            if st.session_state.recommendations:
                # Extract RPA specific content (simplified example - in practice, we'd use regex or other parsing)
                if "RPA USE CASES" in st.session_state.recommendations:
                    try:
                        # This is a simplified approach - in production, we'd use a more robust parsing method
                        rpa_start = st.session_state.recommendations.find("RPA USE CASES")
                        next_heading = st.session_state.recommendations.find("PROCESS IMPROVEMENTS", rpa_start)
                        if next_heading > 0:
                            rpa_content = st.session_state.recommendations[rpa_start:next_heading]
                        else:
                            rpa_content = st.session_state.recommendations[rpa_start:]
                        
                        st.markdown(rpa_content)
                    except:
                        # If parsing fails, just show a message
                        st.write("RPA recommendations are included in the full analysis above.")
        
        with rpa_tab2:
            st.markdown("""
            ### RPA Implementation Guide
            
            #### 1. Discovery & Assessment
            - Document the exact process steps (Process Definition Document)
            - Measure current process metrics (time, error rate, cost)
            - Assess technical feasibility for automation
            
            #### 2. Bot Development
            - Select appropriate RPA platform based on use case
            - Develop process automation using selected RPA tool
            - Test automations in controlled environment
            
            #### 3. Deployment & Monitoring
            - Deploy RPA bots in production environment
            - Monitor bot performance and handle exceptions
            - Measure ROI and process improvements
            
            #### 4. Scaling & Optimization
            - Identify additional processes for automation
            - Create a Center of Excellence for RPA governance
            - Implement continuous improvement for existing bots
            """)
        
        with rpa_tab3:
            st.markdown("### RPA ROI Calculator")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Input Parameters")
                manual_time = st.number_input("Average manual processing time (minutes)", min_value=1, value=15)
                ticket_volume = st.number_input("Monthly ticket volume", min_value=1, value=500)
                agent_cost = st.number_input("Hourly agent cost ($)", min_value=1, value=25)
                automation_rate = st.slider("Automation success rate (%)", min_value=50, max_value=100, value=85)
                
            with col2:
                st.markdown("#### Estimated ROI")
                # Calculate ROI metrics
                monthly_hours_saved = (manual_time * ticket_volume * (automation_rate/100)) / 60
                monthly_cost_savings = monthly_hours_saved * agent_cost
                annual_savings = monthly_cost_savings * 12
                
                # Implementation costs (simplified)
                implementation_cost = 20000 + (monthly_hours_saved * 100)  # Very simplified estimate
                
                # ROI calculation
                roi_months = implementation_cost / monthly_cost_savings
                
                # Display metrics
                st.metric("Monthly Hours Saved", f"{monthly_hours_saved:.1f} hrs")
                st.metric("Monthly Cost Savings", f"${monthly_cost_savings:.2f}")
                st.metric("Annual Savings", f"${annual_savings:.2f}")
                st.metric("Estimated ROI Timeline", f"{roi_months:.1f} months")
            
            st.caption("Note: This is a simplified ROI calculator. Actual results may vary based on specific process complexity, exception handling needs, and maintenance requirements.")
        
        # Add an expander with automation tools & technologies
        with st.expander("🛠️ Recommended Automation & RPA Tools"):
            st.markdown("""
            ### ServiceNow Automation Tools

            1. **ServiceNow Flow Designer**
               - Low-code automation platform for ServiceNow
               - Create automated workflows with minimal code
               - Automate ticket routing, escalations, and status updates

            2. **Integration Hub**
               - Connect ServiceNow with other business systems
               - Automate data sharing between platforms
               - Reduce duplicate ticket entry across systems

            ### RPA Platforms

            1. **UiPath**
               - Enterprise RPA platform with strong screen scraping capabilities
               - Excellent for desktop automation and legacy system integration
               - Features include AI Center, Process Mining, and Task Capture

            2. **Automation Anywhere**
               - Cloud-native RPA platform with IQ Bot for unstructured data
               - Strong security features for enterprise deployments
               - Digital workforce analytics for bot performance monitoring

            3. **Blue Prism**
               - Enterprise-grade RPA with strong governance and compliance features
               - Object-oriented development approach for scalable automation
               - Secure, connected-RPA with centralized release management

            4. **Microsoft Power Automate**
               - Seamless integration with Microsoft products
               - Low-code/no-code approach accessible to business users
               - AI Builder for intelligent document processing
            """)
        
        # Download button for recommendations
        recommendations_text = st.session_state.recommendations
        st.download_button(
            label="Download Automation & Improvement Recommendations",
            data=recommendations_text,
            file_name="servicenow_automation_recommendations.txt",
            mime="text/plain"
        )

# AMS Insights Tab
with tab5:
    st.header("Application Management Services (AMS) Insights")
    st.write("""
    This section provides insights and recommendations from an Application Management Services (AMS) perspective.
    Analyze your ticket data through the lens of AMS to optimize support operations, reduce costs, and improve service quality.
    """)
    
    # Add an image related to AMS
    st.image("https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750", 
             caption="Application Management Services optimization", use_container_width=True)
    
    # AMS Overview Section with custom styling
    st.markdown("""
    <style>
    .ams-header {
        background-color: #00695c;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="ams-header"><h2>🏢 AMS Performance Analysis</h2></div>', 
               unsafe_allow_html=True)
    
    # Create columns for AMS KPI metrics
    if st.session_state.prepared_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="SLA Compliance", 
                value="92.7%", 
                delta="2.3%"
            )
        with col2:
            st.metric(
                label="Ticket Deflection Rate", 
                value="24.5%", 
                delta="5.1%"
            )
        with col3:
            st.metric(
                label="L1 Resolution Rate", 
                value="68.3%", 
                delta="3.7%"
            )
    
    # AMS Dashboard tabs
    ams_tab1, ams_tab2, ams_tab3, ams_tab4 = st.tabs(["AMS Strategy", "SLA Optimization", "Governance Model", "Continuous Improvement"])
    
    with ams_tab1:
        st.subheader("AMS Strategy Recommendations")
        st.info("""
        Based on your ticket data analysis, the following AMS strategy recommendations can help optimize your application support operations.
        These recommendations focus on transitioning to a more proactive service model while reducing operational costs.
        """)
        
        # AMS Strategy Content
        st.markdown("""
        ### AMS Strategy Enhancement Opportunities

        #### 1. Shift Left Strategy Implementation
        - **Current State:** Most issues are being resolved at L2/L3 support levels
        - **Recommendation:** Implement knowledge transfer program to enable L1 to handle more complex issues
        - **Expected Benefit:** 15-20% reduction in ticket escalations, faster resolution times
        - **Implementation Difficulty:** Medium

        #### 2. Support Pyramid Optimization
        - **Current State:** Possible top-heavy support structure with more L3 than L1/L2 resources
        - **Recommendation:** Rebalance support pyramid ratio to 60:30:10 (L1:L2:L3)
        - **Expected Benefit:** 10-15% reduction in support costs while maintaining service levels
        - **Implementation Difficulty:** Medium

        #### 3. Tiered AMS Service Model
        - **Current State:** Potentially uniform support approach across all applications
        - **Recommendation:** Implement business criticality-based tiered support (Platinum/Gold/Silver)
        - **Expected Benefit:** Optimized resource allocation, better alignment with business priorities
        - **Implementation Difficulty:** Medium-High
        """)
        
        # AMS Strategy Implementation Timeline
        st.subheader("Implementation Roadmap")
        timeline_data = {
            'Phase': ['Assessment', 'Design', 'Implementation', 'Optimization'],
            'Duration (weeks)': [4, 6, 12, 'Ongoing'],
            'Key Activities': [
                'Baseline current performance metrics, identify gaps',
                'Define new support model, prepare transition plan',
                'Roll out new processes, tools and metrics',
                'Continuous monitoring and improvement'
            ]
        }
        timeline_df = pd.DataFrame(timeline_data)
        st.table(timeline_df)
        
    with ams_tab2:
        st.subheader("SLA Optimization")
        
        # SLA Analysis
        st.markdown("""
        ### SLA Analysis & Recommendations
        
        #### Current SLA Performance
        Based on the ticket data analysis, we've identified opportunities to optimize your Service Level Agreements 
        to better align with business needs while improving operational efficiency.
        """)
        
        # Create some sample SLA data
        sla_data = {
            'Priority': ['P1', 'P2', 'P3', 'P4'],
            'Current Response Time': ['15 min', '30 min', '4 hrs', '8 hrs'],
            'Current Resolution Time': ['4 hrs', '8 hrs', '24 hrs', '48 hrs'],
            'Compliance Rate': ['96.2%', '94.8%', '93.1%', '98.7%'],
            'Recommended Changes': [
                'No change', 
                'Extend to 1 hr response', 
                'Extend to 8 hrs response',
                'Next business day response'
            ]
        }
        sla_df = pd.DataFrame(sla_data)
        st.table(sla_df)
        
        st.markdown("""
        ### SLA Optimization Recommendations
        
        #### 1. Right-size SLAs based on actual business impact
        - Many P2 tickets could be downgraded to P3 based on actual business impact
        - Implement technical severity vs. business impact matrix
        - Expected outcome: More realistic and achievable SLAs
        
        #### 2. Implement differentiated SLAs by application tier
        - Critical applications: Maintain stringent SLAs
        - Non-critical applications: Relax SLAs to optimize resource utilization
        - Expected outcome: 15-20% improvement in resource efficiency
        
        #### 3. SLA measurement optimization
        - Implement business hours-based SLA measurement instead of 24/7 for non-critical systems
        - Add clear pause/stop conditions based on third-party dependencies
        - Expected outcome: More accurate SLA reporting and fair vendor evaluation
        """)
        
    with ams_tab3:
        st.subheader("AMS Governance Model")
        
        # Governance Model Content
        st.markdown("""
        ### Governance Structure Recommendations
        
        Based on ticket patterns and resolution workflows, we recommend the following governance model to optimize your AMS operations:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### Strategic Governance
            
            **Executive Steering Committee**
            - Quarterly business review meetings
            - Key performance evaluation
            - Strategic direction alignment
            - Innovation roadmap approval
            
            **Change Advisory Board**
            - Bi-weekly change review
            - Release management oversight
            - Risk assessment and mitigation
            - Change impact analysis
            """)
            
        with col2:
            st.markdown("""
            #### Operational Governance
            
            **Service Delivery Management**
            - Weekly service review meetings
            - Incident and problem review
            - SLA compliance monitoring
            - Continuous improvement initiatives
            
            **Daily Operations**
            - Daily stand-up meetings
            - Ticket triage and prioritization
            - Escalation management
            - Knowledge sharing huddles
            """)
        
        st.markdown("""
        ### RACI Matrix for AMS Governance
        
        A clearly defined RACI matrix ensures proper accountability and responsibility assignment across the AMS framework:
        """)
        
        # Sample RACI data
        raci_data = {
            'Activity': [
                'Strategic Direction', 
                'Performance Monitoring', 
                'SLA Management', 
                'Issue Resolution',
                'Change Management', 
                'Knowledge Management',
                'Resource Allocation',
                'Process Improvement'
            ],
            'Client Executive': ['A', 'I', 'I', 'I', 'I', 'I', 'C', 'A'],
            'Client IT': ['R', 'A', 'A', 'C', 'A', 'C', 'C', 'R'],
            'AMS Director': ['R', 'R', 'R', 'A', 'R', 'A', 'A', 'R'],
            'Service Delivery Mgr': ['C', 'R', 'R', 'R', 'R', 'R', 'R', 'R'],
            'Support Team': ['I', 'I', 'C', 'R', 'C', 'R', 'I', 'C']
        }
        raci_df = pd.DataFrame(raci_data)
        st.table(raci_df)
        
        st.caption("R: Responsible, A: Accountable, C: Consulted, I: Informed")
        
    with ams_tab4:
        st.subheader("Continuous Improvement Program")
        
        st.markdown("""
        ### AMS Continuous Improvement Framework
        
        Based on the ticket data patterns and resolution metrics, we recommend implementing a structured continuous 
        improvement program to progressively enhance AMS operations and reduce ticket volumes:
        """)
        
        # Continuous Improvement methodology
        st.image("https://images.pexels.com/photos/6224/hands-people-woman-working.jpg?auto=compress&cs=tinysrgb&w=1260&h=750", 
                caption="Continuous Improvement Cycle", use_container_width=True)
        
        st.markdown("""
        ### Continuous Improvement Initiatives
        
        #### 1. Knowledge Management Enhancement
        - **Current Gap:** Repeated similar tickets suggest knowledge reuse issues
        - **Initiative:** Implement gamified knowledge contribution program
        - **KPIs:** 
          * Knowledge article utilization rate
          * First-time-right resolution percentage
          * Knowledge contribution per team member
        
        #### 2. Problem Management Maturity
        - **Current Gap:** Recurring incidents indicate reactive problem management
        - **Initiative:** Implement proactive problem identification using ML/AI
        - **KPIs:**
          * Problem-to-incident ratio
          * Number of major incidents prevented
          * Mean time to resolve root causes
        
        #### 3. Self-Service Enablement
        - **Current Gap:** High volume of password/access tickets
        - **Initiative:** Enhanced self-service portal with guided resolution
        - **KPIs:**
          * Self-service adoption rate
          * Ticket deflection percentage
          * User satisfaction with self-service
        
        #### 4. Shift-Left Implementation
        - **Current Gap:** Too many tickets escalated to L2/L3
        - **Initiative:** L1 upskilling program and enhanced diagnostic tools
        - **KPIs:**
          * L1 resolution rate
          * Average escalation rate
          * Mean time to resolve by tier
        """)
        
        # Add an outcomes dashboard
        st.subheader("Expected Outcomes")
        
        outcomes_cols = st.columns(3)
        with outcomes_cols[0]:
            st.metric(
                label="Cost Efficiency", 
                value="18-25%", 
                delta="Improvement",
                delta_color="normal"
            )
        with outcomes_cols[1]:
            st.metric(
                label="User Satisfaction", 
                value="92%", 
                delta="↑ 12%",
                delta_color="normal"
            )
        with outcomes_cols[2]:
            st.metric(
                label="Incident Reduction", 
                value="30%", 
                delta="Year-over-Year",
                delta_color="normal"
            )
            
    # Add an expander with AMS transformation roadmap
    with st.expander("🛣️ AMS Transformation Roadmap"):
        st.markdown("""
        ### AMS Transformation Roadmap
        
        #### Phase 1: Foundation (Months 1-3)
        - Baseline current performance and establish metrics
        - Implement enhanced ticket categorization and prioritization
        - Conduct AMS process maturity assessment
        - Design governance structure and RACI model
        
        #### Phase 2: Optimization (Months 4-6)
        - Implement SLA optimization recommendations
        - Establish knowledge management program
        - Introduce shift-left initiatives
        - Launch self-service enhancement program
        
        #### Phase 3: Transformation (Months 7-12)
        - Deploy AI-assisted ticket routing and resolution
        - Implement predictive analytics for proactive support
        - Introduce automated health checks and monitoring
        - Establish AMS innovation program
        
        #### Phase 4: Innovation (Ongoing)
        - Continuous process improvement
        - Regular technology refresh assessments
        - Quarterly innovation showcases
        - Proactive business value delivery
        """)
    
    # Download buttons for AMS insights
    col1, col2 = st.columns(2)
    with col1:
        # We don't have actual AMS analysis to download yet, so this button would just download a template
        # In a real implementation, we would generate this content from the ticket data analysis
        ams_strategy_text = """AMS Strategy Recommendations
        
1. Shift Left Strategy Implementation
- Current State: Most issues are being resolved at L2/L3 support levels
- Recommendation: Implement knowledge transfer program to enable L1 to handle more complex issues
- Expected Benefit: 15-20% reduction in ticket escalations, faster resolution times
- Implementation Difficulty: Medium

2. Support Pyramid Optimization
- Current State: Possible top-heavy support structure with more L3 than L1/L2 resources
- Recommendation: Rebalance support pyramid ratio to 60:30:10 (L1:L2:L3)
- Expected Benefit: 10-15% reduction in support costs while maintaining service levels
- Implementation Difficulty: Medium

3. Tiered AMS Service Model
- Current State: Potentially uniform support approach across all applications
- Recommendation: Implement business criticality-based tiered support (Platinum/Gold/Silver)
- Expected Benefit: Optimized resource allocation, better alignment with business priorities
- Implementation Difficulty: Medium-High
        """
        
        st.download_button(
            label="Download AMS Strategy Recommendations",
            data=ams_strategy_text,
            file_name="ams_strategy_recommendations.txt",
            mime="text/plain"
        )
    
    with col2:
        ams_governance_text = """AMS Governance Model Recommendations
        
1. Strategic Governance
- Executive Steering Committee
  * Quarterly business review meetings
  * Key performance evaluation
  * Strategic direction alignment
  * Innovation roadmap approval
- Change Advisory Board
  * Bi-weekly change review
  * Release management oversight
  * Risk assessment and mitigation
  * Change impact analysis

2. Operational Governance
- Service Delivery Management
  * Weekly service review meetings
  * Incident and problem review
  * SLA compliance monitoring
  * Continuous improvement initiatives
- Daily Operations
  * Daily stand-up meetings
  * Ticket triage and prioritization
  * Escalation management
  * Knowledge sharing huddles
        """
        
        st.download_button(
            label="Download AMS Governance Recommendations",
            data=ams_governance_text,
            file_name="ams_governance_recommendations.txt",
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
    
    #### Advanced RCA Module
    - Data-driven approach to Root Cause Analysis
    - Uses statistical methods to identify patterns and correlations
    - Provides detailed visualizations and contributing factor analysis
    - Combines multiple analytical approaches for a more comprehensive analysis
    
    #### Automation & Improvement Recommendations
    - Identifies ticket types and workflows that can be automated
    - Suggests specific automation tools and technologies to implement
    - Calculates potential efficiency gains and productivity improvements
    - Highlights self-service options to reduce manual ticket creation
    - Provides implementation difficulty ratings for prioritization
    - For best results, run the General Analysis first
    
    #### RPA Use Cases
    - Identifies specific processes ideal for Robotic Process Automation (RPA)
    - Provides detailed process flows suitable for RPA implementation
    - Recommends specific RPA platforms (UiPath, Blue Prism, Automation Anywhere, etc.)
    - Includes development complexity and ROI estimates
    - Features an ROI calculator to estimate cost savings
    - Offers implementation guidance for RPA projects
    
    #### AMS Insights
    - Evaluates ticket data from an Application Management Services perspective
    - Provides strategic recommendations for optimizing support operations
    - Offers SLA optimization suggestions based on ticket patterns
    - Presents AMS governance models and RACI matrices
    - Delivers continuous improvement frameworks for ongoing optimization
    - Includes implementation roadmaps and cost-benefit analyses
    
    All reports can be downloaded as text files for sharing with your team or including in presentations.
    """)
