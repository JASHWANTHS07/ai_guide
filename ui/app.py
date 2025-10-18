"""
Streamlit UI for GATE CS 2026 Preparation System
"""

import streamlit as st
from typing import Dict, List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.neo4j_client import Neo4jClient
from src.rag.retriever import HybridRetriever
from src.rag.answer_generator import AnswerGenerator
from src.learning.progress_tracker import ProgressTracker
from src.learning.spaced_repetition import SpacedRepetitionManager

# Page configuration
st.set_page_config(
    page_title="GATE CS 2026 Prep System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .question-card {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        try:
            st.session_state.neo4j_client = Neo4jClient()
            st.session_state.retriever = HybridRetriever(st.session_state.neo4j_client)
            st.session_state.answer_gen = AnswerGenerator()
            st.session_state.progress_tracker = ProgressTracker(st.session_state.neo4j_client)
            st.session_state.sr_manager = SpacedRepetitionManager()
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"Initialization error: {e}")
            st.stop()

    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'questions_list' not in st.session_state:
        st.session_state.questions_list = []
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'show_explanation' not in st.session_state:
        st.session_state.show_explanation = False


# Helper functions
def reset_session():
    """Reset session variables"""
    st.session_state.current_question_index = 0
    st.session_state.questions_list = []
    st.session_state.user_answers = {}
    st.session_state.show_explanation = False


# Main application
def main():
    init_session_state()

    # Header
    st.markdown('<div class="main-header">🎓 GATE CS 2026 Preparation System</div>',
                unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("📚 Navigation")

        # Get subjects
        try:
            subjects = st.session_state.retriever.get_all_subjects()
        except Exception as e:
            st.error(f"Error loading subjects: {e}")
            subjects = []

        if not subjects:
            st.warning("No subjects found. Please load syllabus first.")
            st.info("Run: python scripts/load_data.py")
            return

        # Subject selection
        selected_subject = st.selectbox(
            "Select Subject",
            subjects,
            key="subject_selector"
        )

        # Topic selection
        try:
            topics = st.session_state.retriever.get_topics_for_subject(selected_subject)
            topic_names = [t['name'] for t in topics]
        except Exception as e:
            st.error(f"Error loading topics: {e}")
            topic_names = []

        if not topic_names:
            st.warning(f"No topics found for {selected_subject}")
            return

        selected_topic = st.selectbox(
            "Select Topic",
            topic_names,
            key="topic_selector"
        )

        # Action selection
        st.markdown("---")
        st.subheader("🎯 Choose Action")

        action = st.radio(
            "What would you like to do?",
            ["Learn", "Teach", "Practice", "Read", "Flashcards"],
            key="action_selector"
        )

        # Start button
        if st.button("🚀 Start", type="primary", use_container_width=True):
            reset_session()
            st.session_state.action = action
            st.session_state.current_subject = selected_subject
            st.session_state.current_topic = selected_topic
            st.rerun()

        # Progress stats
        st.markdown("---")
        st.subheader("📊 Your Progress")

        try:
            stats = st.session_state.progress_tracker.get_user_stats(
                selected_subject,
                selected_topic
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Attempted", stats.get('attempted', 0))
            with col2:
                st.metric("Accuracy", f"{stats.get('accuracy', 0):.1f}%")
        except Exception as e:
            st.error(f"Error loading stats: {e}")

    # Main content area
    if 'action' in st.session_state and 'current_subject' in st.session_state:
        if st.session_state.action == "Learn":
            learn_mode(st.session_state.current_subject, st.session_state.current_topic)
        elif st.session_state.action == "Teach":
            teach_mode(st.session_state.current_subject, st.session_state.current_topic)
        elif st.session_state.action == "Practice":
            practice_mode(st.session_state.current_subject, st.session_state.current_topic)
        elif st.session_state.action == "Read":
            read_mode(st.session_state.current_subject, st.session_state.current_topic)
        elif st.session_state.action == "Flashcards":
            flashcard_mode(st.session_state.current_subject, st.session_state.current_topic)
    else:
        show_welcome_screen()


# Learn Mode
def learn_mode(subject: str, topic: str):
    """Learn mode: Present questions in order of difficulty"""
    st.header(f"📖 Learn: {subject} - {topic}")

    # Load questions if not already loaded
    if not st.session_state.questions_list:
        with st.spinner("Loading questions..."):
            try:
                questions = st.session_state.retriever.get_questions_ordered_by_difficulty(
                    subject, topic, ascending=True
                )
                st.session_state.questions_list = questions
            except Exception as e:
                st.error(f"Error loading questions: {e}")
                return

            if not questions:
                st.warning("No questions available for this topic.")
                st.info("Questions will be added as you load PYQ data.")
                return

    questions = st.session_state.questions_list
    current_idx = st.session_state.current_question_index

    # Progress bar
    if questions:
        progress = (current_idx) / len(questions)
        st.progress(progress, text=f"Question {current_idx + 1} of {len(questions)}")

        if current_idx < len(questions):
            question = questions[current_idx]

            # Display question
            st.markdown(f"""
            <div class="question-card">
                <h3>Question {current_idx + 1}</h3>
                <p style="font-size: 1.1rem; margin: 1rem 0;">
                    {question['question']}
                </p>
                <p style="color: #666; font-size: 0.9rem;">
                    <strong>Year:</strong> {question.get('year', 'N/A')} | 
                    <strong>Difficulty:</strong> {'⭐' * max(1, question.get('difficulty', 1))}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Display options
            if question.get('options'):
                user_answer = st.radio(
                    "Select your answer:",
                    question['options'],
                    key=f"q_{current_idx}"
                )

                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    if st.button("✓ Submit Answer", type="primary"):
                        is_correct = user_answer == question['answer']
                        st.session_state.user_answers[current_idx] = {
                            'user_answer': user_answer,
                            'correct': is_correct
                        }

                        # Track progress
                        try:
                            st.session_state.progress_tracker.record_attempt(
                                subject, topic, question['question'], is_correct
                            )
                        except Exception as e:
                            st.error(f"Error recording attempt: {e}")

                        if is_correct:
                            st.success("✓ Correct!")
                        else:
                            st.error(f"✗ Incorrect. Correct answer: {question['answer']}")

                with col2:
                    if st.button("💡 Teach Me"):
                        st.session_state.show_explanation = True
                        st.rerun()

                with col3:
                    if st.button("⏭️ Next Question"):
                        st.session_state.current_question_index += 1
                        st.session_state.show_explanation = False
                        st.rerun()

            # Show explanation if requested
            if st.session_state.show_explanation:
                with st.expander("📚 Explanation", expanded=True):
                    with st.spinner("Generating explanation..."):
                        try:
                            # Get context
                            context = st.session_state.retriever.vector_search(
                                question['question'], subject=subject, topic=topic, top_k=3
                            )

                            explanation = st.session_state.answer_gen.generate_explanation(
                                question['question'],
                                question.get('answer', 'N/A'),
                                subject,
                                topic,
                                context
                            )
                            st.markdown(explanation)
                        except Exception as e:
                            st.error(f"Error generating explanation: {e}")
        else:
            # Completed all questions
            st.success("🎉 Congratulations! You've completed all questions for this topic.")

            # Show summary
            correct_count = sum(1 for ans in st.session_state.user_answers.values() if ans['correct'])
            total_count = len(st.session_state.user_answers)
            accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Questions Attempted", total_count)
            with col2:
                st.metric("Correct Answers", correct_count)
            with col3:
                st.metric("Accuracy", f"{accuracy:.1f}%")

            if st.button("🔄 Restart", type="primary"):
                reset_session()
                st.rerun()


# Teach Mode
def teach_mode(subject: str, topic: str):
    """Teach mode: AI explains concepts"""
    st.header(f"🧑‍🏫 Teach: {subject} - {topic}")

    # Get topic information
    try:
        topic_info = st.session_state.retriever.graph_search(subject, topic)
    except Exception as e:
        st.error(f"Error loading topic info: {e}")
        topic_info = {}

    # Display topic description
    st.markdown(f"""
    ### {topic}
    {topic_info.get('description', 'No description available.')}
    """)

    difficulty = topic_info.get('difficulty', 1)
    st.markdown(f"**Difficulty Level:** {'⭐' * difficulty}")

    st.markdown("---")

    # User query
    user_query = st.text_input(
        "What would you like to learn about this topic?",
        placeholder="E.g., Explain process synchronization with examples"
    )

    if st.button("🔍 Get Explanation", type="primary"):
        if user_query:
            with st.spinner("Generating explanation..."):
                try:
                    # Retrieve relevant context
                    context = st.session_state.retriever.hybrid_search(
                        user_query, subject, topic, top_k=5
                    )

                    # Generate explanation
                    explanation = st.session_state.answer_gen.teach(
                        query=user_query,
                        subject=subject,
                        topic=topic,
                        context=context
                    )

                    # Display explanation
                    st.markdown("### Explanation")
                    st.markdown(explanation)

                except Exception as e:
                    st.error(f"Error generating explanation: {e}")
        else:
            st.warning("Please enter a question or topic to learn about.")


# Practice Mode
def practice_mode(subject: str, topic: str):
    """Practice mode: Generate AI questions"""
    st.header(f"✍️ Practice: {subject} - {topic}")

    st.markdown("Practice with AI-generated questions similar to GATE.")

    # Settings
    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.slider("Number of questions", 1, 10, 5)
    with col2:
        difficulty = st.select_slider(
            "Difficulty level",
            options=[1, 2, 3, 4, 5],
            value=2,
            format_func=lambda x: '⭐' * x
        )

    if st.button("🎲 Generate Questions", type="primary"):
        with st.spinner("Generating questions..."):
            try:
                # Get example questions
                pyqs = st.session_state.retriever.get_questions_by_topic(
                    subject, topic, limit=5
                )

                # Generate new questions
                generated_questions = st.session_state.answer_gen.generate_practice_questions(
                    subject=subject,
                    topic=topic,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    example_questions=pyqs
                )

                st.session_state.practice_questions = generated_questions

            except Exception as e:
                st.error(f"Error generating questions: {e}")

    # Display generated questions
    if 'practice_questions' in st.session_state and st.session_state.practice_questions:
        for idx, q in enumerate(st.session_state.practice_questions, 1):
            with st.expander(f"Question {idx}", expanded=True):
                st.markdown(f"**{q.get('question', 'No question text')}**")

                if q.get('options'):
                    user_answer = st.radio(
                        "Select answer:",
                        q['options'],
                        key=f"practice_{idx}"
                    )

                    if st.button(f"Check Answer", key=f"check_{idx}"):
                        if user_answer == q.get('answer'):
                            st.success("✓ Correct!")
                        else:
                            st.error(f"✗ Incorrect. Correct answer: {q.get('answer', 'N/A')}")

                        if q.get('explanation'):
                            st.markdown("**Explanation:**")
                            st.markdown(q['explanation'])


# Read Mode
def read_mode(subject: str, topic: str):
    """Read mode: Build reading material"""
    st.header(f"📚 Read: {subject} - {topic}")

    with st.spinner("Building reading material..."):
        try:
            # Get relevant chunks
            chunks = st.session_state.retriever.vector_search(
                query=f"comprehensive explanation of {topic}",
                subject=subject,
                topic=topic,
                top_k=10
            )

            if not chunks:
                st.warning("No reading material available for this topic.")
                st.info("Material will be available after loading textbook data.")
                return

            # Generate structured reading material
            reading_material = st.session_state.answer_gen.build_reading_material(
                subject=subject,
                topic=topic,
                chunks=chunks
            )

            # Display reading material
            st.markdown(reading_material)

            # Download option
            st.download_button(
                label="📥 Download as Text",
                data=reading_material,
                file_name=f"{subject}_{topic}_reading_material.txt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Error building reading material: {e}")


# Flashcard Mode
def flashcard_mode(subject: str, topic: str):
    """Flashcard mode: Spaced repetition"""
    st.header(f"🃏 Flashcards: {subject} - {topic}")

    # Get due flashcards
    try:
        due_cards = st.session_state.sr_manager.get_due_cards(subject, topic)
    except Exception as e:
        st.error(f"Error loading flashcards: {e}")
        due_cards = []

    if not due_cards:
        st.info("No flashcards due for review right now!")

        if st.button("📝 Create New Flashcards"):
            with st.spinner("Generating flashcards..."):
                try:
                    flashcards = st.session_state.answer_gen.generate_flashcards(
                        subject, topic, num_cards=10
                    )
                    st.session_state.sr_manager.add_cards(flashcards)
                    st.success(f"Created {len(flashcards)} new flashcards!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating flashcards: {e}")
        return

    # Display flashcard
    if 'current_card_idx' not in st.session_state:
        st.session_state.current_card_idx = 0

    card_idx = st.session_state.current_card_idx

    if card_idx < len(due_cards):
        card = due_cards[card_idx]

        # Progress
        st.progress((card_idx + 1) / len(due_cards),
                    text=f"Card {card_idx + 1} of {len(due_cards)}")

        # Show question side
        st.markdown(f"""
        <div class="question-card">
            <h3>Question</h3>
            <p style="font-size: 1.2rem;">{card['front']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Flip button
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = False

        if st.button("🔄 Flip Card", type="primary", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()

        # Show answer if flipped
        if st.session_state.show_answer:
            st.markdown(f"""
            <div class="question-card" style="background-color: #e8f4f8;">
                <h3>Answer</h3>
                <p style="font-size: 1.1rem;">{card['back']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Rating buttons
            st.markdown("### How well did you remember?")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("😟 Again", use_container_width=True):
                    rate_card(card, 1)
            with col2:
                if st.button("😐 Hard", use_container_width=True):
                    rate_card(card, 2)
            with col3:
                if st.button("🙂 Good", use_container_width=True):
                    rate_card(card, 3)
            with col4:
                if st.button("😄 Easy", use_container_width=True):
                    rate_card(card, 4)
    else:
        st.success("🎉 You've reviewed all due flashcards!")
        if st.button("🔄 Reset"):
            st.session_state.current_card_idx = 0
            st.session_state.show_answer = False
            st.rerun()


def rate_card(card, rating):
    """Rate flashcard and update schedule"""
    try:
        st.session_state.sr_manager.review_card(card['id'], rating)
        st.session_state.current_card_idx += 1
        st.session_state.show_answer = False
        st.rerun()
    except Exception as e:
        st.error(f"Error rating card: {e}")


# Welcome Screen
def show_welcome_screen():
    """Show welcome screen"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>Welcome to your GATE CS 2026 Preparation System! 🎓</h2>
        <p style="font-size: 1.2rem; color: #666;">
            Select a subject, topic, and action from the sidebar to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 📖 Learn
        Practice questions with increasing difficulty.
        Get explanations when needed.
        """)

    with col2:
        st.markdown("""
        ### 🧑‍🏫 Teach
        Get AI-powered explanations.
        Deep dive into concepts.
        """)

    with col3:
        st.markdown("""
        ### ✍️ Practice
        Generate GATE-level questions.
        Test your knowledge.
        """)


# Run the app
if __name__ == "__main__":
    main()
