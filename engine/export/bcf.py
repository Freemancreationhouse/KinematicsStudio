import json

from .base import Exporter


class BCFExporter(Exporter):
    """Exports workspace BCF coordination data through the export framework."""

    extension = "bcf"
    format_name = "BCF"

    def serialize(self, context):
        """Return JSON-based BCF foundation content."""

        manager = getattr(context.workspace, "bcf_manager", None)

        if manager is None:
            return json.dumps({"bcf": {}}, indent=2)

        return json.dumps({"bcf": manager.active_project.to_dict()}, indent=2) + "\n"


class BCFExchange:
    """Small import/export helper that reuses the workspace-owned BCF manager."""

    def export(self, workspace, path, project=None):
        """Export one BCF project."""

        return workspace.bcf_manager.export_bcf(path, project)

    def import_file(self, workspace, path):
        """Import one BCF project into the workspace."""

        return workspace.bcf_manager.import_bcf(path)
