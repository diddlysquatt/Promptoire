"""
UI Performance Optimizer
Manages UI performance optimizations and metrics
"""

import time
import threading
from typing import Dict, List, Any, Callable, Optional
from collections import deque
import tkinter as tk


class PerformanceMetrics:
    """Track performance metrics for UI operations"""

    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.metrics = {
            'render_times': deque(maxlen=max_samples),
            'filter_times': deque(maxlen=max_samples),
            'scroll_times': deque(maxlen=max_samples),
            'widget_counts': deque(maxlen=max_samples),
            'memory_usage': deque(maxlen=max_samples)
        }
        self.operation_counts = {
            'renders': 0,
            'filters': 0,
            'scrolls': 0,
            'optimizations': 0
        }

    def record_render(self, duration: float, widget_count: int):
        """Record a render operation"""
        self.metrics['render_times'].append(duration)
        self.metrics['widget_counts'].append(widget_count)
        self.operation_counts['renders'] += 1

    def record_filter(self, duration: float, item_count: int):
        """Record a filter operation"""
        self.metrics['filter_times'].append(duration)
        self.operation_counts['filters'] += 1

    def record_scroll(self, duration: float):
        """Record a scroll operation"""
        self.metrics['scroll_times'].append(duration)
        self.operation_counts['scrolls'] += 1

    def get_average_render_time(self) -> float:
        """Get average render time"""
        times = list(self.metrics['render_times'])
        return sum(times) / len(times) if times else 0

    def get_average_filter_time(self) -> float:
        """Get average filter time"""
        times = list(self.metrics['filter_times'])
        return sum(times) / len(times) if times else 0

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'avg_render_time': self.get_average_render_time(),
            'avg_filter_time': self.get_average_filter_time(),
            'total_operations': dict(self.operation_counts),
            'recent_widget_counts': list(self.metrics['widget_counts'])[-10:],
            'render_samples': len(self.metrics['render_times']),
            'filter_samples': len(self.metrics['filter_times'])
        }


class Debouncer:
    """Utility for debouncing function calls"""

    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self.timers = {}
        self.lock = threading.Lock()

    def debounce(self, key: str, func: Callable, *args, **kwargs):
        """Debounce a function call with a specific key"""
        with self.lock:
            # Cancel existing timer for this key
            if key in self.timers:
                self.timers[key].cancel()

            # Create new timer
            timer = threading.Timer(self.delay, func, args, kwargs)
            self.timers[key] = timer
            timer.start()

    def cancel(self, key: str):
        """Cancel a debounced call"""
        with self.lock:
            if key in self.timers:
                self.timers[key].cancel()
                del self.timers[key]

    def cancel_all(self):
        """Cancel all debounced calls"""
        with self.lock:
            for timer in self.timers.values():
                timer.cancel()
            self.timers.clear()


class UIOptimizer:
    """
    Main UI optimization manager
    Provides performance optimization utilities and metrics
    """

    def __init__(self, performance_threshold: float = 0.1):
        self.performance_threshold = performance_threshold
        self.metrics = PerformanceMetrics()
        self.debouncer = Debouncer(delay=0.05)

        # Optimization settings
        self.settings = {
            'virtual_scrolling_enabled': True,
            'lazy_loading_enabled': True,
            'debounce_delay': 0.05,
            'batch_size': 20,
            'cache_enabled': True,
            'throttle_updates': True
        }

        # Cache for expensive operations
        self.cache = {}
        self.cache_lock = threading.Lock()

        # Performance monitoring
        self.monitoring_enabled = True
        self.slow_operations = []

    def optimize_render_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute and optimize a render operation"""
        start_time = time.time()

        # Execute the operation
        result = operation(*args, **kwargs)

        # Record metrics
        duration = time.time() - start_time
        widget_count = kwargs.get('widget_count', 0)
        self.metrics.record_render(duration, widget_count)

        # Track slow operations
        if duration > self.performance_threshold:
            self.slow_operations.append({
                'operation': operation.__name__,
                'duration': duration,
                'timestamp': time.time(),
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            })

        return result

    def debounce_filter(self, filter_func: Callable, filter_text: str, data: List[Any]):
        """Debounce filter operations to improve performance"""
        key = f"filter_{hash(filter_text)}"

        def execute_filter():
            start_time = time.time()
            result = filter_func(filter_text, data)
            duration = time.time() - start_time
            self.metrics.record_filter(duration, len(data))
            return result

        self.debouncer.debounce(key, execute_filter)

    def cache_result(self, key: str, operation: Callable, *args, **kwargs) -> Any:
        """Cache expensive operation results"""
        with self.cache_lock:
            if key in self.cache and self.settings['cache_enabled']:
                return self.cache[key]

            # Execute operation
            result = operation(*args, **kwargs)

            # Cache result
            if self.settings['cache_enabled']:
                self.cache[key] = result

                # Limit cache size
                if len(self.cache) > 1000:
                    # Remove oldest entries
                    keys_to_remove = list(self.cache.keys())[:500]
                    for k in keys_to_remove:
                        del self.cache[k]

            return result

    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        with self.cache_lock:
            if pattern:
                keys_to_remove = [k for k in self.cache.keys() if pattern in k]
                for k in keys_to_remove:
                    del self.cache[k]
            else:
                self.cache.clear()

    def batch_process(self, items: List[Any], processor: Callable, batch_size: int = None) -> List[Any]:
        """Process items in batches to improve performance"""
        batch_size = batch_size or self.settings['batch_size']
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = processor(batch)
            results.extend(batch_results)

            # Allow UI to remain responsive
            if i + batch_size < len(items):
                tk._default_root.update()

        return results

    def throttle_update(self, update_func: Callable, throttle_key: str = "default"):
        """Throttle UI updates to improve performance"""
        current_time = time.time()

        if not hasattr(self, '_last_update_times'):
            self._last_update_times = {}

        if throttle_key not in self._last_update_times:
            self._last_update_times[throttle_key] = 0

        # Only update if enough time has passed
        if current_time - self._last_update_times[throttle_key] > 0.016:  # ~60 FPS
            self._last_update_times[throttle_key] = current_time
            update_func()

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        summary = self.metrics.get_performance_summary()

        return {
            'performance_metrics': summary,
            'slow_operations_count': len(self.slow_operations),
            'recent_slow_operations': self.slow_operations[-5:],
            'cache_size': len(self.cache),
            'optimization_settings': self.settings.copy(),
            'performance_score': self._calculate_performance_score(summary)
        }

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        score = 100.0

        # Penalize slow render times
        avg_render = metrics['avg_render_time']
        if avg_render > 0.05:
            score -= min(50, (avg_render - 0.05) * 100)

        # Penalize slow filter times
        avg_filter = metrics['avg_filter_time']
        if avg_filter > 0.02:
            score -= min(30, (avg_filter - 0.02) * 100)

        # Bonus for efficient widget usage
        if metrics['recent_widget_counts']:
            avg_widgets = sum(metrics['recent_widget_counts']) / len(metrics['recent_widget_counts'])
            if avg_widgets < 50:
                score += min(20, (50 - avg_widgets) * 0.4)

        return max(0, min(100, score))

    def clear_slow_operations(self):
        """Clear recorded slow operations"""
        self.slow_operations.clear()

    def reset_metrics(self):
        """Reset all performance metrics"""
        self.metrics = PerformanceMetrics()
        self.clear_slow_operations()

    def optimize_list_rendering(self, items: List[Any], render_callback: Callable,
                               container_widget, item_height: int = 40) -> Dict[str, Any]:
        """Optimize list rendering with virtual scrolling recommendations"""
        total_items = len(items)
        container_height = container_widget.winfo_height() if hasattr(container_widget, 'winfo_height') else 400

        # Calculate visible items
        visible_items = container_height // item_height

        # Recommendations
        recommendations = []

        if total_items > 100:
            recommendations.append("Consider using virtual scrolling for large datasets")

        if visible_items < total_items * 0.1:
            recommendations.append("Virtual scrolling would provide significant performance benefits")

        if total_items > 500:
            recommendations.append("Implement pagination for very large datasets")

        return {
            'total_items': total_items,
            'visible_items': visible_items,
            'recommended_approach': 'virtual_scrolling' if total_items > visible_items * 2 else 'standard',
            'performance_benefit': (total_items - visible_items) / total_items * 100,
            'recommendations': recommendations
        }

    def cleanup(self):
        """Clean up resources"""
        self.debouncer.cancel_all()
        self.invalidate_cache()
        self.reset_metrics()