import streamlit as st

st.set_page_config(
    page_title="About | ServiceNow Ticket Analyzer",
    page_icon="ℹ️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("About ServiceNow Ticket Analyzer")

# Header image
st.image("https://pixabay.com/get/gada98cde0b5dc60952361a55014bab85d3388f5213c0d4efcbfc5cc316574dbbf11a47d6666423ae344b920867f89e5bdfd5a85738960cb85a91f3ad7dd444f1_1280.jpg", 
         caption="Intelligent IT Service Management", use_column_width=True)

# Application overview
st.header("Application Overview")
st.markdown("""
The ServiceNow Ticket Analyzer is an intelligent platform designed to help IT support teams gain deeper insights into 
their ServiceNow ticket data. By leveraging advanced AI technologies, this tool provides data-driven analysis and 
recommendations to improve service delivery and reduce ticket resolution times.

### Key Features

1. **Interactive Dashboard**
   - Visualize ticket trends and patterns
   - Filter by various criteria like date, category, and priority
   - View key metrics such as resolution times and ticket volumes

2. **AI-Powered Chatbot**
   - Ask natural language questions about your ticket data
   - Get instant insights and answers
   - Uses GROQ LLM and AutoGen framework for intelligent responses

3. **Advanced Analysis**
   - Comprehensive ticket data analysis
   - Root Cause Analysis (RCA) for specific incidents
   - Smart recommendations for improving service operations

4. **Data Processing**
   - Support for large ServiceNow ticket datasets
   - Automated data cleaning and standardization
   - Efficient processing pipeline for quick analysis
""")

# Technical details
st.header("Technical Details")
st.markdown("""
### Technology Stack

- **Streamlit**: Web application framework
- **AutoGen**: Multi-agent framework for complex reasoning
- **GROQ LLM**: Large Language Model for natural language processing
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive data visualizations
- **PyArrow**: Efficient large dataset handling

### How It Works

1. **Data Upload**: Upload your ServiceNow ticket data in CSV or Excel format
2. **Data Processing**: The system automatically cleans and standardizes your ticket data
3. **Visualization**: Interactive charts and graphs are generated to visualize patterns
4. **AI Analysis**: AutoGen agents analyze your data to extract insights
5. **Query Interface**: Natural language interface for asking questions about your data
6. **Report Generation**: Generate comprehensive analysis reports and recommendations
""")

# Usage instructions
st.header("How to Use")
st.markdown("""
### Getting Started

1. **Upload Data**: On the home page, upload your ServiceNow ticket export file (CSV or Excel)
2. **Explore Dashboard**: Navigate to the Dashboard page to view visualizations and metrics
3. **Ask Questions**: Use the Chatbot page to ask specific questions about your data
4. **Generate Reports**: On the Analysis page, generate comprehensive reports and recommendations

### Required Data Format

For best results, your ServiceNow ticket data should include these fields:
- Ticket number/ID
- Short description
- Description
- Status
- Priority
- Category
- Assigned to
- Created date/time
- Resolved date/time

Additional fields will enhance the analysis capabilities.
""")

# Tips and best practices
st.header("Tips & Best Practices")
st.markdown("""
### For Best Results

1. **Data Quality**: Ensure your data is as complete as possible with minimal missing values
2. **Historical Data**: Include at least 3-6 months of ticket data for trend analysis
3. **API Key**: Use a valid GROQ API key with sufficient usage quota
4. **Specific Questions**: When using the chatbot, ask specific questions for more precise answers
5. **RCA Details**: Provide detailed incident descriptions for more accurate Root Cause Analysis
6. **Regular Analysis**: Run analysis periodically to track improvements over time
""")

# Footer with contact/help
st.header("Contact & Support")
st.markdown("""
For questions, feedback, or support with the ServiceNow Ticket Analyzer platform:

- Refer to the documentation in the "Analysis Feature Guide" expandable section on the Analysis page
- Ensure your GROQ API key is valid and has sufficient usage quota
- Check that your data follows the recommended format for best results
""")

# Version information
st.sidebar.markdown("---")
st.sidebar.info("Version 1.0.0")
