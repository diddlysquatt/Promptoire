"""
Search service for Promptoire with debounced search and caching capabilities.
Provides high-performance prompt searching with fuzzy matching and category filtering.
"""

import time
import threading
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from difflib import SequenceMatcher
import re


@dataclass
class SearchResult:
    """Represents a single search result"""
    prompt: Dict
    category_path: str
    score: float
    matched_fields: List[str]


@dataclass
class SearchStats:
    """Search performance statistics"""
    total_prompts: int
    matching_prompts: int
    categories_searched: int
    search_time_ms: float


class Debouncer:
    """Utility class for debouncing function calls"""

    def __init__(self, delay_ms: int = 300):
        self.delay_ms = delay_ms
        self.timer = None
        self.callback = None
        self.args = ()
        self.kwargs = {}

    def debounce(self, callback: Callable, *args, **kwargs) -> None:
        """Debounce a function call"""
        if self.timer:
            self.timer.cancel()

        self.callback = callback
        self.args = args
        self.kwargs = kwargs

        self.timer = threading.Timer(self.delay_ms / 1000.0, self._execute)
        self.timer.start()

    def _execute(self) -> None:
        """Execute the debounced callback"""
        if self.callback:
            self.callback(*self.args, **self.kwargs)

    def cancel(self) -> None:
        """Cancel any pending debounced call"""
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def flush(self) -> None:
        """Immediately execute any pending debounced call"""
        if self.timer:
            self.timer.cancel()
            self._execute()
            self.timer = None


class SearchService:
    """High-performance search service with debouncing and caching"""

    def __init__(self, cache_service=None, fuzzy_threshold: float = 0.6, search_delay_ms: int = 300, enable_fuzzy: bool = False):
        self.cache_service = cache_service
        self.fuzzy_threshold = fuzzy_threshold
        self.enable_fuzzy = enable_fuzzy
        self.search_delay_ms = search_delay_ms
        self.debouncer = Debouncer(search_delay_ms)
        self._search_index = {}
        self._index_built = False

        # Performance tracking
        self._last_search_stats = None
        self._search_history = []

    def build_search_index(self, prompts_data: Dict) -> None:
        """Build an optimized search index for faster lookups"""
        start_time = time.time()
        self._search_index = {}
        word_index = {}

        def index_category(category_name: str, category_data: Dict, path: str = ""):
            """Recursively index all prompts in a category"""
            current_path = f"{path}/{category_name}" if path else category_name

            # Index direct prompts
            if "prompts" in category_data:
                for i, prompt in enumerate(category_data["prompts"]):
                    prompt_id = f"{current_path}:{i}"
                    searchable_text = self._create_searchable_text(prompt)
                    self._search_index[prompt_id] = {
                        'prompt': prompt,
                        'category_path': current_path,
                        'searchable_text': searchable_text,
                        'title': prompt.get('title', '').lower(),
                        'tags': [t.lower() for t in prompt.get('tags', []) if isinstance(t, str)]
                    }

                    # Build word index for fast single-word searches
                    words = searchable_text.lower().split()
                    title_words = prompt.get('title', '').lower().split()
                    tag_words = [t.lower() for t in prompt.get('tags', []) if isinstance(t, str)]

                    for word in set(words + title_words + tag_words):
                        if word not in word_index:
                            word_index[word] = []
                        word_index[word].append(prompt_id)

            # Index subcategories
            if "subcategories" in category_data:
                for sub_name, sub_data in category_data["subcategories"].items():
                    index_category(sub_name, sub_data, current_path)

        # Start indexing from root categories
        if "categories" in prompts_data:
            for category_name, category_data in prompts_data["categories"].items():
                index_category(category_name, category_data)

        # Add word index to search index
        self._search_index['_word_index'] = word_index

        self._index_built = True
        build_time = (time.time() - start_time) * 1000
        print(f"Search index built in {build_time:.2f}ms with {len(self._search_index)-1} prompts")

    def _create_searchable_text(self, prompt: Dict) -> str:
        """Create normalized searchable text from a prompt"""
        title = prompt.get('title', '').lower()
        content = prompt.get('prompt', '').lower()
        tags = ' '.join(prompt.get('tags', [])).lower() if isinstance(prompt.get('tags'), list) else ''

        # Combine all searchable fields
        return f"{title} {content} {tags}"

    def _text_matches(self, hay: str, needle: str) -> Tuple[bool, float]:
        """Check if text matches search query with optional fuzzy matching"""
        if not needle:
            return True, 1.0

        hay_lower = hay.lower()
        needle_lower = needle.lower()

        # Exact match gets highest score
        if needle_lower in hay_lower:
            return True, 1.0

        # Fuzzy matching only if enabled (disabled by default for performance)
        if self.enable_fuzzy:
            ratio = SequenceMatcher(None, hay_lower, needle_lower).ratio()
            matches = ratio >= self.fuzzy_threshold
            return matches, ratio

        return False, 0.0

    def _search_single_query(self, query: str, category_filter: Optional[str] = None) -> List[SearchResult]:
        """Perform search for a single query with optimized matching"""
        if not self._index_built:
            return []

        results = []
        query_terms = query.strip().split()
        query_lower = query.lower()

        # Optimization: if single word and no category filter, use faster approach
        if len(query_terms) == 1 and not category_filter:
            term = query_terms[0].lower()
            if term in self._search_index.get('_word_index', {}):
                # Use pre-built word index for faster single-word searches
                matching_ids = self._search_index['_word_index'][term]
                for prompt_id in matching_ids:
                    if prompt_id in self._search_index:
                        prompt_data = self._search_index[prompt_id]
                        # Calculate score
                        title_score = 2.0 if term in prompt_data['title'] else 1.0
                        if any(term in tag for tag in prompt_data['tags']):
                            title_score = 2.5

                        results.append(SearchResult(
                            prompt=prompt_data['prompt'],
                            category_path=prompt_data['category_path'],
                            score=min(title_score, 1.0),
                            matched_fields=['title'] if term in prompt_data['title'] else ['content']
                        ))
                return results

        # Standard search for multi-word queries or when category filter is applied
        for prompt_id, prompt_data in self._search_index.items():
            # Skip index metadata
            if prompt_id.startswith('_'):
                continue

            # Apply category filter if specified
            if category_filter and not prompt_data['category_path'].startswith(category_filter):
                continue

            searchable_text = prompt_data['searchable_text']
            title = prompt_data['title']
            tags = prompt_data['tags']

            # Quick check first - does any term match?
            quick_match = False
            for term in query_terms:
                term_lower = term.lower()
                if term_lower in title or term_lower in searchable_text:
                    quick_match = True
                    break
                elif any(term_lower in tag for tag in tags):
                    quick_match = True
                    break

            if not quick_match:
                continue

            # Calculate match score (optimized)
            total_score = 0
            matched_fields = []

            for term in query_terms:
                term_lower = term.lower()

                # Fast exact match first
                if term_lower in title:
                    total_score += 2.0
                    if 'title' not in matched_fields:
                        matched_fields.append('title')
                elif term_lower in searchable_text:
                    total_score += 1.0
                    if 'content' not in matched_fields:
                        matched_fields.append('content')

                # Tag matches
                for tag in tags:
                    if term_lower in tag:
                        total_score += 1.5
                        if 'tags' not in matched_fields:
                            matched_fields.append('tags')
                        break

            # Only include results that match at least one term
            if total_score > 0:
                # Normalize score by number of terms
                avg_score = total_score / len(query_terms)
                results.append(SearchResult(
                    prompt=prompt_data['prompt'],
                    category_path=prompt_data['category_path'],
                    score=min(avg_score, 1.0),  # Cap at 1.0
                    matched_fields=matched_fields
                ))

        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def search(self, query: str, callback: Callable[[List[SearchResult], SearchStats], None],
               category_filter: Optional[str] = None, use_cache: bool = True) -> None:
        """
        Perform debounced search with optional caching

        Args:
            query: Search query string
            callback: Function to call with search results
            category_filter: Optional category path to filter results
            use_cache: Whether to use cached results if available
        """
        # Cancel any pending search
        self.debouncer.cancel()

        # Create the search function to be debounced
        def perform_search():
            start_time = time.time()

            # Check cache first
            cache_key = f"search:{query}:{category_filter or ''}" if use_cache else None
            if cache_key and self.cache_service:
                cached_results = self.cache_service.get(cache_key)
                if cached_results:
                    search_time = (time.time() - start_time) * 1000
                    stats = SearchStats(
                        total_prompts=len(self._search_index),
                        matching_prompts=len(cached_results),
                        categories_searched=len(set(r.category_path for r in cached_results)),
                        search_time_ms=search_time
                    )
                    callback(cached_results, stats)
                    return

            # Perform actual search
            results = self._search_single_query(query, category_filter)

            # Cache results
            if cache_key and self.cache_service:
                self.cache_service.set(cache_key, results, ttl=300)  # 5 minutes TTL

            # Calculate statistics
            search_time = (time.time() - start_time) * 1000
            stats = SearchStats(
                total_prompts=len(self._search_index),
                matching_prompts=len(results),
                categories_searched=len(set(r.category_path for r in results)),
                search_time_ms=search_time
            )

            self._last_search_stats = stats
            self._search_history.append({
                'query': query,
                'timestamp': time.time(),
                'stats': stats
            })

            # Keep history limited to last 100 searches
            if len(self._search_history) > 100:
                self._search_history.pop(0)

            callback(results, stats)

        # Debounce the search
        self.debouncer.debounce(perform_search)

    def search_immediate(self, query: str, category_filter: Optional[str] = None) -> Tuple[List[SearchResult], SearchStats]:
        """
        Perform immediate search without debouncing

        Returns:
            Tuple of (results, stats)
        """
        start_time = time.time()
        results = self._search_single_query(query, category_filter)
        search_time = (time.time() - start_time) * 1000

        stats = SearchStats(
            total_prompts=len(self._search_index),
            matching_prompts=len(results),
            categories_searched=len(set(r.category_path for r in results)),
            search_time_ms=search_time
        )

        return results, stats

    def get_categories_for_query(self, query: str) -> List[str]:
        """Get list of categories that contain matching prompts for a query"""
        results, _ = self.search_immediate(query)
        return sorted(set(result.category_path for result in results))

    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query"""
        if len(partial_query) < 2:
            return []

        suggestions = set()
        partial_lower = partial_query.lower()

        # Extract suggestions from prompt titles and tags
        for prompt_data in self._search_index.values():
            title = prompt_data['title']
            tags = prompt_data['tags']

            # Check title for partial matches
            if partial_lower in title:
                words = title.split()
                for word in words:
                    if partial_lower in word and len(word) > len(partial_query):
                        suggestions.add(word)

            # Check tags
            for tag in tags:
                if partial_lower in tag and len(tag) > len(partial_query):
                    suggestions.add(tag)

        return sorted(list(suggestions))[:limit]

    def clear_search_history(self) -> None:
        """Clear search history"""
        self._search_history.clear()

    def get_search_stats(self) -> Dict:
        """Get search performance statistics"""
        if not self._search_history:
            return {}

        recent_searches = self._search_history[-10:]  # Last 10 searches
        avg_time = sum(s['stats'].search_time_ms for s in recent_searches) / len(recent_searches)

        return {
            'total_searches': len(self._search_history),
            'average_search_time_ms': avg_time,
            'last_search_stats': self._last_search_stats.__dict__ if self._last_search_stats else None,
            'indexed_prompts': len(self._search_index),
            'index_built': self._index_built
        }

    def destroy(self) -> None:
        """Clean up resources"""
        self.debouncer.cancel()
        self._search_index.clear()
        self._search_history.clear()
        self._index_built = False