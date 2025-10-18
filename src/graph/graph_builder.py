"""
Graph builder for constructing knowledge graph in Neo4j
"""

from typing import List, Dict, Optional
from tqdm import tqdm
import sys

sys.path.append('../..')

from src.graph.neo4j_client import Neo4jClient
from src.ingestion.embeddings_generator import EmbeddingsGenerator


class GraphBuilder:
    """Build knowledge graph from processed data"""

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize graph builder

        Args:
            neo4j_client: Neo4j client instance
        """
        self.client = neo4j_client
        self.embedder = EmbeddingsGenerator()

    # ============= Subject and Topic Management =============

    def create_subject(self, name: str, description: str = "") -> Dict:
        """Create a Subject node"""
        query = """
        MERGE (s:Subject {name: $name})
        SET s.description = $description,
            s.updated_at = datetime()
        RETURN s
        """
        result = self.client.run_query(query, {
            'name': name,
            'description': description
        })
        return result[0] if result else None

    def create_topic(self, subject_name: str, topic_name: str,
                     description: str = "", difficulty: int = 1) -> Dict:
        """
        Create a Topic node and link to Subject

        Args:
            subject_name: Parent subject name
            topic_name: Topic name
            description: Topic description
            difficulty: Difficulty level (1-5)
        """
        query = """
        MATCH (s:Subject {name: $subject_name})
        MERGE (t:Topic {name: $topic_name, subject: $subject_name})
        SET t.description = $description,
            t.difficulty_level = $difficulty,
            t.updated_at = datetime()
        MERGE (s)-[:HAS_TOPIC]->(t)
        RETURN t
        """
        result = self.client.run_query(query, {
            'subject_name': subject_name,
            'topic_name': topic_name,
            'description': description,
            'difficulty': difficulty
        })
        return result[0] if result else None

    def load_syllabus(self, syllabus_data: Dict):
        """
        Load complete syllabus into graph

        Args:
            syllabus_data: Dictionary with structure:
                {
                    'subject_name': {
                        'description': '...',
                        'topics': [
                            {'name': '...', 'description': '...', 'difficulty': 1},
                            ...
                        ]
                    }
                }
        """
        print("\n📚 Loading syllabus into graph...")

        for subject_name, subject_info in tqdm(syllabus_data.items(), desc="Loading subjects"):
            # Create subject
            self.create_subject(
                name=subject_name,
                description=subject_info.get('description', '')
            )

            # Create topics
            for topic in subject_info.get('topics', []):
                self.create_topic(
                    subject_name=subject_name,
                    topic_name=topic['name'],
                    description=topic.get('description', ''),
                    difficulty=topic.get('difficulty', 1)
                )

        stats = self.get_graph_statistics()
        print(f"✅ Syllabus loaded: {stats['subjects']} subjects, {stats['topics']} topics")

    # ============= Question Management =============

    def create_question(self, question_data: Dict) -> Dict:
        """
        Create a Question node

        Args:
            question_data: Dictionary with keys:
                - question_text: Question text
                - year: Exam year
                - paper_set: Paper set identifier
                - subject: Subject name
                - topic: Topic name
                - options: List of options (optional)
                - answer: Correct answer (optional)
                - difficulty: Difficulty level (optional)
                - marks: Question marks (optional)
        """
        # First, ensure topic exists
        topic_query = """
        MATCH (t:Topic {name: $topic, subject: $subject})
        RETURN t
        """
        topic_result = self.client.run_query(topic_query, {
            'subject': question_data['subject'],
            'topic': question_data['topic']
        })

        if not topic_result:
            print(f"⚠️  Topic not found: {question_data['topic']} in {question_data['subject']}")
            return None

        # Generate embedding for question
        full_text = question_data['question_text']
        if question_data.get('options'):
            full_text += "\n" + "\n".join(question_data['options'])

        embedding = self.embedder.generate_embedding(full_text)

        # Create question with embedding
        query = """
        MATCH (t:Topic {name: $topic, subject: $subject})
        CREATE (q:Question {
            text: $text,
            year: $year,
            paper_set: $paper_set,
            options: $options,
            answer: $answer,
            difficulty: $difficulty,
            marks: $marks,
            embedding: $embedding,
            created_at: datetime()
        })
        MERGE (t)-[:HAS_QUESTION]->(q)
        RETURN q
        """

        result = self.client.run_query(query, {
            'subject': question_data['subject'],
            'topic': question_data['topic'],
            'text': question_data['question_text'],
            'year': question_data.get('year', 0),
            'paper_set': question_data.get('paper_set', 'unknown'),
            'options': question_data.get('options', []),
            'answer': question_data.get('answer', ''),
            'difficulty': question_data.get('difficulty', 0),
            'marks': question_data.get('marks', 1),
            'embedding': embedding
        })

        return result[0] if result else None

    def load_pyqs(self, pyqs_data: List[Dict]):
        """
        Load Previous Years Questions into graph

        Args:
            pyqs_data: List of question dictionaries
        """
        print("\n📝 Loading PYQs into graph...")

        success_count = 0
        failed_count = 0

        for question in tqdm(pyqs_data, desc="Loading questions"):
            try:
                result = self.create_question(question)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Error loading question: {e}")
                failed_count += 1

        print(f"✅ Loaded {success_count} questions ({failed_count} failed)")

    # ============= Textbook Chunks Management =============

    def create_chunk(self, chunk_data: Dict) -> Dict:
        """
        Create a Chunk node with embedding

        Args:
            chunk_data: Dictionary with keys:
                - text: Chunk text
                - subject: Subject name
                - topic: Topic name
                - source_file: Source filename
                - page_number: Page number (optional)
                - chunk_index: Chunk index in document
                - embedding: Pre-computed embedding (optional)
        """
        # Generate embedding if not provided
        if 'embedding' not in chunk_data or not chunk_data['embedding']:
            chunk_data['embedding'] = self.embedder.generate_embedding(
                chunk_data['text']
            )

        # Check if topic exists
        topic_query = """
        MATCH (t:Topic {name: $topic, subject: $subject})
        RETURN t
        """
        topic_result = self.client.run_query(topic_query, {
            'subject': chunk_data['subject'],
            'topic': chunk_data['topic']
        })

        if not topic_result:
            print(f"⚠️  Topic not found: {chunk_data['topic']} in {chunk_data['subject']}")
            return None

        query = """
        MATCH (t:Topic {name: $topic, subject: $subject})
        CREATE (c:Chunk {
            text: $text,
            source_file: $source_file,
            source_type: 'textbook',
            page_number: $page_number,
            chunk_index: $chunk_index,
            embedding: $embedding,
            created_at: datetime()
        })
        MERGE (t)-[:EXPLAINED_BY]->(c)
        RETURN c
        """

        result = self.client.run_query(query, {
            'subject': chunk_data['subject'],
            'topic': chunk_data['topic'],
            'text': chunk_data['text'],
            'source_file': chunk_data.get('source_file', 'unknown'),
            'page_number': chunk_data.get('page_number', 0),
            'chunk_index': chunk_data.get('chunk_index', 0),
            'embedding': chunk_data['embedding']
        })

        return result[0] if result else None

    def load_textbook_chunks(self, chunks_data: List[Dict], batch_size: int = 100):
        """
        Load textbook chunks into graph in batches

        Args:
            chunks_data: List of chunk dictionaries
            batch_size: Number of chunks to process at once
        """
        print(f"\n📖 Loading {len(chunks_data)} textbook chunks into graph...")

        success_count = 0
        failed_count = 0

        # Process in batches
        for i in tqdm(range(0, len(chunks_data), batch_size), desc="Loading chunks"):
            batch = chunks_data[i:i + batch_size]

            for chunk in batch:
                try:
                    result = self.create_chunk(chunk)
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    print(f"Error loading chunk: {e}")
                    failed_count += 1

        print(f"✅ Loaded {success_count} chunks ({failed_count} failed)")

    # ============= Concept Management =============

    def create_concept(self, name: str, explanation: str,
                       topic_name: str, subject_name: str) -> Dict:
        """Create a Concept node and link to Topic"""
        query = """
        MATCH (t:Topic {name: $topic, subject: $subject})
        MERGE (c:Concept {name: $name, topic: $topic, subject: $subject})
        SET c.explanation = $explanation,
            c.updated_at = datetime()
        MERGE (t)-[:HAS_CONCEPT]->(c)
        RETURN c
        """

        result = self.client.run_query(query, {
            'name': name,
            'explanation': explanation,
            'topic': topic_name,
            'subject': subject_name
        })

        return result[0] if result else None

    # ============= Statistics =============

    def get_graph_statistics(self) -> Dict:
        """Get statistics about the knowledge graph"""
        stats = {
            'subjects': self.client.get_node_count('Subject'),
            'topics': self.client.get_node_count('Topic'),
            'questions': self.client.get_node_count('Question'),
            'chunks': self.client.get_node_count('Chunk'),
            'concepts': self.client.get_node_count('Concept'),
        }

        return stats


# Example usage
if __name__ == "__main__":
    client = Neo4jClient()
    client.verify_connection()
    builder = GraphBuilder(client)

    # Get statistics
    stats = builder.get_graph_statistics()
    print("\nGraph Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    client.close()
