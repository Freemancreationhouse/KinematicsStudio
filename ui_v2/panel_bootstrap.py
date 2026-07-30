from __future__ import annotations

from typing import Any

from ui_v2.bcf_topic_browser_panel import BCFTopicBrowserPanel
from ui_v2.block_manager_panel import BlockManagerPanel
from ui_v2.clash_dashboard_panel import ClashDashboardPanel
from ui_v2.clash_manager_panel import ClashManagerPanel
from ui_v2.constraint_manager_panel import ConstraintManagerPanel
from ui_v2.coordination_panel import CoordinationPanel
from ui_v2.dimension_manager_panel import DimensionManagerPanel
from ui_v2.explorer_panel import ExplorerPanel
from ui_v2.group_manager_panel import GroupManagerPanel
from ui_v2.layer_manager_panel import LayerManagerPanel
from ui_v2.pattern_manager_panel import PatternManagerPanel
from ui_v2.project_manager_panel import ProjectManagerPanel
from ui_v2.reference_browser_panel import ReferenceBrowserPanel
from ui_v2.reference_layer_panel import ReferenceLayerPanel
from ui_v2.selection_set_manager_panel import SelectionSetManagerPanel


class PanelBootstrap:
    """Registers production workspace panels with a WorkspacePanelManager."""

    @staticmethod
    def register_all(*, panel_manager: Any, app: Any) -> None:
        """Register every production panel as a lazy on-demand factory."""

        panel_manager.register_panel(
            panel_id="explorer",
            title="Explorer",
            factory=lambda: ExplorerPanel(),
            singleton=True,
            category="Project",
        )
        panel_manager.register_panel(
            panel_id="project_manager",
            title="Project Manager",
            factory=lambda: ProjectManagerPanel(app),
            singleton=True,
            category="Project",
        )
        panel_manager.register_panel(
            panel_id="layer_manager",
            title="Layer Manager",
            factory=lambda: LayerManagerPanel(app.workspace),
            singleton=True,
            category="CAD",
        )
        panel_manager.register_panel(
            panel_id="dimension_manager",
            title="Dimension Manager",
            factory=lambda: DimensionManagerPanel(app.workspace),
            singleton=True,
            category="CAD",
        )
        panel_manager.register_panel(
            panel_id="pattern_manager",
            title="Pattern Manager",
            factory=lambda: PatternManagerPanel(app.workspace),
            singleton=True,
            category="CAD",
        )
        panel_manager.register_panel(
            panel_id="block_manager",
            title="Block Manager",
            factory=lambda: BlockManagerPanel(app.workspace),
            singleton=True,
            category="CAD",
        )
        panel_manager.register_panel(
            panel_id="group_manager",
            title="Group Manager",
            factory=lambda: GroupManagerPanel(app.workspace),
            singleton=True,
            category="CAD",
        )
        panel_manager.register_panel(
            panel_id="selection_sets",
            title="Selection Sets",
            factory=lambda: SelectionSetManagerPanel(app.workspace),
            singleton=True,
            category="Selection",
        )
        panel_manager.register_panel(
            panel_id="constraint_manager",
            title="Constraint Manager",
            factory=lambda: ConstraintManagerPanel(app.workspace),
            singleton=True,
            category="Constraints",
        )
        panel_manager.register_panel(
            panel_id="reference_browser",
            title="Reference Browser",
            factory=lambda: ReferenceBrowserPanel(app.workspace),
            singleton=True,
            category="References",
        )
        panel_manager.register_panel(
            panel_id="reference_layers",
            title="Reference Layers",
            factory=lambda: ReferenceLayerPanel(app.workspace),
            singleton=True,
            category="References",
        )
        panel_manager.register_panel(
            panel_id="coordination",
            title="Coordination",
            factory=lambda: CoordinationPanel(app.workspace),
            singleton=True,
            category="Coordination",
        )
        panel_manager.register_panel(
            panel_id="clash_manager",
            title="Clash Manager",
            factory=lambda: ClashManagerPanel(app.workspace),
            singleton=True,
            category="BIM Coordination",
        )
        panel_manager.register_panel(
            panel_id="clash_dashboard",
            title="Clash Dashboard",
            factory=lambda: ClashDashboardPanel(app.workspace),
            singleton=True,
            category="BIM Coordination",
        )
        panel_manager.register_panel(
            panel_id="bcf_topic_browser",
            title="BCF Topic Browser",
            factory=lambda: BCFTopicBrowserPanel(app.workspace),
            singleton=True,
            category="BIM Coordination",
        )
