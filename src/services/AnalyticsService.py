"""
AnalyticsService - Advanced usage analytics and reporting for prompts
"""

import json
import time
import copy
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics

from ..utils.logger import get_logger

logger = get_logger(__name__)


class UsageMetrics:
    """Tracks detailed usage metrics"""

    def __init__(self):
        self.session_metrics = {
            "session_start": datetime.now().isoformat(),
            "total_prompts_used": 0,
            "total_templates_used": 0,
            "categories_used": set(),
            "tags_used": set(),
            "prompts_by_category": defaultdict(int),
            "prompts_by_hour": defaultdict(int),
            "search_queries": [],
            "copy_operations": 0,
            "edit_operations": 0,
            "favorite_operations": 0,
            "session_duration": 0
        }

    def record_prompt_usage(self, prompt_data: Dict[str, Any]):
        """Record a prompt usage event"""
        self.session_metrics["total_prompts_used"] += 1
        self.session_metrics["categories_used"].add(prompt_data.get("category", "Unknown"))

        for tag in prompt_data.get("tags", []):
            self.session_metrics["tags_used"].add(tag)

        self.session_metrics["prompts_by_category"][prompt_data.get("category", "Unknown")] += 1

        # Track usage by hour
        current_hour = datetime.now().hour
        self.session_metrics["prompts_by_hour"][current_hour] += 1

    def record_template_usage(self, template_data: Dict[str, Any]):
        """Record a template usage event"""
        self.session_metrics["total_templates_used"] += 1
        self.session_metrics["categories_used"].add(template_data.get("category", "Templates"))

    def record_search(self, query: str, results_count: int):
        """Record a search query"""
        self.session_metrics["search_queries"].append({
            "query": query,
            "results_count": results_count,
            "timestamp": datetime.now().isoformat()
        })

    def record_copy(self):
        """Record a copy operation"""
        self.session_metrics["copy_operations"] += 1

    def record_edit(self):
        """Record an edit operation"""
        self.session_metrics["edit_operations"] += 1

    def record_favorite_toggle(self):
        """Record a favorite toggle operation"""
        self.session_metrics["favorite_operations"] += 1

    def finalize_session(self):
        """Finalize session metrics"""
        start_time = datetime.fromisoformat(self.session_metrics["session_start"])
        end_time = datetime.now()
        self.session_metrics["session_duration"] = (end_time - start_time).total_seconds()

        # Convert sets to lists for JSON serialization
        self.session_metrics["categories_used"] = list(self.session_metrics["categories_used"])
        self.session_metrics["tags_used"] = list(self.session_metrics["tags_used"])


class AnalyticsData:
    """Stores and manages analytics data over time"""

    def __init__(self, data_file: str = "data/analytics.json"):
        self.data_file = Path(data_file)
        self.data = {
            "daily_stats": {},
            "weekly_stats": {},
            "monthly_stats": {},
            "all_time_stats": {
                "total_prompts_used": 0,
                "total_templates_used": 0,
                "total_sessions": 0,
                "total_session_time": 0,
                "most_used_categories": {},
                "most_used_tags": {},
                "peak_usage_hours": {},
                "average_session_duration": 0
            },
            "usage_patterns": {
                "category_trends": {},
                "tag_trends": {},
                "hourly_patterns": defaultdict(lambda: defaultdict(int)),
                "daily_patterns": defaultdict(lambda: defaultdict(int))
            }
        }
        self.load_data()

    def load_data(self):
        """Load analytics data from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)

                # Handle defaultdict conversion
                self.data["usage_patterns"]["hourly_patterns"] = defaultdict(
                    lambda: defaultdict(int),
                    loaded_data.get("usage_patterns", {}).get("hourly_patterns", {})
                )
                self.data["usage_patterns"]["daily_patterns"] = defaultdict(
                    lambda: defaultdict(int),
                    loaded_data.get("usage_patterns", {}).get("daily_patterns", {})
                )

                # Merge with default structure
                for key in self.data:
                    if key in loaded_data:
                        if isinstance(self.data[key], dict) and isinstance(loaded_data[key], dict):
                            self.data[key].update(loaded_data[key])
                        else:
                            self.data[key] = loaded_data[key]
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")

    def save_data(self):
        """Save analytics data to file"""
        try:
            self.data_file.parent.mkdir(exist_ok=True)

            # Convert defaultdicts to regular dicts for JSON serialization
            save_data = copy.deepcopy(self.data)
            save_data["usage_patterns"]["hourly_patterns"] = dict(
                {k: dict(v) for k, v in self.data["usage_patterns"]["hourly_patterns"].items()}
            )
            save_data["usage_patterns"]["daily_patterns"] = dict(
                {k: dict(v) for k, v in self.data["usage_patterns"]["daily_patterns"].items()}
            )

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")

    def record_session(self, session_metrics: Dict[str, Any]):
        """Record a completed session"""
        date_key = datetime.now().strftime("%Y-%m-%d")
        week_key = datetime.now().strftime("%Y-W%U")
        month_key = datetime.now().strftime("%Y-%m")

        # Update daily stats
        if date_key not in self.data["daily_stats"]:
            self.data["daily_stats"][date_key] = {
                "date": date_key,
                "prompts_used": 0,
                "templates_used": 0,
                "sessions": 0,
                "session_time": 0,
                "categories_used": [],
                "tags_used": []
            }

        daily = self.data["daily_stats"][date_key]
        daily["prompts_used"] += session_metrics["total_prompts_used"]
        daily["templates_used"] += session_metrics["total_templates_used"]
        daily["sessions"] += 1
        daily["session_time"] += session_metrics["session_duration"]
        daily["categories_used"].extend(session_metrics["categories_used"])
        daily["tags_used"].extend(session_metrics["tags_used"])

        # Update all-time stats
        all_time = self.data["all_time_stats"]
        all_time["total_prompts_used"] += session_metrics["total_prompts_used"]
        all_time["total_templates_used"] += session_metrics["total_templates_used"]
        all_time["total_sessions"] += 1
        all_time["total_session_time"] += session_metrics["session_duration"]

        # Update most used categories and tags
        for category in session_metrics["categories_used"]:
            all_time["most_used_categories"][category] = all_time["most_used_categories"].get(category, 0) + 1

        for tag in session_metrics["tags_used"]:
            all_time["most_used_tags"][tag] = all_time["most_used_tags"].get(tag, 0) + 1

        # Update peak usage hours
        for hour, count in session_metrics["prompts_by_hour"].items():
            all_time["peak_usage_hours"][str(hour)] = all_time["peak_usage_hours"].get(str(hour), 0) + count

        # Calculate average session duration
        if all_time["total_sessions"] > 0:
            all_time["average_session_duration"] = all_time["total_session_time"] / all_time["total_sessions"]

        # Update usage patterns
        self._update_usage_patterns(session_metrics)

        # Cleanup old data (keep last 90 days)
        self._cleanup_old_data()

        self.save_data()

    def _update_usage_patterns(self, session_metrics: Dict[str, Any]):
        """Update usage pattern tracking"""
        date_key = datetime.now().strftime("%Y-%m-%d")
        hour_key = datetime.now().hour

        # Category trends
        for category, count in session_metrics["prompts_by_category"].items():
            self.data["usage_patterns"]["category_trends"][category] = \
                self.data["usage_patterns"]["category_trends"].get(category, 0) + count

        # Hourly patterns
        self.data["usage_patterns"]["hourly_patterns"][date_key][hour_key] += session_metrics["total_prompts_used"]

        # Daily patterns (day of week)
        day_of_week = datetime.now().weekday()
        self.data["usage_patterns"]["daily_patterns"][str(day_of_week)][date_key] += session_metrics["total_prompts_used"]

    def _cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old analytics data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_key = cutoff_date.strftime("%Y-%m-%d")

        # Clean daily stats
        self.data["daily_stats"] = {
            k: v for k, v in self.data["daily_stats"].items()
            if k >= cutoff_key
        }

        # Clean hourly patterns
        self.data["usage_patterns"]["hourly_patterns"] = {
            k: v for k, v in self.data["usage_patterns"]["hourly_patterns"].items()
            if k >= cutoff_key
        }

        # Clean daily patterns
        for day_key in self.data["usage_patterns"]["daily_patterns"]:
            self.data["usage_patterns"]["daily_patterns"][day_key] = {
                k: v for k, v in self.data["usage_patterns"]["daily_patterns"][day_key].items()
                if k >= cutoff_key
            }


class AnalyticsService:
    """Main analytics service for prompt usage tracking and reporting"""

    def __init__(self, data_file: str = "data/analytics.json"):
        self.analytics_data = AnalyticsData(data_file)
        self.current_session = UsageMetrics()
        self.session_start_time = time.time()

    def record_prompt_usage(self, prompt_data: Dict[str, Any]):
        """Record prompt usage in current session"""
        self.current_session.record_prompt_usage(prompt_data)

    def record_template_usage(self, template_data: Dict[str, Any]):
        """Record template usage in current session"""
        self.current_session.record_template_usage(template_data)

    def record_search(self, query: str, results_count: int):
        """Record a search query"""
        self.current_session.record_search(query, results_count)

    def record_copy(self):
        """Record a copy operation"""
        self.current_session.record_copy()

    def record_edit(self):
        """Record an edit operation"""
        self.current_session.record_edit()

    def record_favorite_toggle(self):
        """Record a favorite toggle operation"""
        self.current_session.record_favorite_toggle()

    def end_session(self):
        """End current session and record metrics"""
        self.current_session.finalize_session()
        session_data = self.current_session.session_metrics
        self.analytics_data.record_session(session_data)

        # Start new session
        self.current_session = UsageMetrics()
        self.session_start_time = time.time()

    def get_usage_summary(self, period: str = "all") -> Dict[str, Any]:
        """Get usage summary for a specific period"""
        if period == "all":
            return self.analytics_data.data["all_time_stats"]
        elif period == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            return self.analytics_data.data["daily_stats"].get(today, {})
        elif period == "week":
            week_key = datetime.now().strftime("%Y-W%U")
            # Calculate week stats from daily data
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_stats = {"prompts_used": 0, "templates_used": 0, "sessions": 0}

            for i in range(7):
                day_key = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
                daily = self.analytics_data.data["daily_stats"].get(day_key, {})
                week_stats["prompts_used"] += daily.get("prompts_used", 0)
                week_stats["templates_used"] += daily.get("templates_used", 0)
                week_stats["sessions"] += daily.get("sessions", 0)

            return week_stats
        elif period == "month":
            month_key = datetime.now().strftime("%Y-%m")
            # Calculate month stats from daily data
            month_stats = {"prompts_used": 0, "templates_used": 0, "sessions": 0}

            for day_key, daily in self.analytics_data.data["daily_stats"].items():
                if day_key.startswith(month_key):
                    month_stats["prompts_used"] += daily.get("prompts_used", 0)
                    month_stats["templates_used"] += daily.get("templates_used", 0)
                    month_stats["sessions"] += daily.get("sessions", 0)

            return month_stats

        return {}

    def get_category_analytics(self) -> Dict[str, Any]:
        """Get category-specific analytics"""
        all_time = self.analytics_data.data["all_time_stats"]
        category_trends = self.analytics_data.data["usage_patterns"]["category_trends"]

        return {
            "most_used": sorted(all_time["most_used_categories"].items(),
                              key=lambda x: x[1], reverse=True)[:10],
            "trends": category_trends,
            "total_categories": len(all_time["most_used_categories"])
        }

    def get_time_analytics(self) -> Dict[str, Any]:
        """Get time-based analytics"""
        all_time = self.analytics_data.data["all_time_stats"]
        hourly_patterns = self.analytics_data.data["usage_patterns"]["hourly_patterns"]
        daily_patterns = self.analytics_data.data["usage_patterns"]["daily_patterns"]

        # Calculate average usage by hour
        hourly_avg = defaultdict(int)
        total_days = len(hourly_patterns)

        if total_days > 0:
            for date_data in hourly_patterns.values():
                for hour, count in date_data.items():
                    hourly_avg[hour] += count

            for hour in hourly_avg:
                hourly_avg[hour] //= total_days

        # Calculate average usage by day of week
        daily_avg = defaultdict(int)
        total_weeks = max(len(daily_patterns.get(str(day), {})) for day in range(7)) if daily_patterns else 0

        if total_weeks > 0:
            for day_data in daily_patterns.values():
                for date, count in day_data.items():
                    daily_avg[int(day)] += count

            for day in daily_avg:
                daily_avg[day] //= total_weeks

        return {
            "peak_hours": sorted(all_time["peak_usage_hours"].items(),
                               key=lambda x: x[1], reverse=True)[:5],
            "hourly_average": dict(hourly_avg),
            "daily_average": dict(daily_avg),
            "average_session_duration": all_time["average_session_duration"]
        }

    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search-related analytics"""
        # Get recent searches from current session
        recent_searches = self.current_session.session_metrics["search_queries"][-10:]

        # Calculate search effectiveness
        total_searches = len(recent_searches)
        avg_results = 0
        if total_searches > 0:
            avg_results = sum(s["results_count"] for s in recent_searches) / total_searches

        return {
            "recent_searches": recent_searches,
            "total_searches_session": total_searches,
            "average_results": avg_results
        }

    def get_productivity_metrics(self) -> Dict[str, Any]:
        """Get productivity-related metrics"""
        session = self.current_session.session_metrics
        session_duration = time.time() - self.session_start_time

        return {
            "current_session_duration": session_duration,
            "prompts_per_hour": (session["total_prompts_used"] / (session_duration / 3600)) if session_duration > 0 else 0,
            "copy_operations": session["copy_operations"],
            "edit_operations": session["edit_operations"],
            "favorite_operations": session["favorite_operations"],
            "efficiency_score": self._calculate_efficiency_score(session, session_duration)
        }

    def _calculate_efficiency_score(self, session_data: Dict[str, Any], duration: float) -> float:
        """Calculate an efficiency score based on usage patterns"""
        if duration < 60:  # Less than 1 minute
            return 0.0

        # Base score from prompt usage
        prompt_score = min(session_data["total_prompts_used"] / 10, 1.0) * 40

        # Search efficiency
        search_count = len(session_data["search_queries"])
        search_score = min(search_count / 5, 1.0) * 20 if search_count > 0 else 0

        # Operation diversity
        operations = session_data["copy_operations"] + session_data["edit_operations"] + session_data["favorite_operations"]
        operation_score = min(operations / 10, 1.0) * 20

        # Category exploration
        category_score = min(len(session_data["categories_used"]) / 3, 1.0) * 20

        return round(prompt_score + search_score + operation_score + category_score, 1)

    def export_analytics(self, format: str = "json") -> str:
        """Export analytics data"""
        export_data = {
            "export_date": datetime.now().isoformat(),
            "all_time_stats": self.analytics_data.data["all_time_stats"],
            "daily_stats": self.analytics_data.data["daily_stats"],
            "category_analytics": self.get_category_analytics(),
            "time_analytics": self.get_time_analytics(),
            "search_analytics": self.get_search_analytics(),
            "productivity_metrics": self.get_productivity_metrics()
        }

        if format == "json":
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format == "csv":
            # Convert to CSV format (simplified)
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write all-time stats
            writer.writerow(["Metric", "Value"])
            for key, value in export_data["all_time_stats"].items():
                if key not in ["most_used_categories", "most_used_tags", "peak_usage_hours"]:
                    writer.writerow([key, value])

            return output.getvalue()

        return str(export_data)

    def reset_analytics(self):
        """Reset all analytics data"""
        self.analytics_data.data = {
            "daily_stats": {},
            "weekly_stats": {},
            "monthly_stats": {},
            "all_time_stats": {
                "total_prompts_used": 0,
                "total_templates_used": 0,
                "total_sessions": 0,
                "total_session_time": 0,
                "most_used_categories": {},
                "most_used_tags": {},
                "peak_usage_hours": {},
                "average_session_duration": 0
            },
            "usage_patterns": {
                "category_trends": {},
                "tag_trends": {},
                "hourly_patterns": defaultdict(lambda: defaultdict(int)),
                "daily_patterns": defaultdict(lambda: defaultdict(int))
            }
        }
        self.analytics_data.save_data()