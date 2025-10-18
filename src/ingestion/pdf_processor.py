"""
PDF text extraction module using PyMuPDF
Handles extraction from PYQs, textbooks, and syllabus documents
"""

import pymupdf
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import re


class PDFProcessor:
    """Extract text from PDF files using PyMuPDF"""

    def __init__(self):
        self.supported_formats = ['.pdf']

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract text from a single PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with metadata and text by page
        """
        try:
            doc = pymupdf.open(pdf_path)

            result = {
                'file_path': pdf_path,
                'file_name': Path(pdf_path).name,
                'total_pages': len(doc),
                'pages': []
            }

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                result['pages'].append({
                    'page_number': page_num + 1,
                    'text': text,
                    'word_count': len(text.split())
                })

            doc.close()
            return result

        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return None

    def process_directory(self, directory_path: str,
                          pattern: str = "*.pdf") -> List[Dict]:
        """
        Process all PDFs in a directory

        Args:
            directory_path: Path to directory containing PDFs
            pattern: File pattern to match (default: "*.pdf")

        Returns:
            List of extracted text dictionaries
        """
        directory = Path(directory_path)
        if not directory.exists():
            print(f"Directory not found: {directory_path}")
            return []

        pdf_files = list(directory.glob(pattern))

        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return []

        results = []
        for pdf_file in tqdm(pdf_files, desc=f"Processing PDFs from {directory.name}"):
            try:
                extracted = self.extract_text_from_pdf(str(pdf_file))
                if extracted:
                    results.append(extracted)
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")

        return results

    def extract_questions_from_pyq(self, pdf_path: str, year: int,
                                   paper_set: str) -> List[Dict]:
        """
        Extract questions from PYQ PDF with metadata

        Args:
            pdf_path: Path to PYQ PDF
            year: Year of the exam
            paper_set: Paper set identifier

        Returns:
            List of question dictionaries
        """
        extracted = self.extract_text_from_pdf(pdf_path)
        if not extracted:
            return []

        all_text = "\n".join([p['text'] for p in extracted['pages']])

        # Extract questions using pattern matching
        questions = self._parse_questions(all_text, year, paper_set)

        return questions

    def _parse_questions(self, text: str, year: int,
                         paper_set: str) -> List[Dict]:
        """
        Parse questions from text

        This is a basic implementation. You may need to customize
        based on your PYQ format.
        """
        questions = []

        # Split by question numbers
        # Common patterns: "Q.1", "Q 1", "Question 1", "1.", etc.
        question_pattern = r'(?:Q\.?\s*|Question\s+)?(\d+)[\.\)]\s*'

        # Split text by question markers
        parts = re.split(question_pattern, text)

        # Process parts (odd indices are question numbers, even indices are content)
        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break

            q_num = parts[i]
            content = parts[i + 1].strip()

            if not content:
                continue

            # Extract options if present
            options = self._extract_options(content)

            # Clean question text (remove options from main text)
            question_text = content
            if options:
                for opt in options:
                    question_text = question_text.replace(opt, '')

            question_text = question_text.strip()

            if len(question_text) < 10:  # Skip if too short
                continue

            questions.append({
                'question_number': int(q_num),
                'question_text': question_text,
                'options': options,
                'year': year,
                'paper_set': paper_set,
                'answer': '',  # To be filled manually or via OCR
                'difficulty': 0,  # To be classified later
                'marks': 1  # Default
            })

        return questions

    def _extract_options(self, text: str) -> List[str]:
        """Extract MCQ options from text"""
        options = []

        # Pattern for options: (A), (B), (C), (D) or A), B), C), D)
        option_pattern = r'\(?([A-D])\)[\s:]+(.*?)(?=\(?[A-D]\)|$)'

        matches = re.finditer(option_pattern, text, re.DOTALL)

        for match in matches:
            letter = match.group(1)
            option_text = match.group(2).strip()

            # Clean up option text
            option_text = ' '.join(option_text.split())

            if option_text:
                options.append(f"({letter}) {option_text}")

        return options

    def extract_syllabus_structure(self, pdf_path: str) -> Dict:
        """
        Extract syllabus structure from PDF

        Args:
            pdf_path: Path to syllabus PDF

        Returns:
            Dictionary with subjects and topics
        """
        extracted = self.extract_text_from_pdf(pdf_path)
        if not extracted:
            return {}

        all_text = "\n".join([p['text'] for p in extracted['pages']])

        # This is a basic implementation
        # You'll need to customize based on your syllabus format
        syllabus = self._parse_syllabus(all_text)

        return syllabus

    def _parse_syllabus(self, text: str) -> Dict:
        """
        Parse syllabus structure from text

        Customize this based on your syllabus format
        """
        # Example structure - customize as needed
        syllabus = {}

        # Simple line-by-line parsing
        lines = text.split('\n')
        current_subject = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line looks like a subject heading (all caps or title case)
            if line.isupper() or (line.istitle() and len(line.split()) <= 5):
                current_subject = line
                syllabus[current_subject] = {
                    'description': '',
                    'topics': []
                }
            elif current_subject:
                # Assume it's a topic
                # Clean and add
                topic_name = line.strip('•-–—*').strip()
                if topic_name and len(topic_name) > 3:
                    syllabus[current_subject]['topics'].append({
                        'name': topic_name,
                        'description': '',
                        'difficulty': 2  # Default medium difficulty
                    })

        return syllabus


# Example usage
if __name__ == "__main__":
    processor = PDFProcessor()

    # Test with a single PDF
    print("Testing PDF extraction...")

    # Test PYQ extraction
    # result = processor.extract_questions_from_pyq(
    #     "data/raw/pyqs/gate2023_set1.pdf",
    #     year=2023,
    #     paper_set="Set-1"
    # )
    # print(f"Extracted {len(result)} questions")

    # Test directory processing
    # results = processor.process_directory("data/raw/textbooks/")
    # print(f"Processed {len(results)} textbooks")
