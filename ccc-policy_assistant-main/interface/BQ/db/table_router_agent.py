import os
import logging
from dotenv import load_dotenv
from google.adk.agents import Agent
from . import prompt
from .table_factory import table_factory
from vertexai import rag
import vertexai

logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

class TableRouter:
    def __init__(self):
        """Initialize TableRouter with Vertex AI RAG."""
        try:
            # Initialize Vertex AI
            project_id = os.getenv("BQ_PROJECT_ID")
            vertexai.init(project=project_id, location="us-central1")
            logger.info("Initialized Vertex AI for RAG queries")
            self.rag_enabled = True
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            self.rag_enabled = False

    def query_embeddings(self, query_text, corpus_display_name="ccc-schema-updated", top_k=5):
        """Query the embeddings stored in the RAG corpus and return relevant results."""
        if not self.rag_enabled:
            logger.warning("Vertex AI RAG is not enabled, skipping RAG query")
            return []
        
        try:
            # Read project ID from environment
            project_id = os.getenv("BQ_PROJECT_ID")
            logger.info(f"Querying embeddings for project: {project_id}, corpus: {corpus_display_name}")

            # List all corpora to find the target corpus
            corpora = rag.list_corpora()
            target_corpus = None
            for corpus in corpora:
                if corpus.display_name == corpus_display_name:
                    target_corpus = corpus
                    break

            if not target_corpus:
                raise ValueError(f"Corpus with display name '{corpus_display_name}' not found.")

            logger.info(f"Found RAG Corpus: {target_corpus.name}")

            # Perform the query
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=target_corpus.name,
                    )
                ],
                text=query_text,
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=top_k,
                    filter=rag.utils.resources.Filter(vector_distance_threshold=0.5)
                )
            )

            # Process and display results
            results = []
            logger.info(f"Query: {query_text}")
            for context in response.contexts.contexts:
                file_name = context.source_uri.split('/')[-1]  # Extract file name from source_uri
                snippet = context.text
                results.append({"file_name": file_name, "snippet": snippet})
                logger.info(f"File: {file_name}, Snippet: {snippet[:100]}...")

            print(f"\nQuery Results for '{query_text}':")
            for i, result in enumerate(results, 1):
                print(f"{i}. File: {result['file_name']}")
                print(f"   Snippet: {result['snippet'][:200]}...")
                print("-" * 80)

            return results

        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            print(f"Query failed: {str(e)}")
            return []

    def find_relevant_tables(self, user_question: str, top_k=5) -> list:
        """Find the top_k most relevant tables using Vertex AI RAG embeddings."""
        logger.info(f"Searching for relevant tables for question: {user_question}")
        tables = []
        
        # Query Vertex AI RAG
        try:
            rag_results = self.query_embeddings(user_question, top_k=top_k)
            rag_tables = [
                {
                    "table_name": result["file_name"].replace(".json", ""),
                    "table_schema": table_factory.get_schema(result["file_name"].replace(".json", "")),
                    "source": "vertex_rag",
                    "snippet": result["snippet"]
                }
                for result in rag_results
                if table_factory.get_schema(result["file_name"].replace(".json", "")) 
            ]
            tables.extend(rag_tables)
            logger.info(f"Found {len(rag_tables)} relevant tables from Vertex AI RAG: {[t['table_name'] for t in rag_tables]}")
        except Exception as e:
            logger.error(f"Error querying Vertex AI RAG: {str(e)}")
        
        # Deduplicate tables by table_name, keeping the first occurrence
        seen = set()
        unique_tables = []
        for table in tables:
            if table["table_name"] not in seen:
                seen.add(table["table_name"])
                unique_tables.append(table)
        
        # Limit to top_k
        unique_tables = unique_tables[:top_k]
        
        logger.info(f"Returning {len(unique_tables)} unique relevant tables: {[t['table_name'] for t in unique_tables]}")
        return unique_tables

def route_to_table(user_question: str) -> dict:
    """Route a user question to relevant tables."""
    try:
        table_router = TableRouter()
        relevant_tables = table_router.find_relevant_tables(user_question)
        if not relevant_tables:
            logger.warning("No relevant tables found for the question")
            return {"error": "No relevant tables found for this question"}
        
        return {
            "tables": [
                {
                    "table_name": table["table_name"],
                    "table_schema": table["table_schema"],
                    "user_question": user_question,
                    "source": table.get("source", "vertex_rag"),
                    "snippet": table.get("snippet", "")
                }
                for table in relevant_tables
            ]
        }
    except Exception as e:
        logger.error(f"Error routing question: {str(e)}")
        return {"error": f"Failed to route question: {str(e)}"}

table_router_agent = Agent(
    model=prompt.MODEL_NAME,
    name="table_router_agent",
    description="Agent that routes questions to the appropriate IPEDS tables using precomputed embeddings in Vertex AI RAG",
    instruction=prompt.TABLE_ROUTER_PROMPT,
    tools=[route_to_table]
)