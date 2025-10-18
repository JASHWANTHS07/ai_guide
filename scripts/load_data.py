import sys

sys.path.append('..')

from src.ingestion.pdf_processor import PDFProcessor
from src.ingestion.text_splitter import TextChunker
from src.ingestion.embeddings_generator import EmbeddingsGenerator
from src.graph.neo4j_client import Neo4jClient
from src.graph.graph_builder import GraphBuilder
from pathlib import Path
from tqdm import tqdm
import json


def load_syllabus():
    """Load syllabus into graph"""
    print("\n" + "=" * 60)
    print("LOADING SYLLABUS")
    print("=" * 60)

    # Define syllabus structure
    # TODO: Adapt this to your actual syllabus
    syllabus_data = {
        'Operating Systems': {
            'description': 'Fundamentals of operating systems',
            'topics': [
                {'name': 'Process Management', 'description': 'Process scheduling and synchronization',
                 'difficulty': 2},
                {'name': 'Memory Management', 'description': 'Virtual memory and paging', 'difficulty': 3},
                {'name': 'File Systems', 'description': 'File organization and access', 'difficulty': 2},
                {'name': 'Deadlocks', 'description': 'Deadlock handling strategies', 'difficulty': 3},
            ]
        },
        'Database Management Systems': {
            'description': 'Database design and implementation',
            'topics': [
                {'name': 'ER Model', 'description': 'Entity-Relationship modeling', 'difficulty': 1},
                {'name': 'Relational Model', 'description': 'Relational algebra and calculus', 'difficulty': 2},
                {'name': 'Normalization', 'description': 'Normal forms and decomposition', 'difficulty': 3},
                {'name': 'SQL', 'description': 'SQL queries and operations', 'difficulty': 2},
                {'name': 'Transactions', 'description': 'ACID properties and concurrency', 'difficulty': 3},
            ]
        },
        'Algorithms': {
            'description': 'Design and analysis of algorithms',
            'topics': [
                {'name': 'Sorting', 'description': 'Various sorting algorithms', 'difficulty': 2},
                {'name': 'Searching', 'description': 'Search algorithms', 'difficulty': 1},
                {'name': 'Dynamic Programming', 'description': 'DP techniques', 'difficulty': 4},
                {'name': 'Greedy Algorithms', 'description': 'Greedy approach', 'difficulty': 3},
                {'name': 'Graph Algorithms', 'description': 'Graph traversal and shortest paths', 'difficulty': 3},
            ]
        },
        # Add more subjects and topics as needed
    }

    client = Neo4jClient()
    builder = GraphBuilder(client)

    builder.load_syllabus(syllabus_data)

    stats = builder.get_graph_statistics()
    print(f"\n✅ Syllabus loaded:")
    print(f"   Subjects: {stats['subjects']}")
    print(f"   Topics: {stats['topics']}")

    client.close()


def load_pyqs():
    """Load previous years questions"""
    print("\n" + "=" * 60)
    print("LOADING PREVIOUS YEARS QUESTIONS")
    print("=" * 60)

    processor = PDFProcessor()
    client = Neo4jClient()
    builder = GraphBuilder(client)

    pyq_dir = Path("data/raw/pyqs")
    pdf_files = list(pyq_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PYQ PDFs")

    all_questions = []
    for pdf_file in tqdm(pdf_files, desc="Processing PYQs"):
        # Extract year and set from filename
        # Assuming format: gate_YYYY_setN.pdf
        filename = pdf_file.stem
        parts = filename.split('_')
        year = int(parts) if len(parts) > 1 else 2023
        paper_set = parts if len(parts) > 2 else 'set1'

        # Extract questions
        questions = processor.extract_questions_from_pyq(
            str(pdf_file), year, paper_set
        )

        # TODO: You need to map questions to subjects/topics
        # This is a simplified example
        for q in questions:
            q['subject'] = 'Operating Systems'  # Detect from question
            q['topic'] = 'Process Management'  # Detect from question

        all_questions.extend(questions)

    # Load into graph
    builder.load_pyqs(all_questions)

    print(f"\n✅ Loaded {len(all_questions)} questions")

    client.close()


def load_textbooks():
    """Load and chunk textbooks"""
    print("\n" + "=" * 60)
    print("LOADING TEXTBOOKS")
    print("=" * 60)

    processor = PDFProcessor()
    chunker = TextChunker()
    embedder = EmbeddingsGenerator()
    client = Neo4jClient()
    builder = GraphBuilder(client)

    textbook_dir = Path("data/raw/textbooks")
    pdf_files = list(textbook_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} textbook PDFs")

    all_chunks = []
    for pdf_file in tqdm(pdf_files, desc="Processing textbooks"):
        # Extract text
        doc_data = processor.extract_text_from_pdf(str(pdf_file))

        # Chunk the document
        chunks = chunker.chunk_document(doc_data)

        # TODO: Map chunks to subjects/topics based on filename or content
        subject = 'Operating Systems'  # Detect from filename
        topic = 'Process Management'  # Detect from content

        # Add metadata
        for chunk in chunks:
            chunk['subject'] = subject
            chunk['topic'] = topic
            chunk['source_file'] = pdf_file.name

        # Generate embeddings in batches
        chunks_with_embeddings = embedder.embed_chunks(chunks)

        all_chunks.extend(chunks_with_embeddings)

    # Load into graph
    builder.load_textbook_chunks(all_chunks)

    print(f"\n✅ Loaded {len(all_chunks)} textbook chunks")

    client.close()


def main():
    """Main data loading pipeline"""
    print("\n" + "=" * 60)
    print("GATE CS 2026 Prep System - Data Loading")
    print("=" * 60)

    # Step 1: Load syllabus
    load_syllabus()

    # Step 2: Load PYQs
    load_pyqs()

    # Step 3: Load textbooks
    load_textbooks()

    print("\n" + "=" * 60)
    print("✅ DATA LOADING COMPLETE!")
    print("=" * 60)
    print("\nYou can now run the application:")
    print("  streamlit run ui/app.py")


if __name__ == "__main__":
    main()
