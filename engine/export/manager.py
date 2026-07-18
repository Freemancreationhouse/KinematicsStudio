from engine.entities import BlockReference

from .bcf import BCFExporter
from .cad_exchange import professional_cad_exporters
from .context import ExportContext, ExportEntity, ExportOptions
from .dxf import DXFExporter
from .eps import EPSExporter
from .helpers import layer_for
from .pdf import PDFExporter
from .png import PNGExporter
from .psd import PSDExporter
from .svg import SVGExporter


class ExportManager:
    """Builds canonical export contexts and dispatches format exporters."""

    def __init__(self):

        self._exporters = {}
        self.register(DXFExporter())
        self.register(SVGExporter())
        self.register(PDFExporter())
        self.register(PNGExporter())
        self.register(EPSExporter())
        self.register(PSDExporter())
        self.register(BCFExporter())
        for exporter in professional_cad_exporters():
            self.register(exporter)

    # --------------------------------

    def register(self, exporter):
        """Register an exporter by file extension."""

        self._exporters[exporter.extension.lower()] = exporter

        return exporter

    # --------------------------------

    def export(self, workspace, path, format_name=None, options=None):
        """Export a workspace using the requested or inferred format."""

        exporter = self._exporter_for(path, format_name)
        context = self.context(workspace, options)

        return exporter.export(context, path)

    # --------------------------------

    def context(self, workspace, options=None):
        """Create the canonical workspace export context."""

        opts = options or ExportOptions()

        return ExportContext(
            workspace=workspace,
            entities=self._collect_entities(workspace, opts),
            layers=list(getattr(workspace.layer_manager, "layers", [])),
            dimension_styles=list(getattr(workspace.dimension_style_manager, "styles", [])),
            patterns=list(getattr(workspace.pattern_manager, "patterns", [])),
            blocks=list(getattr(workspace.block_manager, "definitions", [])),
            groups=list(getattr(workspace.group_manager, "groups", [])),
            options=opts,
        )

    # --------------------------------

    def _collect_entities(self, workspace, options):

        if options.include_hidden_layers:
            source = [
                entity for entity in workspace.entities
                if getattr(entity, "visible", True)
            ]
        else:
            source = workspace.visible_entities()

        collected = []

        for entity in source:
            self._collect_entity(workspace, entity, collected, ())

        return collected

    # --------------------------------

    def _collect_entity(self, workspace, entity, collected, block_path):

        collected.append(ExportEntity(entity, layer_for(workspace, entity), block_path))

        if not isinstance(entity, BlockReference):
            return

        for child in entity.exploded_entities():
            self._collect_entity(
                workspace,
                child,
                collected,
                block_path + (getattr(entity, "definition_name", "Block"),),
            )

    # --------------------------------

    def _exporter_for(self, path, format_name=None):

        key = str(format_name or "").lower().lstrip(".")

        if not key:
            key = str(path).rsplit(".", 1)[-1].lower()

        exporter = self._exporters.get(key)

        if exporter is None:
            raise ValueError(f"Unsupported export format: {key}")

        return exporter
