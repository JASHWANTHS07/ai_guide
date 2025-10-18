"""
Text chunking module for splitting documents into manageable pieces
"""

from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
import sys

sys.path.append('..')
from config.config import config


class TextChunker:
    """Split text into chunks for embedding and retrieval"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize text chunker

        Args:
            chunk_size: Size of each chunk (default from config)
            chunk_overlap: Overlap between chunks (default from config)
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks with metadata

        Args:
            text: Text to split
            metadata: Additional metadata to attach

        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            return []

        chunks = self.splitter.split_text(text)

        result = []
        for idx, chunk in enumerate(chunks):
            chunk_dict = {
                'chunk_id': idx,
                'text': chunk.strip(),
                'char_count': len(chunk),
                'word_count': len(chunk.split()),
                'metadata': metadata or {}
            }
            result.append(chunk_dict)

        return result

    def chunk_document(self, document: Dict,
                       subject: str = None,
                       topic: str = None) -> List[Dict]:
        """
        Chunk an entire document (from PDF extraction)

        Args:
            document: Document dictionary from PDFProcessor
            subject: Subject name (optional)
            topic: Topic name (optional)

        Returns:
            List of chunks with document metadata
        """
        # Combine all pages
        all_text = "\n\n".join([
            page['text'] for page in document['pages']
            if page['text'].strip()
        ])

        metadata = {
            'file_name': document['file_name'],
            'total_pages': document['total_pages'],
            'source_type': 'textbook'
        }

        if subject:
            metadata['subject'] = subject
        if topic:
            metadata['topic'] = topic

        chunks = self.chunk_text(all_text, metadata)

        # Add page number information to each chunk
        for chunk in chunks:
            chunk['source_file'] = document['file_name']

        return chunks

    def chunk_by_subject_topic(self, text: str, subject: str,
                               topic: str, source_file: str = None) -> List[Dict]:
        """
        Chunk text with subject/topic metadata

        Args:
            text: Text to chunk
            subject: Subject name
            topic: Topic name
            source_file: Source filename (optional)

        Returns:
            List of chunks with subject/topic metadata
        """
        metadata = {
            'subject': subject,
            'topic': topic,
            'source_type': 'textbook'
        }

        if source_file:
            metadata['source_file'] = source_file

        chunks = self.chunk_text(text, metadata)

        # Add source file to each chunk
        for chunk in chunks:
            if source_file:
                chunk['source_file'] = source_file

        return chunks

    def chunk_questions(self, questions: List[Dict]) -> List[Dict]:
        """
        Process questions into chunk format

        Args:
            questions: List of question dictionaries

        Returns:
            List of question chunks
        """
        chunks = []

        for idx, q in enumerate(questions):
            # Combine question text and options
            full_text = q['question_text']
            if q.get('options'):
                full_text += "\n" + "\n".join(q['options'])

            chunk = {
                'chunk_id': idx,
                'text': full_text,
                'char_count': len(full_text),
                'word_count': len(full_text.split()),
                'metadata': {
                    'type': 'question',
                    'year': q.get('year'),
                    'paper_set': q.get('paper_set'),
                    'difficulty': q.get('difficulty', 0),
                    'subject': q.get('subject'),
                    'topic': q.get('topic')
                },
                'question_data': q
            }

            chunks.append(chunk)

        return chunks


# Example usage
if __name__ == "__main__":
    chunker = TextChunker()

    # Test chunking
    sample_text = """
    Operating systems manage hardware resources and provide services to applications.
    Process management is a key responsibility, including scheduling and synchronization.
    Memory management involves allocation and deallocation of memory to processes.
    The file system provides persistent storage and organization of data.
    """

    chunks = chunker.chunk_by_subject_topic(
        sample_text,
        subject="Operating Systems",
        topic="Introduction"
    )

    print(f"Created {len(chunks)} chunks")
    for chunk in chunks:
        print(f"Chunk {chunk['chunk_id']}: {chunk['word_count']} words")
