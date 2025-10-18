"""
Neo4j database client for managing connections and queries
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional, Any
import sys

sys.path.append('../..')
from config.config import config


class Neo4jClient:
    """Client for Neo4j database operations"""

    def __init__(self):
        """Initialize Neo4j driver"""
        try:
            self.driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
            )
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()

    def verify_connection(self):
        """Verify database connectivity"""
        try:
            self.driver.verify_connectivity()
            print("✓ Connected to Neo4j")
            return True
        except Exception as e:
            print(f"✗ Neo4j connection failed: {e}")
            return False

    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                print(f"Query execution error: {e}")
                print(f"Query: {query}")
                print(f"Parameters: {parameters}")
                raise

    def run_write_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a write query in a transaction

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results
        """

        def execute_query(tx, query, params):
            result = tx.run(query, params)
            return [record.data() for record in result]

        with self.driver.session() as session:
            try:
                return session.execute_write(execute_query, query, parameters or {})
            except Exception as e:
                print(f"Write query error: {e}")
                raise

    def create_indexes(self):
        """Create necessary indexes for performance"""
        print("Creating indexes...")

        indexes = [
            "CREATE INDEX subject_name IF NOT EXISTS FOR (s:Subject) ON (s.name)",
            "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
            "CREATE INDEX topic_subject IF NOT EXISTS FOR (t:Topic) ON (t.subject)",
            "CREATE INDEX question_year IF NOT EXISTS FOR (q:Question) ON (q.year)",
            "CREATE INDEX question_difficulty IF NOT EXISTS FOR (q:Question) ON (q.difficulty)",
            "CREATE INDEX chunk_source IF NOT EXISTS FOR (c:Chunk) ON (c.source_type)",
            "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        ]

        for index_query in indexes:
            try:
                self.run_query(index_query)
            except Exception as e:
                print(f"Index creation warning: {e}")

        print("✓ Indexes created")

    def create_vector_index(self, index_name: str = "chunk_embeddings",
                            dimension: int = 384):
        """
        Create vector index for similarity search

        Args:
            index_name: Name of the vector index
            dimension: Embedding dimension
        """
        query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (c:Chunk)
        ON c.embedding
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimension},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """

        try:
            self.run_query(query)
            print(f"✓ Vector index '{index_name}' created (dimension: {dimension})")
        except Exception as e:
            print(f"Vector index creation warning: {e}")

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        print("⚠️  WARNING: Clearing entire database...")
        self.run_query("MATCH (n) DETACH DELETE n")
        print("✓ Database cleared")

    def get_node_count(self, label: str) -> int:
        """Get count of nodes with specific label"""
        query = f"MATCH (n:{label}) RETURN count(n) as count"
        result = self.run_query(query)
        return result[0]['count'] if result else 0

    def get_all_labels(self) -> List[str]:
        """Get all node labels in database"""
        query = "CALL db.labels()"
        result = self.run_query(query)
        return [r['label'] for r in result]


# Example usage
if __name__ == "__main__":
    client = Neo4jClient()

    if client.verify_connection():
        # Get statistics
        labels = client.get_all_labels()
        print(f"\nNode labels in database: {labels}")

        for label in labels:
            count = client.get_node_count(label)
            print(f"{label}: {count} nodes")

    client.close()
