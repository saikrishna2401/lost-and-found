"""
Smart Matching Service Module.
Provides rule-based matching between Lost and Found submissions based on Title, Category, and Location.
Designed modularly so AI image embeddings or NLP similarity can be plugged in easily.
"""
import re
from models.item import Item

class MatchingService:

    @staticmethod
    def _extract_keywords(text):
        """Extracts clean lowercase alphanumeric keywords from text."""
        if not text:
            return set()
        words = re.findall(r'\b\w{3,}\b', text.lower())
        # Filter out common stop words
        stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'lost', 'found', 'near'}
        return {w for w in words if w not in stopwords}

    @staticmethod
    def find_potential_matches(target_item):
        """
        Finds matching items of opposite type ('lost' vs 'found') that share:
        1. Same category
        2. Location similarity or title/description keyword overlap.
        """
        opposite_type = 'found' if target_item.item_type == 'lost' else 'lost'

        # Query non-deleted candidate items of opposite type
        candidates = Item.query.filter(
            Item.item_type == opposite_type,
            Item.is_deleted == False,
            Item.status.in_([Item.STATUS_APPROVED, Item.STATUS_PENDING, Item.STATUS_UNDER_REVIEW]),
            Item.id != target_item.id
        ).all()

        matches = []
        target_title_words = MatchingService._extract_keywords(target_item.title)
        target_location = target_item.location.lower().strip()

        for candidate in candidates:
            # Rule 1: Must be in same category
            if candidate.category_id != target_item.category_id:
                continue

            score = 0
            candidate_title_words = MatchingService._extract_keywords(candidate.title)
            candidate_location = candidate.location.lower().strip()

            # Rule 2: Title keyword match
            shared_title_words = target_title_words.intersection(candidate_title_words)
            if shared_title_words:
                score += len(shared_title_words) * 2

            # Rule 3: Location match
            if target_location in candidate_location or candidate_location in target_location:
                score += 3

            if score > 0:
                matches.append((candidate, score))

        # Sort matches by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches[:5]] # Top 5 potential matches
