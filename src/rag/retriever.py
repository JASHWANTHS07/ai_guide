"""
Hybrid retriever combining vector similarity and graph traversal
"""

from typing import List, Dict, Optional
import sys

sys.path.append('../..')

from src.graph.neo4j_client import Neo4jClient
from src.ingestion.embeddings_generator import EmbeddingsGenerator


class HybridRetriever:
    """Hybrid retriever combining vector similarity and graph traversal"""

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize retriever

        Args:
            neo4j_client: Neo4j client instance
        """
        self.client = neo4j_client
        self.embedder = EmbeddingsGenerator()

    # ============= Vector Similarity Search =============

    def vector_search(self, query: str, top_k: int = 5,
                      subject: str = None, topic: str = None) -> List[Dict]:
        """
        Perform vector similarity search on chunks

        Args:
            query: Search query
            top_k: Number of results to return
            subject: Optional subject filter
            topic: Optional topic filter

        Returns:
            List of relevant chunks with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)

        # Build Cypher query
        cypher = """
        CALL db.index.vector.queryNodes(
            'chunk_embeddings', 
            $top_k, 
            $query_embedding
        ) YIELD node AS chunk, score
        """

        # Add filters if provided
        if subject or topic:
            cypher += "\nMATCH (chunk)<-[:EXPLAINED_BY]-(t:Topic)"

            filters = []
            if subject:
                filters.append("t.subject = $subject")
            if topic:
                filters.append("t.name = $topic")

            if filters:
                cypher += "\nWHERE " + " AND ".join(filters)

        cypher += """
        RETURN chunk.text AS text,
               chunk.source_file AS source,
               chunk.page_number AS page,
               score
        ORDER BY score DESC
        LIMIT $top_k
        """

        try:
            results = self.client.run_query(cypher, {
                'query_embedding': query_embedding,
                'top_k': top_k,
                'subject': subject,
                'topic': topic
            })
            return results
        except Exception as e:
            print(f"Vector search error: {e}")
            return []

    # ============= Graph Traversal Search =============

    def graph_search(self, subject: str, topic: str,
                     include_concepts: bool = True) -> Dict:
        """
        Retrieve information using graph traversal

        Args:
            subject: Subject name
            topic: Topic name
            include_concepts: Include related concepts

        Returns:
            Dictionary with topic information
        """
        cypher = """
        MATCH (s:Subject {name: $subject})-[:HAS_TOPIC]->(t:Topic {name: $topic})
        OPTIONAL MATCH (t)-[:EXPLAINED_BY]->(chunk:Chunk)
        OPTIONAL MATCH (t)-[:HAS_QUESTION]->(q:Question)
        """

        if include_concepts:
            cypher += "\nOPTIONAL MATCH (t)-[:HAS_CONCEPT]->(c:Concept)"

        cypher += """
        RETURN t.name AS topic,
               t.description AS description,
               t.difficulty_level AS difficulty,
               collect(DISTINCT chunk.text)[0..5] AS sample_chunks,
               count(DISTINCT q) AS question_count
        """

        if include_concepts:
            cypher += ", collect(DISTINCT c.name) AS concepts"

        try:
            results = self.client.run_query(cypher, {
                'subject': subject,
                'topic': topic
            })
            return results[0] if results else {}
        except Exception as e:
            print(f"Graph search error: {e}")
            return {}

    # ============= Hybrid Search =============

    def hybrid_search(self, query: str, subject: str, topic: str,
                      top_k: int = 5) -> Dict:
        """
        Combine vector search and graph traversal

        Args:
            query: Search query
            subject: Subject name
            topic: Topic name
            top_k: Number of vector results

        Returns:
            Combined results
        """
        # Get vector search results
        vector_results = self.vector_search(query, top_k, subject, topic)

        # Get graph traversal results
        graph_results = self.graph_search(subject, topic)

        # Combine results
        combined = {
            'topic_info': graph_results,
            'relevant_chunks': vector_results,
            'search_query': query
        }

        return combined

    # ============= Question Retrieval =============

    def get_questions_by_topic(self, subject: str, topic: str,
                               year: int = None,
                               difficulty: int = None,
                               limit: int = 10) -> List[Dict]:
        """
        Retrieve questions for a specific topic

        Args:
            subject: Subject name
            topic: Topic name
            year: Optional year filter
            difficulty: Optional difficulty filter
            limit: Maximum number of questions

        Returns:
            List of questions
        """
        cypher = """
        MATCH (t:Topic {name: $topic, subject: $subject})-[:HAS_QUESTION]->(q:Question)
        """

        where_clauses = []
        params = {
            'subject': subject,
            'topic': topic,
            'limit': limit
        }

        if year:
            where_clauses.append("q.year = $year")
            params['year'] = year

        if difficulty is not None:
            where_clauses.append("q.difficulty = $difficulty")
            params['difficulty'] = difficulty

        if where_clauses:
            cypher += "\nWHERE " + " AND ".join(where_clauses)

        cypher += """
        RETURN q.text AS question,
               q.options AS options,
               q.answer AS answer,
               q.year AS year,
               q.difficulty AS difficulty,
               q.marks AS marks,
               q.paper_set AS paper_set
        ORDER BY q.year DESC, q.difficulty ASC
        LIMIT $limit
        """

        try:
            results = self.client.run_query(cypher, params)
            return results
        except Exception as e:
            print(f"Question retrieval error: {e}")
            return []

    def get_questions_ordered_by_difficulty(self, subject: str, topic: str,
                                            ascending: bool = True) -> List[Dict]:
        """
        Get questions ordered by difficulty for Learn mode

        Args:
            subject: Subject name
            topic: Topic name
            ascending: If True, easy to hard; if False, hard to easy

        Returns:
            Ordered list of questions
        """
        order = "ASC" if ascending else "DESC"

        cypher = f"""
        MATCH (t:Topic {{name: $topic, subject: $subject}})-[:HAS_QUESTION]->(q:Question)
        RETURN q.text AS question,
               q.options AS options,
               q.answer AS answer,
               q.difficulty AS difficulty,
               q.year AS year,
               q.marks AS marks
        ORDER BY q.difficulty {order}, q.year DESC
        """

        try:
            results = self.client.run_query(cypher, {
                'subject': subject,
                'topic': topic
            })
            return results
        except Exception as e:
            print(f"Question ordering error: {e}")
            return []

    def get_all_subjects(self) -> List[str]:
        """Get list of all subjects"""
        query = "MATCH (s:Subject) RETURN s.name AS name ORDER BY name"
        results = self.client.run_query(query)
        return [r['name'] for r in results]

    def get_topics_for_subject(self, subject: str) -> List[Dict]:
        """Get list of topics for a subject with metadata"""
        query = """
        MATCH (s:Subject {name: $subject})-[:HAS_TOPIC]->(t:Topic)
        OPTIONAL MATCH (t)-[:HAS_QUESTION]->(q:Question)
        RETURN t.name AS name,
               t.description AS description,
               t.difficulty_level AS difficulty,
               count(DISTINCT q) AS question_count
        ORDER BY t.name
        """
        results = self.client.run_query(query, {'subject': subject})
        return results


# Example usage
if __name__ == "__main__":
    from src.graph.neo4j_client import Neo4jClient

    client = Neo4jClient()
    retriever = HybridRetriever(client)

    # Test getting subjects
    subjects = retriever.get_all_subjects()
    print(f"Subjects: {subjects}")

    if subjects:
        # Test getting topics
        topics = retriever.get_topics_for_subject(subjects[0])
        print(f"\nTopics in {subjects[0]}:")
        for topic in topics:
            print(f"  - {topic['name']} (Questions: {topic['question_count']})")

    client.close()
