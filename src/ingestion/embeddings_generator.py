"""
Embeddings generation module using sentence-transformers
"""

from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import sys

sys.path.append('..')
from config.config import config


class EmbeddingsGenerator:
    """Generate embeddings for text chunks"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embeddings generator

        Args:
            model_name: Name of sentence-transformers model
                Options:
                - 'all-MiniLM-L6-v2' (384 dim, fast, default)
                - 'all-mpnet-base-v2' (768 dim, better quality)
                - 'all-MiniLM-L12-v2' (384 dim, balanced)
        """
        print(f"Loading embedding model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"✅ Model loaded. Dimension: {self.dimension}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            Embedding vector as list
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimension

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimension

    def generate_embeddings_batch(self, texts: List[str],
                                  batch_size: int = 32,
                                  show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Show progress bar

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts and keep track of indices
        valid_texts = []
        valid_indices = []

        for idx, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(idx)

        if not valid_texts:
            return [[0.0] * self.dimension] * len(texts)

        try:
            # Generate embeddings for valid texts
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )

            # Create result list with proper indices
            result = [[0.0] * self.dimension] * len(texts)
            for valid_idx, original_idx in enumerate(valid_indices):
                result[original_idx] = embeddings[valid_idx].tolist()

            return result

        except Exception as e:
            print(f"Error in batch embedding generation: {e}")
            return [[0.0] * self.dimension] * len(texts)

    def embed_chunks(self, chunks: List[Dict],
                     batch_size: int = 32) -> List[Dict]:
        """
        Add embeddings to chunk dictionaries

        Args:
            chunks: List of chunk dictionaries
            batch_size: Batch size for processing

        Returns:
            Chunks with embeddings added
        """
        if not chunks:
            return []

        print(f"Generating embeddings for {len(chunks)} chunks...")

        # Extract texts
        texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts, batch_size)

        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding

        print(f"✅ Generated {len(embeddings)} embeddings")

        return chunks

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


# Example usage
if __name__ == "__main__":
    embedder = EmbeddingsGenerator()

    sample_texts = [
        "Process synchronization is critical in operating systems.",
        "Semaphores are used to solve synchronization problems.",
        "Deadlock occurs when processes wait indefinitely for resources."
    ]

    # Single embedding
    single_emb = embedder.generate_embedding(sample_texts[0])
    print(f"\nSingle embedding dimension: {len(single_emb)}")

    # Batch embeddings
    batch_embs = embedder.generate_embeddings_batch(sample_texts)
    print(f"Generated {len(batch_embs)} embeddings")
    print(f"First embedding (first 5 values): {batch_embs[0][:5]}")
