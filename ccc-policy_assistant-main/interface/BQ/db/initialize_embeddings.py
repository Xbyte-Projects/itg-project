import os
import logging
from dotenv import load_dotenv
from vertexai import rag

# Load environment variables and configure logging
load_dotenv()
logger = logging.getLogger(__name__)

def initialize_embeddings_with_vertex_ai():
    """Initialize embeddings for all GCS schemas using Vertex AI RAG and save them in a managed corpus."""
    try:
        # Read configuration from environment or hardcode
        project_id = os.getenv("BQ_PROJECT_ID")
        gcs_bucket = os.getenv("GOOGLE_BUCKET")
        gcs_path = os.getenv("GOOGLE_SCHEMA_PATH")
        corpus_display_name = os.getenv("CORPUS_DISPLAY_NAME")

        logger.info(f"Initializing embedding process for GCS path: gs://{gcs_bucket}/{gcs_path}")

        # Define embedding model
        embedding_model_config = rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model="publishers/google/models/text-embedding-005"
            )
        )

        # Create or get corpus
        rag_corpus = rag.create_corpus(
            display_name=corpus_display_name,
            backend_config=rag.RagVectorDbConfig(
                rag_embedding_model_config=embedding_model_config
            )
        )
        logger.info(f"Created RAG Corpus: {rag_corpus.name}")

        # Define GCS path to import files
        gcs_full_path = f"gs://{gcs_bucket}/{gcs_path}"

        # Import files with chunking and transformation config
        rag.import_files(
            rag_corpus.name,
            paths=[gcs_full_path],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(
                    chunk_size=512,
                    chunk_overlap=100
                )
            ),
            max_embedding_requests_per_min=600
        )
        logger.info("Import and embedding of schema files completed successfully.")

        print(f"Embeddings initialized and stored in RAG corpus: {corpus_display_name}")

    except Exception as e:
        logger.error(f"Embedding initialization failed: {str(e)}")
        print(f"Embedding initialization failed: {str(e)}")

if __name__ == "__main__":
    initialize_embeddings_with_vertex_ai()
