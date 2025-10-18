import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from config.config import config
except ModuleNotFoundError as e:
    print("ERROR: Configuration module not found.")
    print("Please ensure config/config.py exists.")
    print(f"Current directory: {Path.cwd()}")
    sys.exit(1)

from neo4j import GraphDatabase


class DatabaseSetup:
    """Setup Neo4j database with indexes and constraints"""

    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
            )
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            print("\nPlease ensure:")
            print("1. Neo4j Desktop is running")
            print("2. Database is started")
            print("3. Credentials in .env are correct")
            sys.exit(1)

    def verify_connection(self):
        """Verify database connection"""
        try:
            self.driver.verify_connectivity()
            print("✅ Neo4j connection verified")
            return True
        except Exception as e:
            print(f"❌ Connection verification failed: {e}")
            return False

    def create_constraints(self):
        """Create uniqueness constraints"""
        print("\n📝 Creating constraints...")

        constraints = [
            "CREATE CONSTRAINT subject_name_unique IF NOT EXISTS FOR (s:Subject) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT topic_unique IF NOT EXISTS FOR (t:Topic) REQUIRE (t.name, t.subject) IS UNIQUE",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"  ✓ {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                except Exception as e:
                    print(f"  ⚠ {e}")

    def create_indexes(self):
        """Create indexes for performance"""
        print("\n📝 Creating indexes...")

        indexes = [
            "CREATE INDEX subject_name IF NOT EXISTS FOR (s:Subject) ON (s.name)",
            "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
            "CREATE INDEX topic_subject IF NOT EXISTS FOR (t:Topic) ON (t.subject)",
            "CREATE INDEX question_year IF NOT EXISTS FOR (q:Question) ON (q.year)",
            "CREATE INDEX question_difficulty IF NOT EXISTS FOR (q:Question) ON (q.difficulty)",
            "CREATE INDEX chunk_source IF NOT EXISTS FOR (c:Chunk) ON (c.source_type)",
        ]

        with self.driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    index_name = index.split('FOR')[1].split('ON')[0].strip()
                    print(f"  ✓ {index_name}")
                except Exception as e:
                    print(f"  ⚠ {e}")

    def create_vector_index(self):
        """Create vector index for embeddings"""
        print("\n📝 Creating vector index...")

        query = """
        CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
        FOR (c:Chunk)
        ON c.embedding
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
            }
        }
        """

        try:
            with self.driver.session() as session:
                session.run(query)
                print("  ✓ Vector index 'chunk_embeddings' created")
        except Exception as e:
            print(f"  ⚠ Vector index creation: {e}")

    def get_database_stats(self):
        """Get current database statistics"""
        print("\n📊 Database Statistics:")

        queries = {
            'Subjects': "MATCH (s:Subject) RETURN count(s) as count",
            'Topics': "MATCH (t:Topic) RETURN count(t) as count",
            'Questions': "MATCH (q:Question) RETURN count(q) as count",
            'Chunks': "MATCH (c:Chunk) RETURN count(c) as count",
            'Concepts': "MATCH (c:Concept) RETURN count(c) as count",
        }

        with self.driver.session() as session:
            for name, query in queries.items():
                try:
                    result = session.run(query)
                    count = result.single()['count']
                    print(f"  {name}: {count}")
                except Exception as e:
                    print(f"  {name}: Error - {e}")

    def close(self):
        """Close database connection"""
        self.driver.close()
        print("\n✅ Database connection closed")


def main():
    """Main setup function"""
    print("=" * 60)
    print("GATE CS 2026 Prep System - Database Setup")
    print("=" * 60)

    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("\n❌ .env file not found!")
        print("Please create .env file with your credentials.")
        print("\nExample .env content:")
        print("-" * 40)
        print("NEO4J_URI=neo4j://localhost:7687")
        print("NEO4J_USERNAME=neo4j")
        print("NEO4J_PASSWORD=your_password")
        print("GEMINI_API_KEY=your_api_key")
        print("-" * 40)
        sys.exit(1)

    # Check configuration
    if not config.NEO4J_PASSWORD:
        print("\n❌ NEO4J_PASSWORD not set in .env file")
        sys.exit(1)

    # Initialize setup
    setup = DatabaseSetup()

    # Verify connection
    if not setup.verify_connection():
        setup.close()
        sys.exit(1)

    # Create constraints
    setup.create_constraints()

    # Create indexes
    setup.create_indexes()

    # Create vector index
    setup.create_vector_index()

    # Show statistics
    setup.get_database_stats()

    # Close connection
    setup.close()

    print("\n" + "=" * 60)
    print("✅ DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Place your PDF files in data/raw/ directories")
    print("2. Run: python scripts/load_data.py")
    print("3. Run: streamlit run ui/app.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
