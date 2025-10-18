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