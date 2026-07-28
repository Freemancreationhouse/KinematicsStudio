from dataclasses import dataclass, field
from string import Template


@dataclass
class PromptTemplate:
    """Reusable production prompt template."""

    name: str
    text: str
    parent: str = ""
    variables: dict = field(default_factory=dict)

    def render(self, variables=None, parent_text=""):
        """Render the template with explicit variables."""

        values = dict(self.variables)
        values.update(variables or {})
        text = f"{parent_text}\n{self.text}" if parent_text else self.text
        return Template(text).safe_substitute(values)

    def to_dict(self):
        """Return JSON-safe template state."""

        return {
            "name": self.name,
            "text": self.text,
            "parent": self.parent,
            "variables": dict(self.variables),
        }

    @classmethod
    def from_dict(cls, data):
        """Restore a prompt template."""

        return cls(
            data.get("name", ""),
            data.get("text", ""),
            data.get("parent", ""),
            dict(data.get("variables", {})),
        )


class PromptLibrary:
    """Stores reusable prompt templates without provider business logic."""

    def __init__(self):
        self.templates = {}

    def add(self, template):
        """Add or replace a prompt template."""

        if not isinstance(template, PromptTemplate):
            raise TypeError("template must be PromptTemplate")
        self.templates[template.name] = template
        return template

    def render(self, name, variables=None):
        """Render a stored template by name."""

        template = self.templates[name]
        parent_text = self.render(template.parent, variables) if template.parent else ""
        return template.render(variables, parent_text)

    def workspace_variables(self, workspace):
        """Build template variables from Workspace only."""

        selection = getattr(workspace, "selection", None)
        selected = list(getattr(selection, "selected", [])) if selection is not None else []
        product = getattr(workspace, "product_manager", None)
        return {
            "workspace_name": getattr(workspace, "name", ""),
            "selection_count": len(selected),
            "selected_names": ", ".join([getattr(item, "name", "") for item in selected]),
            "feature_count": len(getattr(product, "features", [])) if product is not None else 0,
            "body_count": len(getattr(product, "bodies", [])) if product is not None else 0,
            "history_count": getattr(getattr(workspace, "command_manager", None), "undo_count", 0),
        }

    def to_dict(self):
        """Return JSON-safe prompt library state."""

        return {"templates": [template.to_dict() for template in self.templates.values()]}

    def from_dict(self, data):
        """Restore prompt library state."""

        self.templates = {
            template.name: template
            for template in [PromptTemplate.from_dict(item) for item in data.get("templates", [])]
        }
