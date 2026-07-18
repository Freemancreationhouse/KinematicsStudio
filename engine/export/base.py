from abc import ABC, abstractmethod


class Exporter(ABC):
    """Base class for version-ready workspace exporters."""

    extension = ""
    format_name = ""

    def export(self, context, path):
        """Write an export file and return the destination path."""

        target = context.target_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        content = self.serialize(context)
        target.write_text(content, encoding="utf-8")

        return target

    @abstractmethod
    def serialize(self, context):
        """Return exporter-specific text content."""

