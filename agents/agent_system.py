import os
import autogen
from groq import Groq
import json
import pandas as pd
import streamlit as st
from .prompt_templates import (
    SYSTEM_PROMPT, 
    DATA_ANALYSIS_PROMPT, 
    RCA_PROMPT,
    RECOMMENDATION_PROMPT
)

class GroqLLMConfig:
    """Configuration for Groq LLM"""
    
    def __init__(self, api_key, model="llama3-8b-8192"):
        """
        Initialize the Groq LLM configuration
        
        Args:
            api_key: Groq API key
            model: Model to use, default is llama3-8b-8192
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
    
    def get_completion(self, prompt, system_prompt=None):
        """
        Get completion from Groq
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt
            
        Returns:
            The model's response as string
        """
        if not self.client:
            raise ValueError("Groq client not initialized. Please provide a valid API key.")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
                top_p=1,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

class AgentSystem:
    """
    AutoGen agent system for ServiceNow ticket analysis
    """
    
    def __init__(self, groq_config):
        """
        Initialize the agent system
        
        Args:
            groq_config: GroqLLMConfig instance
        """
        self.groq_config = groq_config
        self.setup_agents()
    
    def setup_agents(self):
        """
        Set up the AutoGen agent system
        """
        # Configure LLM for AutoGen
        llm_config = {
            "config_list": [{"model": self.groq_config.model}],
            "temperature": 0.3,
            "cache_seed": None,
        }
        
        # Create the user proxy agent
        self.user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
            code_execution_config={"use_docker": False},
        )
        
        # Create the ticket analyzer agent
        self.ticket_analyzer = autogen.AssistantAgent(
            name="TicketAnalyzer",
            llm_config=llm_config,
            system_message=SYSTEM_PROMPT
        )
        
        # Create the RCA specialist agent
        self.rca_specialist = autogen.AssistantAgent(
            name="RCASpecialist",
            llm_config=llm_config,
            system_message="""You are an expert in Root Cause Analysis for IT incidents. 
            Your role is to analyze ServiceNow ticket data and identify underlying causes of issues.
            Focus on patterns, dependencies, and technical factors that might contribute to problems."""
        )
        
        # Create the recommendation agent
        self.recommendation_agent = autogen.AssistantAgent(
            name="RecommendationAgent",
            llm_config=llm_config,
            system_message="""You are an expert in IT service management and resolution strategies.
            Your role is to provide actionable recommendations based on ticket data analysis.
            Focus on practical solutions, best practices, and preventive measures."""
        )
    
    def direct_query(self, query, ticket_data):
        """
        Send a direct query to the Groq LLM without using agents
        
        Args:
            query: User query about the ticket data
            ticket_data: Dictionary with processed ticket data
            
        Returns:
            LLM response
        """
        # Format the data context
        data_context = f"""
        Here's the ServiceNow ticket data summary:
        - Total tickets: {ticket_data.get('total_tickets', 'N/A')}
        - Available columns: {', '.join(ticket_data.get('columns', []))}
        
        Time metrics:
        {json.dumps(ticket_data.get('time_metrics', {}), indent=2)}
        
        Category metrics:
        {json.dumps(ticket_data.get('category_metrics', {}), indent=2)}
        
        Common keywords in tickets:
        {json.dumps(ticket_data.get('common_keywords', {}), indent=2)}
        """
        
        # Combine data context with user query
        full_prompt = f"""
        {data_context}
        
        User query: {query}
        
        Please provide a helpful, accurate, and concise answer based on the ticket data.
        """
        
        # Get completion from Groq
        system_prompt = "You are a ServiceNow ticket analysis assistant. Help the user understand their ticket data and answer their questions."
        response = self.groq_config.get_completion(full_prompt, system_prompt)
        
        return response
    
    def analyze_data(self, ticket_data):
        """
        Analyze ticket data using the LLM
        
        Args:
            ticket_data: Dictionary with processed ticket data
            
        Returns:
            Analysis results as string
        """
        # Format the data for analysis
        data_str = json.dumps(ticket_data, indent=2)
        
        # Create the prompt for analysis
        analysis_prompt = DATA_ANALYSIS_PROMPT.format(data=data_str)
        
        # Get completion from Groq
        response = self.groq_config.get_completion(analysis_prompt, SYSTEM_PROMPT)
        
        return response
    
    def generate_rca(self, ticket_data, incident_description):
        """
        Generate Root Cause Analysis for an incident
        
        Args:
            ticket_data: Dictionary with processed ticket data
            incident_description: Description of the incident
            
        Returns:
            RCA report as string
        """
        # Format the data for RCA
        data_str = json.dumps(ticket_data, indent=2)
        
        # Create the prompt for RCA
        rca_prompt = RCA_PROMPT.format(
            data=data_str,
            incident_description=incident_description
        )
        
        # Get completion from Groq
        response = self.groq_config.get_completion(rca_prompt)
        
        return response
    
    def generate_recommendations(self, ticket_data, analysis_results):
        """
        Generate recommendations based on ticket data and analysis
        
        Args:
            ticket_data: Dictionary with processed ticket data
            analysis_results: Results from previous analysis
            
        Returns:
            Recommendations as string
        """
        # Format the data for recommendations
        data_str = json.dumps(ticket_data, indent=2)
        
        # Create the prompt for recommendations
        recommendation_prompt = RECOMMENDATION_PROMPT.format(
            data=data_str,
            analysis_results=analysis_results
        )
        
        # Get completion from Groq
        response = self.groq_config.get_completion(recommendation_prompt)
        
        return response
    
    def multi_agent_chat(self, query, ticket_data):
        """
        Run a multi-agent chat to answer a complex query
        
        Args:
            query: User query
            ticket_data: Dictionary with processed ticket data
            
        Returns:
            Chat transcript
        """
        # Format the data context
        data_str = json.dumps(ticket_data, indent=2)
        
        # Initiate the chat
        self.user_proxy.initiate_chat(
            self.ticket_analyzer,
            message=f"""
            Here is the ServiceNow ticket data:
            {data_str}
            
            User query: {query}
            
            Please analyze this data and provide a helpful response.
            Once you're done, include "TERMINATE" at the end of your message.
            """
        )
        
        # Extract the responses from the chat history
        responses = []
        for message in self.user_proxy.chat_history[self.ticket_analyzer]:
            if message["role"] == "assistant":
                responses.append(message["content"])
        
        # Join the responses and remove the termination marker
        full_response = "\n\n".join(responses)
        full_response = full_response.replace("TERMINATE", "").strip()
        
        return full_response
