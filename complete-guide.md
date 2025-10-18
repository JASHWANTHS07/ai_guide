# GATE CS 2026 Preparation System
## Complete Step-by-Step Implementation Guide

---

## 📋 Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Detailed Setup Instructions](#detailed-setup-instructions)
3. [Data Loading Pipeline](#data-loading-pipeline)
4. [System Components Overview](#system-components-overview)
5. [Usage Guide](#usage-guide)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10 or higher
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection for API calls

### 5-Minute Setup

```bash
# 1. Clone/create project directory
mkdir gate-cs-prep-system && cd gate-cs-prep-system

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Create requirements.txt and install
pip install -r requirements.txt

# 4. Download Neo4j Desktop from https://neo4j.com/download/

# 5. Get Gemini API key from https://ai.google.dev/

# 6. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 7. Setup database
python setup_database.py

# 8. Run the application
streamlit run ui/app.py
```

---

## 📝 Detailed Setup Instructions

### Step 1: Python Environment Setup

**For macOS/Linux:**
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Create project directory
mkdir gate-cs-prep-system
cd gate-cs-prep-system

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation
which python  # Should point to venv/bin/python
```

**For Windows:**
```cmd
# Check Python version
python --version

# Create project directory
mkdir gate-cs-prep-system
cd gate-cs-prep-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation
where python  # Should point to venv\Scripts\python.exe
```

### Step 2: Install Dependencies

**Create requirements.txt:**
```text
# Core Dependencies
python>=3.10

# Graph Database
neo4j==5.24.0
neo4j-graphrag==0.9.0

# LLM & Embeddings
google-genai==1.0.0
langchain==0.3.0
langchain-neo4j==0.3.0
langchain-google-genai==2.0.0
langchain-community==0.3.0

# PDF Processing
pymupdf==1.24.10

# Text Processing
tiktoken==0.7.0
sentence-transformers==3.0.1

# Web Framework
streamlit==1.38.0
plotly==5.23.0
pandas==2.2.2

# Spaced Repetition
fsrs==4.3.2

# Utilities
python-dotenv==1.0.1
tqdm==4.66.5
numpy==1.26.4
pydantic==2.9.0

# Development
pytest==8.3.2
jupyter==1.0.0
black==24.8.0
```

**Install packages:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Neo4j Desktop Installation

**Download Neo4j Desktop:**
1. Visit [https://neo4j.com/download/](https://neo4j.com/download/)
2. Click "Download Desktop"
3. Fill in your details (you'll receive an activation key)
4. Download for your operating system:
   - macOS: `.dmg` file
   - Windows: `.exe` installer
   - Linux: `.AppImage` file

**Install Neo4j Desktop:**

*macOS:*
```
1. Open the downloaded .dmg file
2. Drag Neo4j Desktop to Applications folder
3. Open from Applications
4. Enter activation key when prompted
```

*Windows:*
```
1. Run the .exe installer
2. Follow installation wizard
3. Launch Neo4j Desktop
4. Enter activation key when prompted
```

*Linux:*
```bash
# Make the AppImage executable
chmod +x neo4j-desktop-*.AppImage

# Run it
./neo4j-desktop-*.AppImage
```

**Create Database:**
```
1. In Neo4j Desktop, click "New" → "Create Project"
2. Name it "GATE-Prep"
3. Click "Add" → "Local DBMS"
4. Configure:
   - Name: gate-prep-db
   - Password: [choose a strong password]
   - Version: 5.11+ (latest)
5. Click "Create"
```

**Install APOC Plugin (Required):**
```
1. Select your database
2. Click "Plugins" tab
3. Find "APOC" and click "Install"
4. Wait for installation to complete
```

**Start Database:**
```
1. Click "Start" button next to your database
2. Wait for status to show "Active"
3. Click "Open" to verify in Neo4j Browser
4. Login with username: neo4j, password: [your password]
```

### Step 4: Get Google Gemini API Key

```
1. Visit https://ai.google.dev/
2. Click "Get API key in Google AI Studio"
3. Sign in with your Google account
4. Click "Get API key" → "Create API key"
5. Copy the generated key (starts with "AI...")
6. Save it securely
```

### Step 5: Project Structure Setup

**Create directory structure:**
```bash
# Create all directories
mkdir -p config
mkdir -p data/raw/{pyqs,textbooks,syllabus}
mkdir -p data/processed/{embeddings,chunks}
mkdir -p src/{ingestion,graph,rag,learning,utils}
mkdir -p ui/{components,styles}
mkdir -p notebooks
mkdir -p tests

# Create __init__.py files
touch config/__init__.py
touch src/__init__.py
touch src/ingestion/__init__.py
touch src/graph/__init__.py
touch src/rag/__init__.py
touch src/learning/__init__.py
touch src/utils/__init__.py
touch ui/__init__.py
```

**Create .env file:**
```bash
cat > .env << 'EOF'
# Neo4j Configuration
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
CHUNK_SIZE=500
CHUNK_OVERLAP=100
EMBEDDING_DIMENSION=384
MAX_TOKENS=2000
TEMPERATURE=0.0
EOF
```

**Edit .env file** and replace:
- `your_neo4j_password_here` with your Neo4j password
- `your_gemini_api_key_here` with your Gemini API key

### Step 6: Verify Installation

**Create test_setup.py:**
```python
from neo4j import GraphDatabase
from google import genai
from config.config import config
import sys

def test_neo4j():
    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USERNAME, config.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("✅ Neo4j: Connected successfully")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j: Connection failed - {e}")
        return False

def test_gemini():
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello"
        )
        print(f"✅ Gemini API: Connected successfully")
        print(f"   Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Gemini API: Connection failed - {e}")
        return False

def test_packages():
    packages = [
        'neo4j', 'streamlit', 'pymupdf', 'langchain',
        'sentence_transformers', 'fsrs', 'pandas'
    ]
    
    all_ok = True
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Not installed")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("=" * 60)
    print("GATE CS 2026 Prep System - Setup Verification")
    print("=" * 60)
    
    print("\n1. Testing Package Installation:")
    packages_ok = test_packages()
    
    print("\n2. Testing Neo4j Connection:")
    neo4j_ok = test_neo4j()
    
    print("\n3. Testing Gemini API:")
    gemini_ok = test_gemini()
    
    print("\n" + "=" * 60)
    if packages_ok and neo4j_ok and gemini_ok:
        print("✅ All tests passed! System ready to use.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check configuration.")
        sys.exit(1)
```

**Run verification:**
```bash
python test_setup.py
```

You should see all tests passing.

---

## 📊 Data Loading Pipeline

### Step 1: Prepare Your Data

**Organize your data in these directories:**

```
data/raw/
├── syllabus/
│   └── gate_cs_syllabus.pdf
├── pyqs/
│   ├── gate_2023_set1.pdf
│   ├── gate_2023_set2.pdf
│   ├── gate_2022_set1.pdf
│   └── ...
└── textbooks/
    ├── operating_systems.pdf
    ├── dbms.pdf
    ├── algorithms.pdf
    └── ...
```

### Step 2: Create Data Loading Script

**Create scripts/load_data.py:**
```python
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
                {'name': 'Process Management', 'description': 'Process scheduling and synchronization', 'difficulty': 2},
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
        year = int(parts[1]) if len(parts) > 1 else 2023
        paper_set = parts[2] if len(parts) > 2 else 'set1'
        
        # Extract questions
        questions = processor.extract_questions_from_pyq(
            str(pdf_file), year, paper_set
        )
        
        # TODO: You need to map questions to subjects/topics
        # This is a simplified example
        for q in questions:
            q['subject'] = 'Operating Systems'  # Detect from question
            q['topic'] = 'Process Management'   # Detect from question
        
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
        topic = 'Process Management'   # Detect from content
        
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
```

**Run data loading:**
```bash
python scripts/load_data.py
```

---

## 🎯 Usage Guide

### Starting the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate

# Start Streamlit app
streamlit run ui/app.py

# App will open at http://localhost:8501
```

### Using Different Modes

**1. Learn Mode:**
- Select subject and topic
- Choose "Learn" action
- Click "Start"
- Answer questions in order of difficulty
- Click "Teach Me" for explanations
- Track your progress

**2. Teach Mode:**
- Select subject and topic
- Choose "Teach" action
- Ask specific questions
- Get AI-generated explanations with examples

**3. Practice Mode:**
- Select subject and topic
- Choose "Practice" action
- Set number of questions and difficulty
- Get AI-generated GATE-level questions

**4. Read Mode:**
- Select subject and topic
- Choose "Read" action
- Get structured reading material from textbooks

**5. Flashcard Mode:**
- Select subject and topic
- Choose "Flashcards" action
- Review due flashcards with spaced repetition

---

## 🔧 Troubleshooting

### Common Issues

**1. Neo4j Connection Error:**
```
Error: Could not connect to Neo4j

Solutions:
- Verify Neo4j Desktop is running
- Check NEO4J_URI in .env file
- Verify password in .env matches Neo4j
- Ensure firewall allows port 7687
```

**2. Gemini API Error:**
```
Error: Invalid API key

Solutions:
- Verify GEMINI_API_KEY in .env
- Check API key is active at ai.google.dev
- Ensure no trailing spaces in .env
```

**3. Import Errors:**
```
Error: ModuleNotFoundError

Solutions:
- Verify virtual environment is activated
- Run: pip install -r requirements.txt
- Check all __init__.py files exist
```

**4. Out of Memory:**
```
Error: MemoryError during embedding generation

Solutions:
- Reduce CHUNK_SIZE in .env
- Process textbooks in smaller batches
- Reduce embedding batch_size
- Add more RAM or use cloud instance
```

### Getting Help

1. Check error logs in terminal
2. Verify .env configuration
3. Test connections with test_setup.py
4. Review Neo4j Browser for data issues

---

## ⚙️ Advanced Configuration

### Customizing Chunk Size

Edit in `.env`:
```
CHUNK_SIZE=500        # Characters per chunk
CHUNK_OVERLAP=100     # Overlap between chunks
```

### Changing Embedding Model

Edit `src/ingestion/embeddings_generator.py`:
```python
# Change model in __init__
self.model = SentenceTransformer('all-MiniLM-L6-v2')

# Options:
# - 'all-MiniLM-L6-v2' (384 dim, fast)
# - 'all-mpnet-base-v2' (768 dim, better quality)
# - 'all-MiniLM-L12-v2' (384 dim, balanced)
```

Update `EMBEDDING_DIMENSION` in `.env` to match.

### Switching Gemini Models

Edit in code where model is specified:
```python
# For faster responses:
model="gemini-2.0-flash"

# For better quality:
model="gemini-1.5-pro"
```

---

## 📈 System Monitoring

### Check Graph Statistics

```python
from src.graph.neo4j_client import Neo4jClient
from src.graph.graph_builder import GraphBuilder

client = Neo4jClient()
builder = GraphBuilder(client)

stats = builder.get_graph_statistics()
print(stats)
# {'subjects': 10, 'topics': 85, 'questions': 500, 'chunks': 2000, 'concepts': 150}

client.close()
```

### Monitor Neo4j Performance

Open Neo4j Browser (localhost:7474) and run:
```cypher
// See all node types and counts
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(*) as count', {})
YIELD value
RETURN label, value.count as count

// Check vector index
SHOW INDEXES
```

---

## 🚀 Next Steps

1. **Customize the syllabus** in `load_data.py`
2. **Add your PDF files** to data/raw directories
3. **Run data loading** script
4. **Launch the app** and start learning!
5. **Iterate and improve** based on your needs

---

## 📚 Additional Resources

- Neo4j Documentation: https://neo4j.com/docs/
- LangChain Documentation: https://python.langchain.com/
- Streamlit Documentation: https://docs.streamlit.io/
- Google Gemini API: https://ai.google.dev/docs

---

**Good luck with your GATE CS 2026 preparation! 🎓**
