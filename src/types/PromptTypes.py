"""
PromptTypes - Type definitions for prompt-related data structures
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """Types of prompts supported by the application"""
    TEXT = "text"
    CODE = "code"
    SYSTEM = "system"
    CUSTOM = "custom"
    TEMPLATE = "template"


@dataclass
class Prompt:
    """Represents a single prompt with metadata"""
    id: str
    title: str
    prompt: str
    category: str
    tags: List[str]
    favorite: bool = False
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    usage_count: int = 0
    prompt_type: PromptType = PromptType.TEXT
    template_variables: List[str] = None
    is_template: bool = False
    last_used: Optional[str] = None
    rating: int = 0  # 1-5 star rating
    notes: str = ""  # User notes about the prompt

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "title": self.title,
            "prompt": self.prompt,
            "category": self.category,
            "tags": self.tags,
            "favorite": self.favorite,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "usage_count": self.usage_count,
            "type": self.prompt_type.value,
            "template_variables": self.template_variables or [],
            "is_template": self.is_template,
            "last_used": self.last_used,
            "rating": self.rating,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """Create from dictionary representation"""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            prompt=data.get("prompt", ""),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            favorite=data.get("favorite", False),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
            usage_count=data.get("usage_count", 0),
            prompt_type=PromptType(data.get("type", "text")),
            template_variables=data.get("template_variables", []),
            is_template=data.get("is_template", False),
            last_used=data.get("last_used"),
            rating=data.get("rating", 0),
            notes=data.get("notes", "")
        )


@dataclass
class Category:
    """Represents a prompt category with metadata"""
    id: str
    name: str
    description: str = ""
    icon: str = ""
    color: str = ""
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    prompt_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "prompt_count": self.prompt_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        """Create from dictionary representation"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            color=data.get("color", ""),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
            prompt_count=data.get("prompt_count", 0)
        )


@dataclass
class PromptLibrary:
    """Container for the entire prompt library structure"""
    categories: Dict[str, Category]
    prompts: Dict[str, List[Prompt]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "prompts": {k: [p.to_dict() for p in v] for k, v in self.prompts.items()},
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptLibrary":
        """Create from dictionary representation"""
        categories = {k: Category.from_dict(v) for k, v in data.get("categories", {}).items()}
        prompts = {}
        for cat_id, prompt_list in data.get("prompts", {}).items():
            prompts[cat_id] = [Prompt.from_dict(p) for p in prompt_list]

        return cls(
            categories=categories,
            prompts=prompts,
            metadata=data.get("metadata", {})
        )


@dataclass
class PromptTemplate:
    """Represents a prompt template with variables"""
    id: str
    name: str
    content: str
    variables: List[str]
    description: str = ""
    category: str = "Templates"
    created_at: Optional[str] = None
    usage_count: int = 0
    last_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "variables": self.variables,
            "description": self.description,
            "category": self.category,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
            "last_used": self.last_used
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptTemplate":
        """Create from dictionary representation"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            content=data.get("content", ""),
            variables=data.get("variables", []),
            description=data.get("description", ""),
            category=data.get("category", "Templates"),
            created_at=data.get("created_at"),
            usage_count=data.get("usage_count", 0),
            last_used=data.get("last_used")
        )


# Type aliases for better readability
PromptID = str
CategoryID = str
TagList = List[str]
PromptDict = Dict[str, Any]
CategoryDict = Dict[str, Any]
TemplateDict = Dict[str, Any]