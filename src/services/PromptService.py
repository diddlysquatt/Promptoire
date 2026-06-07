"""
PromptService - Enhanced prompt management with templates and history
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import copy

from ..types.PromptTypes import Prompt, PromptType, Category, PromptLibrary
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PromptTemplate:
    """Represents a prompt template with variables"""

    def __init__(self, name: str, content: str, variables: List[str] = None,
                 description: str = "", category: str = "Templates"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.content = content
        self.variables = variables or []
        self.description = description
        self.category = category
        self.created_at = datetime.now().isoformat()
        self.usage_count = 0

    def render(self, variables: Dict[str, str]) -> str:
        """Render template with provided variables"""
        content = self.content
        for var, value in variables.items():
            content = content.replace(f"{{{{{var}}}}}", value)
        self.usage_count += 1
        return content

    def extract_variables(self) -> List[str]:
        """Extract variables from template content"""
        import re
        return list(set(re.findall(r'\{\{(\w+)\}\}', self.content)))


class PromptHistory:
    """Manages prompt usage history"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.file_path = Path("data/prompt_history.json")
        self.load_history()

    def add_usage(self, prompt: Prompt, rendered_content: str = None):
        """Add prompt usage to history"""
        entry = {
            "id": str(uuid.uuid4()),
            "prompt_id": prompt.id,
            "prompt_title": prompt.title,
            "prompt_content": rendered_content or prompt.prompt,
            "category": prompt.category,
            "tags": prompt.tags,
            "timestamp": datetime.now().isoformat(),
            "usage_type": "direct"
        }

        self.history.append(entry)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        self.save_history()

    def add_template_usage(self, template: PromptTemplate, variables: Dict[str, str],
                          rendered_content: str):
        """Add template usage to history"""
        entry = {
            "id": str(uuid.uuid4()),
            "template_id": template.id,
            "template_name": template.name,
            "template_content": rendered_content,
            "variables": variables,
            "category": template.category,
            "timestamp": datetime.now().isoformat(),
            "usage_type": "template"
        }

        self.history.append(entry)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        self.save_history()

    def get_recent_usage(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent prompt usage"""
        return sorted(self.history, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_usage_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get usage history for specific category"""
        return [h for h in self.history if h.get("category") == category]

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_usage = len(self.history)
        category_stats = {}
        tag_stats = {}

        for entry in self.history:
            cat = entry.get("category", "Unknown")
            category_stats[cat] = category_stats.get(cat, 0) + 1

            for tag in entry.get("tags", []):
                tag_stats[tag] = tag_stats.get(tag, 0) + 1

        return {
            "total_usage": total_usage,
            "category_stats": category_stats,
            "tag_stats": tag_stats,
            "most_used_category": max(category_stats.items(), key=lambda x: x[1])[0] if category_stats else None,
            "most_used_tag": max(tag_stats.items(), key=lambda x: x[1])[0] if tag_stats else None
        }

    def load_history(self):
        """Load history from file"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prompt history: {e}")
            self.history = []

    def save_history(self):
        """Save history to file"""
        try:
            self.file_path.parent.mkdir(exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save prompt history: {e}")


class PromptService:
    """Enhanced prompt management service"""

    def __init__(self, prompts_file: str = "data/prompt_library.json"):
        self.prompts_file = Path(prompts_file)
        self.templates: Dict[str, PromptTemplate] = {}
        self.history = PromptHistory()
        self.prompt_library: Optional[PromptLibrary] = None
        self.load_prompts()
        self.load_templates()

    def load_prompts(self):
        """Load prompts from file"""
        try:
            if self.prompts_file.exists():
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.prompt_library = PromptLibrary.from_dict(data)
            else:
                self.prompt_library = PromptLibrary(categories={}, prompts={}, metadata={})
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            self.prompt_library = PromptLibrary(categories={}, prompts={}, metadata={})

    def save_prompts(self):
        """Save prompts to file"""
        try:
            if self.prompt_library:
                self.prompts_file.parent.mkdir(exist_ok=True)
                with open(self.prompts_file, 'w', encoding='utf-8') as f:
                    json.dump(self.prompt_library.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")

    def load_templates(self):
        """Load prompt templates"""
        templates_file = Path("data/prompt_templates.json")
        try:
            if templates_file.exists():
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for template_data in data.get("templates", []):
                    template = PromptTemplate(**template_data)
                    self.templates[template.id] = template
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")

    def save_templates(self):
        """Save prompt templates"""
        templates_file = Path("data/prompt_templates.json")
        try:
            templates_file.parent.mkdir(exist_ok=True)
            data = {
                "templates": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "content": t.content,
                        "variables": t.variables,
                        "description": t.description,
                        "category": t.category,
                        "created_at": t.created_at,
                        "usage_count": t.usage_count
                    }
                    for t in self.templates.values()
                ]
            }
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")

    def create_template(self, name: str, content: str, description: str = "",
                       category: str = "Templates") -> PromptTemplate:
        """Create a new prompt template"""
        template = PromptTemplate(name=name, content=content, description=description,
                                category=category)
        template.variables = template.extract_variables()
        self.templates[template.id] = template
        self.save_templates()
        return template

    def render_template(self, template_id: str, variables: Dict[str, str]) -> str:
        """Render a template with variables"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")

        template = self.templates[template_id]
        rendered = template.render(variables)
        self.history.add_template_usage(template, variables, rendered)
        return rendered

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get templates by category"""
        return [t for t in self.templates.values() if t.category == category]

    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all templates"""
        return list(self.templates.values())

    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            self.save_templates()
            return True
        return False

    def update_template(self, template_id: str, **kwargs) -> bool:
        """Update template properties"""
        if template_id not in self.templates:
            return False

        template = self.templates[template_id]
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)

        if 'content' in kwargs:
            template.variables = template.extract_variables()

        self.save_templates()
        return True

    def use_prompt(self, prompt: Prompt, rendered_content: str = None):
        """Record prompt usage"""
        self.history.add_usage(prompt, rendered_content)

        # Update prompt usage count in the library if we can find it
        if not self.prompt_library or not self.prompt_library.prompts:
            return
        try:
            for prompts in self.prompt_library.prompts.values():
                for lib_prompt in prompts:
                    if lib_prompt.id and prompt.id and lib_prompt.id == prompt.id:
                        lib_prompt.usage_count = (lib_prompt.usage_count or 0) + 1
                        lib_prompt.modified_at = datetime.now().isoformat()
                        self.save_prompts()
                        return
        except Exception:
            # Never fail prompt usage tracking if the library is inconsistent
            return

    def get_recent_prompts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently used prompts"""
        return self.history.get_recent_usage(limit)

    def get_prompt_stats(self) -> Dict[str, Any]:
        """Get prompt usage statistics"""
        return self.history.get_usage_stats()

    def search_prompts(self, query: str, category: str = None, tags: List[str] = None) -> List[Prompt]:
        """Search prompts by text, category, or tags"""
        results = []

        if not self.prompt_library:
            return results

        query_lower = query.lower()

        for category_id, prompts in self.prompt_library.prompts.items():
            if category and category_id != category:
                continue

            for prompt in prompts:
                # Text search
                if query and query_lower not in prompt.title.lower() and query_lower not in prompt.prompt.lower():
                    continue

                # Tag search
                if tags and not any(tag in prompt.tags for tag in tags):
                    continue

                results.append(prompt)

        return results

    def add_prompt(self, title: str, content: str, category: str = "General",
                   tags: List[str] = None, prompt_type: PromptType = PromptType.TEXT) -> Prompt:
        """Add a new prompt"""
        if not self.prompt_library:
            self.prompt_library = PromptLibrary(categories={}, prompts={}, metadata={})

        prompt = Prompt(
            id=str(uuid.uuid4()),
            title=title,
            prompt=content,
            category=category,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            modified_at=datetime.now().isoformat(),
            prompt_type=prompt_type
        )

        if category not in self.prompt_library.prompts:
            self.prompt_library.prompts[category] = []

        self.prompt_library.prompts[category].append(prompt)
        self.save_prompts()
        return prompt

    def update_prompt(self, prompt_id: str, **kwargs) -> bool:
        """Update an existing prompt"""
        if not self.prompt_library:
            return False

        for category_id, prompts in self.prompt_library.prompts.items():
            for prompt in prompts:
                if prompt.id == prompt_id:
                    for key, value in kwargs.items():
                        if hasattr(prompt, key):
                            setattr(prompt, key, value)

                    prompt.modified_at = datetime.now().isoformat()
                    self.save_prompts()
                    return True

        return False

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt"""
        if not self.prompt_library:
            return False

        for category_id, prompts in self.prompt_library.prompts.items():
            for i, prompt in enumerate(prompts):
                if prompt.id == prompt_id:
                    prompts.pop(i)
                    self.save_prompts()
                    return True

        return False

    def get_categories(self) -> List[str]:
        """Get all categories"""
        if not self.prompt_library:
            return []
        return list(self.prompt_library.prompts.keys())

    def get_prompts_by_category(self, category: str) -> List[Prompt]:
        """Get prompts by category"""
        if not self.prompt_library:
            return []
        return self.prompt_library.prompts.get(category, [])

    def export_data(self) -> Dict[str, Any]:
        """Export all prompt data"""
        return {
            "prompts": self.prompt_library.to_dict() if self.prompt_library else {},
            "templates": {
                "templates": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "content": t.content,
                        "variables": t.variables,
                        "description": t.description,
                        "category": t.category,
                        "created_at": t.created_at,
                        "usage_count": t.usage_count
                    }
                    for t in self.templates.values()
                ]
            },
            "history": self.history.history
        }

    def import_data(self, data: Dict[str, Any], merge: bool = True) -> bool:
        """Import prompt data"""
        try:
            if "prompts" in data:
                if merge and self.prompt_library:
                    # Merge logic here
                    pass
                else:
                    self.prompt_library = PromptLibrary.from_dict(data["prompts"])

            if "templates" in data:
                if not merge:
                    self.templates.clear()

                for template_data in data["templates"].get("templates", []):
                    template = PromptTemplate(**template_data)
                    self.templates[template.id] = template

            if "history" in data and not merge:
                self.history.history = data["history"]

            self.save_prompts()
            self.save_templates()
            self.history.save_history()
            return True
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            return False
