"""
Spaced repetition system using FSRS algorithm
"""

from typing import List, Dict
from datetime import datetime, timedelta
from fsrs import FSRS, Card, Rating, ReviewLog
import json
from pathlib import Path


class SpacedRepetitionManager:
    """Manage flashcards with spaced repetition"""

    def __init__(self, storage_file: str = "data/processed/flashcards.json"):
        """
        Initialize spaced repetition manager

        Args:
            storage_file: File to store flashcard data
        """
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        self.fsrs = FSRS()
        self.cards = self._load_cards()

    def _load_cards(self) -> Dict[str, Dict]:
        """Load flashcards from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading flashcards: {e}")
                return {}
        return {}

    def _save_cards(self):
        """Save flashcards to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.cards, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving flashcards: {e}")

    def add_cards(self, flashcards: List[Dict]):
        """
        Add new flashcards

        Args:
            flashcards: List of flashcard dictionaries with keys:
                - id: Unique identifier
                - subject: Subject name
                - topic: Topic name
                - front: Question side
                - back: Answer side
        """
        for card in flashcards:
            card_id = card['id']

            if card_id not in self.cards:
                # Create new FSRS card
                fsrs_card = Card()

                self.cards[card_id] = {
                    'id': card_id,
                    'subject': card['subject'],
                    'topic': card['topic'],
                    'front': card['front'],
                    'back': card['back'],
                    'fsrs_state': {
                        'due': datetime.now().isoformat(),
                        'stability': fsrs_card.stability,
                        'difficulty': fsrs_card.difficulty,
                        'elapsed_days': fsrs_card.elapsed_days,
                        'scheduled_days': fsrs_card.scheduled_days,
                        'reps': fsrs_card.reps,
                        'lapses': fsrs_card.lapses,
                        'state': fsrs_card.state.value,
                        'last_review': fsrs_card.last_review.isoformat() if fsrs_card.last_review else None
                    },
                    'created_at': datetime.now().isoformat()
                }

        self._save_cards()
        print(f"✅ Added {len(flashcards)} flashcards")

    def get_due_cards(self, subject: str = None,
                      topic: str = None) -> List[Dict]:
        """
        Get flashcards due for review

        Args:
            subject: Optional subject filter
            topic: Optional topic filter

        Returns:
            List of due flashcards
        """
        now = datetime.now()
        due_cards = []

        for card_id, card in self.cards.items():
            # Apply filters
            if subject and card['subject'] != subject:
                continue
            if topic and card['topic'] != topic:
                continue

            # Check if due
            due_date = datetime.fromisoformat(card['fsrs_state']['due'])
            if due_date <= now:
                due_cards.append(card)

        # Sort by due date (most overdue first)
        due_cards.sort(key=lambda x: datetime.fromisoformat(x['fsrs_state']['due']))

        return due_cards

    def review_card(self, card_id: str, rating: int):
        """
        Review a flashcard

        Args:
            card_id: Flashcard ID
            rating: User rating (1=Again, 2=Hard, 3=Good, 4=Easy)
        """
        if card_id not in self.cards:
            print(f"Card not found: {card_id}")
            return

        card_data = self.cards[card_id]
        fsrs_state = card_data['fsrs_state']

        # Reconstruct FSRS Card object
        fsrs_card = Card()
        fsrs_card.stability = fsrs_state['stability']
        fsrs_card.difficulty = fsrs_state['difficulty']
        fsrs_card.elapsed_days = fsrs_state['elapsed_days']
        fsrs_card.scheduled_days = fsrs_state['scheduled_days']
        fsrs_card.reps = fsrs_state['reps']
        fsrs_card.lapses = fsrs_state['lapses']
        fsrs_card.state = fsrs_state['state']
        if fsrs_state['last_review']:
            fsrs_card.last_review = datetime.fromisoformat(fsrs_state['last_review'])

        # Map rating to FSRS Rating
        rating_map = {
            1: Rating.Again,
            2: Rating.Hard,
            3: Rating.Good,
            4: Rating.Easy
        }

        fsrs_rating = rating_map.get(rating, Rating.Good)

        # Schedule next review
        scheduling_cards = self.fsrs.repeat(fsrs_card, datetime.now())
        updated_card = scheduling_cards[fsrs_rating].card

        # Update stored card
        card_data['fsrs_state'] = {
            'due': updated_card.due.isoformat(),
            'stability': updated_card.stability,
            'difficulty': updated_card.difficulty,
            'elapsed_days': updated_card.elapsed_days,
            'scheduled_days': updated_card.scheduled_days,
            'reps': updated_card.reps,
            'lapses': updated_card.lapses,
            'state': updated_card.state.value,
            'last_review': updated_card.last_review.isoformat() if updated_card.last_review else None
        }
        card_data['last_reviewed'] = datetime.now().isoformat()

        self._save_cards()

    def get_stats(self, subject: str = None) -> Dict:
        """
        Get flashcard statistics

        Args:
            subject: Optional subject filter

        Returns:
            Statistics dictionary
        """
        total = 0
        due = 0
        learned = 0

        now = datetime.now()

        for card in self.cards.values():
            if subject and card['subject'] != subject:
                continue

            total += 1

            if datetime.fromisoformat(card['fsrs_state']['due']) <= now:
                due += 1

            if card['fsrs_state']['reps'] >= 3:
                learned += 1

        return {
            'total': total,
            'due': due,
            'learned': learned,
            'retention_rate': (learned / total * 100) if total > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    manager = SpacedRepetitionManager()

    # Add sample flashcards
    sample_cards = [
        {
            'id': 'os_process_1',
            'subject': 'Operating Systems',
            'topic': 'Process Management',
            'front': 'What is a process?',
            'back': 'A program in execution with its own address space and resources.'
        },
        {
            'id': 'os_process_2',
            'subject': 'Operating Systems',
            'topic': 'Process Management',
            'front': 'What is the difference between process and thread?',
            'back': 'Process has its own address space; threads share the same address space.'
        }
    ]

    manager.add_cards(sample_cards)

    # Get due cards
    due = manager.get_due_cards(subject='Operating Systems')
    print(f"\nDue flashcards: {len(due)}")

    # Get stats
    stats = manager.get_stats()
    print(f"\nFlashcard Stats:")
    print(f"  Total: {stats['total']}")
    print(f"  Due: {stats['due']}")
    print(f"  Learned: {stats['learned']}")
