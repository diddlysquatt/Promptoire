"""
Performance test script for the SearchService.
Tests search response times to verify they meet the <100ms requirement.
"""

import time
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_data(num_prompts=1000):
    """Create test prompts data for performance testing"""
    categories = {}

    # Create various categories
    category_names = [
        "Development", "Writing", "Analysis", "Creative", "Business",
        "Education", "Research", "Marketing", "Productivity", "Communication"
    ]

    for cat_name in category_names:
        prompts = []
        for i in range(num_prompts // len(category_names)):
            prompt = {
                "title": f"{cat_name} Prompt {i+1}",
                "prompt": f"This is a test prompt for {cat_name} category with content {i+1}. " +
                         f"It contains various keywords like development, analysis, creative, " +
                         f"business, education, research, marketing, productivity, communication.",
                "tags": [cat_name.lower(), "test", f"keyword{i%10}", "sample"],
                "id": f"{cat_name.lower()}_{i+1}"
            }
            prompts.append(prompt)

        categories[cat_name] = {
            "prompts": prompts,
            "subcategories": {}
        }

    return {"categories": categories}

def test_search_performance():
    """Test search service performance"""
    print("=== SearchService Performance Test ===")

    try:
        from services.SearchService import SearchService
        from utils.cache import get_cache
    except ImportError as e:
        print(f"Failed to import services: {e}")
        return False

    # Create test data
    print("Creating test data...")
    test_data = create_test_data(1000)  # 1000 prompts

    # Initialize services
    print("Initializing services...")
    cache_service = get_cache("memory", max_size=100)
    search_service = SearchService(
        cache_service=cache_service,
        fuzzy_threshold=0.6,
        search_delay_ms=0  # No delay for testing
    )

    # Build search index
    print("Building search index...")
    start_time = time.time()
    search_service.build_search_index(test_data)
    index_time = (time.time() - start_time) * 1000
    print(f"Search index built in {index_time:.2f}ms")

    # Test queries
    test_queries = [
        "development",  # Single word
        "creative writing",  # Multi-word
        "business analysis",  # Two categories
        "keyword5",  # Tag search
        "prompt 42",  # Number search
        "nonexistent",  # No results
        "",  # Empty query
    ]

    print("\n=== Search Performance Tests ===")
    all_passed = True

    for query in test_queries:
        print(f"\nTesting query: '{query}'")

        # Test immediate search
        start_time = time.time()
        results, stats = search_service.search_immediate(query)
        search_time = (time.time() - start_time) * 1000

        print(f"  Results: {len(results)}")
        print(f"  Search time: {search_time:.2f}ms")
        print(f"  Categories searched: {stats.categories_searched}")

        # Check if under 100ms
        if search_time < 100:
            print(f"  [PASS] Under 100ms")
        else:
            print(f"  [FAIL] Over 100ms ({search_time:.2f}ms)")
            all_passed = False

        # Test cached search (second time)
        start_time = time.time()
        results2, stats2 = search_service.search_immediate(query)
        cached_time = (time.time() - start_time) * 1000

        print(f"  Cached search time: {cached_time:.2f}ms")

        # Cache should be faster
        if cached_time < search_time:
            print(f"  [OK] Cache working: {cached_time:.2f}ms vs {search_time:.2f}ms")
        else:
            print(f"  [WARN] Cache may not be working optimally")

    # Test debounced search
    print("\n=== Debounced Search Test ===")
    callback_results = []

    def test_callback(results, stats):
        callback_results.append((results, stats))

    start_time = time.time()
    search_service.search("test query", test_callback)

    # Wait for callback
    timeout = time.time() + 1.0  # 1 second timeout
    while not callback_results and time.time() < timeout:
        time.sleep(0.01)

    if callback_results:
        results, stats = callback_results[0]
        debounce_time = (time.time() - start_time) * 1000
        print(f"Debounced search completed in {debounce_time:.2f}ms")
        print(f"Results: {len(results)}")

        if debounce_time < 100:
            print(f"  [PASS] Debounced search under 100ms")
        else:
            print(f"  [FAIL] Debounced search over 100ms")
            all_passed = False
    else:
        print("  [FAIL] Debounced search timeout")
        all_passed = False

    # Get search statistics
    stats = search_service.get_search_stats()
    print(f"\n=== Search Statistics ===")
    print(f"Total searches: {stats['total_searches']}")
    print(f"Average search time: {stats['average_search_time_ms']:.2f}ms")
    print(f"Indexed prompts: {stats['indexed_prompts']}")

    # Cleanup
    search_service.destroy()
    cache_service.clear()

    print(f"\n=== Final Result ===")
    if all_passed:
        print("[SUCCESS] All performance tests PASSED!")
        print("Search service meets <100ms response time requirement")
    else:
        print("[FAILURE] Some performance tests FAILED!")
        print("Search service does not meet <100ms response time requirement")

    return all_passed

if __name__ == "__main__":
    success = test_search_performance()
    sys.exit(0 if success else 1)