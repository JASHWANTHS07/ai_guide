"""
Answer generation using Google Gemini API
"""

from typing import List, Dict, Optional
from google import genai
import sys

sys.path.append('../..')
from config.config import config


class AnswerGenerator:
    """Generate answers and explanations using Gemini"""

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize answer generator

        Args:
            model_name: Gemini model to use
        """
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.client = genai.Client()
            self.model_name = model_name
            print(f"✅ Gemini API initialized with model: {model_name}")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            raise

    def generate_explanation(self, question: str, answer: str,
                             subject: str, topic: str,
                             context: List[Dict] = None) -> str:
        """
        Generate explanation for a question

        Args:
            question: Question text
            answer: Correct answer
            subject: Subject name
            topic: Topic name
            context: Additional context chunks

        Returns:
            Explanation text
        """
        # Build prompt with context
        prompt = f"""You are an expert tutor preparing students for the GATE Computer Science exam.

Subject: {subject}
Topic: {topic}

Question: {question}
Correct Answer: {answer}

"""

        if context:
            prompt += "\nRelevant study material:\n"
            for chunk in context[:3]:
                prompt += f"- {chunk.get('text', '')[:200]}...\n"

        prompt += """
Please provide a detailed explanation that:
1. Explains why the correct answer is right
2. Explains why other options are wrong (if applicable)
3. Provides the underlying concept with examples
4. Gives tips to remember this concept

Keep the explanation clear, concise, and helpful for exam preparation.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return "Error generating explanation. Please try again."

    def teach(self, query: str, subject: str, topic: str,
              context: Dict) -> str:
        """
        Generate teaching content for a topic

        Args:
            query: User's question or learning query
            subject: Subject name
            topic: Topic name
            context: Context from hybrid search

        Returns:
            Teaching content
        """
        # Extract relevant context
        topic_info = context.get('topic_info', {})
        relevant_chunks = context.get('relevant_chunks', [])

        prompt = f"""You are an expert teacher for GATE Computer Science preparation.

Subject: {subject}
Topic: {topic}
Topic Description: {topic_info.get('description', 'N/A')}
Difficulty Level: {topic_info.get('difficulty', 'N/A')}/5

Student's Question: {query}

Relevant Study Material:
"""

        for idx, chunk in enumerate(relevant_chunks[:5], 1):
            prompt += f"\n{idx}. {chunk.get('text', '')[:300]}...\n"

        prompt += """
Based on the above context, provide a comprehensive explanation that:
1. Directly answers the student's question
2. Explains the core concepts with clear examples
3. Relates concepts to real-world applications
4. Highlights key points for GATE exam preparation
5. Provides practice tips

Make the explanation engaging and easy to understand.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error in teach mode: {e}")
            return "Error generating teaching content. Please try again."

    def generate_practice_questions(self, subject: str, topic: str,
                                    num_questions: int = 5,
                                    difficulty: int = 2,
                                    example_questions: List[Dict] = None) -> List[Dict]:
        """
        Generate practice questions similar to GATE

        Args:
            subject: Subject name
            topic: Topic name
            num_questions: Number of questions to generate
            difficulty: Difficulty level (1-5)
            example_questions: Example PYQs for reference

        Returns:
            List of generated questions
        """
        prompt = f"""You are creating GATE Computer Science practice questions.

Subject: {subject}
Topic: {topic}
Difficulty Level: {difficulty}/5 (1=Easy, 5=Very Hard)
Number of Questions: {num_questions}

"""

        if example_questions:
            prompt += "\nExample questions from previous GATE papers:\n"
            for idx, eq in enumerate(example_questions[:3], 1):
                prompt += f"\n{idx}. {eq.get('question', '')}\n"
                if eq.get('options'):
                    for opt in eq['options']:
                        prompt += f"   {opt}\n"

        prompt += f"""
Generate {num_questions} multiple-choice questions similar to GATE pattern:
- Each question should test conceptual understanding
- Provide 4 options (A, B, C, D)
- Indicate the correct answer
- Provide a brief explanation

Format each question as:
Question [N]:
[Question text]
(A) [Option A]
(B) [Option B]
(C) [Option C]
(D) [Option D]
Correct Answer: [Letter]
Explanation: [Brief explanation]

---
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Parse the response
            questions = self._parse_generated_questions(response.text)
            return questions

        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    def _parse_generated_questions(self, text: str) -> List[Dict]:
        """Parse generated questions from text"""
        questions = []

        # Split by question separator
        parts = text.split('---')

        for part in parts:
            if 'Question' not in part:
                continue

            lines = part.strip().split('\n')
            question_data = {
                'question': '',
                'options': [],
                'answer': '',
                'explanation': ''
            }

            current_section = 'question'

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('(A)') or line.startswith('(B)') or \
                        line.startswith('(C)') or line.startswith('(D)'):
                    question_data['options'].append(line)
                    current_section = 'options'
                elif line.startswith('Correct Answer:'):
                    question_data['answer'] = line.replace('Correct Answer:', '').strip()
                    current_section = 'answer'
                elif line.startswith('Explanation:'):
                    question_data['explanation'] = line.replace('Explanation:', '').strip()
                    current_section = 'explanation'
                elif current_section == 'question' and 'Question' not in line:
                    question_data['question'] += ' ' + line
                elif current_section == 'explanation':
                    question_data['explanation'] += ' ' + line

            if question_data['question'] and question_data['options']:
                questions.append(question_data)

        return questions

    def build_reading_material(self, subject: str, topic: str,
                               chunks: List[Dict]) -> str:
        """
        Build structured reading material from chunks

        Args:
            subject: Subject name
            topic: Topic name
            chunks: Text chunks from retrieval

        Returns:
            Formatted reading material
        """
        # Combine chunks
        context = "\n\n".join([chunk.get('text', '') for chunk in chunks[:10]])

        prompt = f"""You are creating study material for GATE Computer Science preparation.

Subject: {subject}
Topic: {topic}

Source Material:
{context}

Create a comprehensive, well-structured study guide that:
1. Starts with an introduction to the topic
2. Explains key concepts in a logical sequence
3. Provides examples and illustrations
4. Highlights important points for GATE exam
5. Ends with a summary of key takeaways

Structure the content with clear headings and subheadings.
Make it suitable for self-study and revision.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error building reading material: {e}")
            return "Error generating reading material. Please try again."

    def generate_flashcards(self, subject: str, topic: str,
                            num_cards: int = 10) -> List[Dict]:
        """
        Generate flashcards for spaced repetition

        Args:
            subject: Subject name
            topic: Topic name
            num_cards: Number of flashcards

        Returns:
            List of flashcard dictionaries
        """
        prompt = f"""Create {num_cards} flashcards for GATE Computer Science preparation.

Subject: {subject}
Topic: {topic}

For each flashcard:
- Front: A clear, concise question or prompt
- Back: A detailed answer with key points

Format:
Card [N]:
Front: [Question]
Back: [Answer]
---
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Parse flashcards
            flashcards = self._parse_flashcards(response.text, subject, topic)
            return flashcards

        except Exception as e:
            print(f"Error generating flashcards: {e}")
            return []

    def _parse_flashcards(self, text: str, subject: str, topic: str) -> List[Dict]:
        """Parse generated flashcards"""
        flashcards = []

        cards = text.split('---')

        for idx, card in enumerate(cards):
            if 'Front:' not in card or 'Back:' not in card:
                continue

            lines = card.strip().split('\n')
            front = ''
            back = ''
            current = None

            for line in lines:
                if line.strip().startswith('Front:'):
                    current = 'front'
                    front = line.replace('Front:', '').strip()
                elif line.strip().startswith('Back:'):
                    current = 'back'
                    back = line.replace('Back:', '').strip()
                elif current == 'front':
                    front += ' ' + line.strip()
                elif current == 'back':
                    back += ' ' + line.strip()

            if front and back:
                flashcards.append({
                    'id': f"{subject}_{topic}_{idx}",
                    'subject': subject,
                    'topic': topic,
                    'front': front.strip(),
                    'back': back.strip()
                })

        return flashcards


# Example usage
if __name__ == "__main__":
    generator = AnswerGenerator()

    # Test explanation generation
    explanation = generator.generate_explanation(
        question="What is a semaphore?",
        answer="A synchronization primitive",
        subject="Operating Systems",
        topic="Process Synchronization"
    )

    print("Explanation:")
    print(explanation)
