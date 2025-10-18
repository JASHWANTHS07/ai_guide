import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Application configuration"""

    # Neo4j Configuration
    NEO4J_URI: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "neo4j://localhost:7687"))
    NEO4J_USERNAME: str = Field(default_factory=lambda: os.getenv("NEO4J_USERNAME", "neo4j"))
    NEO4J_PASSWORD: Optional[str] = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD"))

    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))

    # Application Settings
    CHUNK_SIZE: int = Field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "500")))
    CHUNK_OVERLAP: int = Field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "100")))
    EMBEDDING_DIMENSION: int = Field(default_factory=lambda: int(os.getenv("EMBEDDING_DIMENSION", "384")))
    MAX_TOKENS: int = Field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "2000")))
    TEMPERATURE: float = Field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.0")))

    class Config:
        arbitrary_types_allowed = True


# Create global config instance
config = Config()

# Validate critical settings
if not config.NEO4J_PASSWORD:
    print("WARNING: NEO4J_PASSWORD not set in .env file")

if not config.GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set in .env file")
