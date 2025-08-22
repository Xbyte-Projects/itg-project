# db/agent.py
import logging
from google.adk.agents import Agent
from . import prompt
# Import bq_connector from the correct path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from bq_connector import generate_sql, execute_sql
from .table_router_agent import table_router_agent
from .table_factory import table_factory

def dynamic_get_data(table_name: str, user_question: str) -> dict:
    """Dynamically generate and execute SQL for the specified table."""
    try:
        # Get the schema for the table
        table_schema = table_factory.get_schema(table_name)
        # Generate the specific prompt for this table
        table_prompt = prompt.generate_table_prompt(table_name, table_schema)
        # Create the query prompt with SQL generation rules
        query_prompt = (
            f"{table_prompt}\n"
            "Important: When generating SQL:\n"
            "1. Use SAFE_CAST for type conversions.\n"
            "2. Handle NULL values explicitly.\n"
            "3. Ensure all COALESCE arguments are the same type.\n"
            f"Question: {user_question}"
        )
        # Generate SQL using bq_connector
        clean_sql = generate_sql(query_prompt)
        logging.info(f"Generated SQL for {table_name}: {clean_sql}")
        # Execute SQL and return results
        result = execute_sql(clean_sql, table_name)
        if not result or (isinstance(result, dict) and result.get("status") == "error"):
            return {"error": "No results found or error occurred"}
        return result
    except Exception as e:
        logging.error(f"Error in dynamic_get_data for {table_name}: {str(e)}")
        return {"error": str(e), "status": "error"}

# Create root_agent with dynamic query handling
# RENAMED FROM db_root_agent TO root_agent
root_agent = Agent(
    model=prompt.MODEL_NAME,
    name="db_root_agent", # You can keep this internal name, or change to "root_agent" if you prefer
    description="Root agent for IPEDS database queries",
    instruction=prompt.DB_ROOT_AGENT_PROMPT,
    sub_agents=[table_router_agent],
    tools=[dynamic_get_data]
)