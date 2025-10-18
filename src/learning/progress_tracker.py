"""
Track user learning progress and performance
"""

from typing import Dict, List
from datetime import datetime
import sys

sys.path.append('../..')

from src.graph.neo4j_client import Neo4jClient


class ProgressTracker:
    """Track user progress and performance"""

    def __init__(self, neo4j_client: Neo4jClient):
        """
        Initialize progress tracker

        Args:
            neo4j_client: Neo4j client instance
        """
        self.client = neo4j_client
        self._ensure_progress_nodes()

    def _ensure_progress_nodes(self):
        """Ensure User and Progress nodes exist"""
        # Create default user if not exists
        query = """
        MERGE (u:User {id: 'default_user'})
        SET u.created_at = COALESCE(u.created_at, datetime())
        RETURN u
        """
        self.client.run_query(query)

    def record_attempt(self, subject: str, topic: str,
                       question_text: str, is_correct: bool):
        """
        Record a question attempt

        Args:
            subject: Subject name
            topic: Topic name
            question_text: Question text
            is_correct: Whether answer was correct
        """
        query = """
        MATCH (u:User {id: 'default_user'})
        MATCH (t:Topic {name: $topic, subject: $subject})
        MATCH (t)-[:HAS_QUESTION]->(q:Question {text: $question_text})

        MERGE (u)-[a:ATTEMPTED]->(q)
        ON CREATE SET 
            a.first_attempt = datetime(),
            a.attempt_count = 1,
            a.correct_count = CASE WHEN $is_correct THEN 1 ELSE 0 END,
            a.last_correct = CASE WHEN $is_correct THEN datetime() ELSE null END
        ON MATCH SET
            a.last_attempt = datetime(),
            a.attempt_count = a.attempt_count + 1,
            a.correct_count = a.correct_count + CASE WHEN $is_correct THEN 1 ELSE 0 END,
            a.last_correct = CASE WHEN $is_correct THEN datetime() ELSE a.last_correct END

        RETURN a
        """

        try:
            self.client.run_query(query, {
                'subject': subject,
                'topic': topic,
                'question_text': question_text,
                'is_correct': is_correct
            })
        except Exception as e:
            print(f"Error recording attempt: {e}")

    def get_user_stats(self, subject: str = None,
                       topic: str = None) -> Dict:
        """
        Get user statistics

        Args:
            subject: Optional subject filter
            topic: Optional topic filter

        Returns:
            Dictionary with statistics
        """
        if topic and subject:
            # Topic-specific stats
            query = """
            MATCH (u:User {id: 'default_user'})-[a:ATTEMPTED]->(q:Question)
            MATCH (q)<-[:HAS_QUESTION]-(t:Topic {name: $topic, subject: $subject})
            WITH sum(a.attempt_count) AS total_attempts,
                 sum(a.correct_count) AS total_correct
            RETURN total_attempts,
                   total_correct,
                   CASE WHEN total_attempts > 0 
                        THEN toFloat(total_correct) / total_attempts * 100 
                        ELSE 0 END AS accuracy
            """
            result = self.client.run_query(query, {
                'subject': subject,
                'topic': topic
            })
        elif subject:
            # Subject-specific stats
            query = """
            MATCH (u:User {id: 'default_user'})-[a:ATTEMPTED]->(q:Question)
            MATCH (q)<-[:HAS_QUESTION]-(t:Topic {subject: $subject})
            WITH sum(a.attempt_count) AS total_attempts,
                 sum(a.correct_count) AS total_correct
            RETURN total_attempts,
                   total_correct,
                   CASE WHEN total_attempts > 0 
                        THEN toFloat(total_correct) / total_attempts * 100 
                        ELSE 0 END AS accuracy
            """
            result = self.client.run_query(query, {'subject': subject})
        else:
            # Overall stats
            query = """
            MATCH (u:User {id: 'default_user'})-[a:ATTEMPTED]->(q:Question)
            WITH sum(a.attempt_count) AS total_attempts,
                 sum(a.correct_count) AS total_correct
            RETURN total_attempts,
                   total_correct,
                   CASE WHEN total_attempts > 0 
                        THEN toFloat(total_correct) / total_attempts * 100 
                        ELSE 0 END AS accuracy
            """
            result = self.client.run_query(query)

        if result and result[0]:
            return {
                'attempted': result[0].get('total_attempts', 0) or 0,
                'correct': result[0].get('total_correct', 0) or 0,
                'accuracy': round(result[0].get('accuracy', 0) or 0, 1)
            }

        return {'attempted': 0, 'correct': 0, 'accuracy': 0.0}

    def get_topic_progress(self, subject: str) -> List[Dict]:
        """
        Get progress for all topics in a subject

        Args:
            subject: Subject name

        Returns:
            List of topic progress dictionaries
        """
        query = """
        MATCH (t:Topic {subject: $subject})
        OPTIONAL MATCH (t)-[:HAS_QUESTION]->(q:Question)<-[a:ATTEMPTED]-(u:User {id: 'default_user'})
        WITH t, 
             count(DISTINCT q) AS total_questions,
             sum(a.attempt_count) AS attempts,
             sum(a.correct_count) AS correct
        RETURN t.name AS topic,
               t.difficulty_level AS difficulty,
               total_questions,
               COALESCE(attempts, 0) AS attempts,
               COALESCE(correct, 0) AS correct,
               CASE WHEN attempts > 0 
                    THEN toFloat(correct) / attempts * 100 
                    ELSE 0 END AS accuracy
        ORDER BY t.name
        """

        try:
            results = self.client.run_query(query, {'subject': subject})
            return results
        except Exception as e:
            print(f"Error getting topic progress: {e}")
            return []

    def get_weak_topics(self, subject: str = None,
                        threshold: float = 60.0) -> List[Dict]:
        """
        Get topics where user is performing poorly

        Args:
            subject: Optional subject filter
            threshold: Accuracy threshold (default 60%)

        Returns:
            List of weak topics
        """
        query = """
        MATCH (t:Topic)
        """

        if subject:
            query += "WHERE t.subject = $subject\n"

        query += """
        MATCH (t)-[:HAS_QUESTION]->(q:Question)<-[a:ATTEMPTED]-(u:User {id: 'default_user'})
        WITH t,
             sum(a.attempt_count) AS attempts,
             sum(a.correct_count) AS correct,
             toFloat(sum(a.correct_count)) / sum(a.attempt_count) * 100 AS accuracy
        WHERE attempts >= 3 AND accuracy < $threshold
        RETURN t.name AS topic,
               t.subject AS subject,
               t.difficulty_level AS difficulty,
               attempts,
               correct,
               accuracy
        ORDER BY accuracy ASC, attempts DESC
        LIMIT 10
        """

        try:
            params = {'threshold': threshold}
            if subject:
                params['subject'] = subject

            results = self.client.run_query(query, params)
            return results
        except Exception as e:
            print(f"Error getting weak topics: {e}")
            return []


# Example usage
if __name__ == "__main__":
    from src.graph.neo4j_client import Neo4jClient

    client = Neo4jClient()
    tracker = ProgressTracker(client)

    # Get overall stats
    stats = tracker.get_user_stats()
    print("\nOverall Stats:")
    print(f"  Attempted: {stats['attempted']}")
    print(f"  Correct: {stats['correct']}")
    print(f"  Accuracy: {stats['accuracy']}%")

    client.close()
