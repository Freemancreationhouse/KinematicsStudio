from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from engine.geometry import BoundingBox3D, Vector3


CLASH_TYPES = (
    "Hard Clash",
    "Clearance Clash",
    "Duplicate Geometry",
    "Bounding Box Clash",
    "Reference Clash",
    "Category Clash",
    "Rule Placeholder",
)


@dataclass
class ClashSettings:
    """Reusable settings for clash detection."""

    enabled: bool = True
    visible: bool = True
    clearance: float = 0.0
    include_references: bool = True
    include_native: bool = True
    collection_filter: str = ""
    layer_filter: str = ""
    category_filter: str = ""
    selection_only: bool = False
    incremental: bool = True

    def to_dict(self):
        """Return JSON-safe settings."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create settings from persisted data."""

        data = data or {}

        return ClashSettings(
            bool(data.get("enabled", True)),
            bool(data.get("visible", True)),
            float(data.get("clearance", 0.0)),
            bool(data.get("include_references", True)),
            bool(data.get("include_native", True)),
            data.get("collection_filter", ""),
            data.get("layer_filter", ""),
            data.get("category_filter", ""),
            bool(data.get("selection_only", False)),
            bool(data.get("incremental", True)),
        )


@dataclass
class ClashStatistics:
    """Summary statistics for clash results."""

    total: int = 0
    hard: int = 0
    clearance: int = 0
    duplicate: int = 0
    bounding_box: int = 0
    reference: int = 0
    category: int = 0
    unresolved: int = 0

    def to_dict(self):
        """Return JSON-safe statistics."""

        return dict(self.__dict__)

    @staticmethod
    def from_results(results):
        """Build statistics from clash results."""

        return ClashStatistics(
            len(results),
            len([item for item in results if item.clash_type == "Hard Clash"]),
            len([item for item in results if item.clash_type == "Clearance Clash"]),
            len([item for item in results if item.clash_type == "Duplicate Geometry"]),
            len([item for item in results if item.clash_type == "Bounding Box Clash"]),
            len([item for item in results if item.clash_type == "Reference Clash"]),
            len([item for item in results if item.clash_type == "Category Clash"]),
            len([item for item in results if item.status != "Resolved"]),
        )


class ClashResult:
    """Persistent selectable 3D clash marker."""

    type_name = "ClashResult"
    is_3d = True
    is_clash = True

    def __init__(
        self,
        clash_type="Hard Clash",
        entity_a=None,
        entity_b=None,
        location=None,
        bounds=None,
        status="Open",
        severity="Medium",
        description="",
    ):

        self.id = str(uuid4())
        self.name = clash_type
        self.clash_type = clash_type if clash_type in CLASH_TYPES else "Hard Clash"
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.entity_a_name = _entity_name(entity_a)
        self.entity_b_name = _entity_name(entity_b)
        self.location = location or Vector3()
        self.bounds = bounds or BoundingBox3D()
        self.status = status
        self.severity = severity
        self.description = description or self._default_description()
        self.visible = True
        self.locked = False
        self.selected = False
        self.hovered = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = "#ff5252"
        self.priority = "Normal"
        self.assigned_reviewer = ""
        self.owner = ""
        self.due_date = ""
        self.comments = ""
        self.resolution_notes = ""
        self.resolution_category = ""
        self.approval_state = "Pending"
        self.watch_list = False
        self.review_queue = False
        self.discipline = ""
        self.linked_issue_id = ""
        self.linked_review_id = ""
        self.analytics_focus = False
        self.category = self._default_category()
        self.history = []

    @property
    def bounding_box3d(self):
        """Return clash display bounds."""

        if self.bounds.valid:
            return self.bounds

        box = BoundingBox3D()
        pad = 5.0
        box.add(self.location - Vector3(pad, pad, pad))
        box.add(self.location + Vector3(pad, pad, pad))

        return box

    @property
    def display_color(self):
        """Return clash display color."""

        return self.color

    def points(self):
        """Return representative points."""

        return [self.location]

    def segments(self):
        """Return marker segments."""

        pad = 8.0

        return [
            (self.location - Vector3(pad, 0.0, 0.0), self.location + Vector3(pad, 0.0, 0.0)),
            (self.location - Vector3(0.0, pad, 0.0), self.location + Vector3(0.0, pad, 0.0)),
            (self.location - Vector3(0.0, 0.0, pad), self.location + Vector3(0.0, 0.0, pad)),
        ]

    def to_dict(self):
        """Return JSON-safe clash data."""

        return {
            "id": self.id,
            "name": self.name,
            "clash_type": self.clash_type,
            "entity_a_name": self.entity_a_name,
            "entity_b_name": self.entity_b_name,
            "location": _vector_to_data(self.location),
            "bounds": _box_to_data(self.bounds),
            "status": self.status,
            "severity": self.severity,
            "description": self.description,
            "visible": self.visible,
            "locked": self.locked,
            "selected": self.selected,
            "layer_name": self.layer_name,
            "color": self.color,
            "priority": self.priority,
            "assigned_reviewer": self.assigned_reviewer,
            "owner": self.owner,
            "due_date": self.due_date,
            "comments": self.comments,
            "resolution_notes": self.resolution_notes,
            "resolution_category": self.resolution_category,
            "approval_state": self.approval_state,
            "watch_list": self.watch_list,
            "review_queue": self.review_queue,
            "discipline": self.discipline,
            "linked_issue_id": self.linked_issue_id,
            "linked_review_id": self.linked_review_id,
            "analytics_focus": self.analytics_focus,
            "category": self.category,
            "history": list(self.history),
        }

    @staticmethod
    def from_dict(data):
        """Create clash result from persisted data."""

        data = data or {}
        result = ClashResult(
            data.get("clash_type", "Hard Clash"),
            location=_vector_from_data(data.get("location")),
            bounds=_box_from_data(data.get("bounds")),
            status=data.get("status", "Open"),
            severity=data.get("severity", "Medium"),
            description=data.get("description", ""),
        )
        result.id = data.get("id", result.id)
        result.name = data.get("name", result.name)
        result.entity_a_name = data.get("entity_a_name", "")
        result.entity_b_name = data.get("entity_b_name", "")
        result.visible = bool(data.get("visible", True))
        result.locked = bool(data.get("locked", False))
        result.selected = bool(data.get("selected", False))
        result.layer_name = data.get("layer_name")
        result.color = data.get("color", result.color)
        result.priority = data.get("priority", result.priority)
        result.assigned_reviewer = data.get("assigned_reviewer", "")
        result.owner = data.get("owner", "")
        result.due_date = data.get("due_date", "")
        result.comments = data.get("comments", "")
        result.resolution_notes = data.get("resolution_notes", "")
        result.resolution_category = data.get("resolution_category", "")
        result.approval_state = data.get("approval_state", "Pending")
        result.watch_list = bool(data.get("watch_list", False))
        result.review_queue = bool(data.get("review_queue", False))
        result.discipline = data.get("discipline", "")
        result.linked_issue_id = data.get("linked_issue_id", "")
        result.linked_review_id = data.get("linked_review_id", "")
        result.analytics_focus = bool(data.get("analytics_focus", False))
        result.category = data.get("category", result._default_category())
        result.history = list(data.get("history", []))

        return result

    def _default_description(self):

        return f"{self.clash_type}: {self.entity_a_name} vs {self.entity_b_name}"

    def _default_category(self):

        return "Reference" if self.clash_type == "Reference Clash" else "Coordination"


class ClashGroup:
    """Named grouping for persistent clash results."""

    def __init__(self, name="Clash Group", result_ids=None, visible=True):

        self.id = str(uuid4())
        self.name = name
        self.result_ids = list(result_ids or [])
        self.visible = bool(visible)

    def to_dict(self):
        """Return JSON-safe group data."""

        return dict(self.__dict__)

    @staticmethod
    def from_dict(data):
        """Create group from persisted data."""

        data = data or {}
        group = ClashGroup(
            data.get("name", "Clash Group"),
            data.get("result_ids", []),
            data.get("visible", True),
        )
        group.id = data.get("id", group.id)

        return group


class ClashManager:
    """Workspace-owned clash detection and persistent clash storage."""

    def __init__(self):

        self.results = []
        self.groups = []
        self.settings = ClashSettings()
        self.statistics = ClashStatistics()
        self.current_result_id = None
        self.dock_state = {
            "search": "",
            "severity_filter": "All",
            "status_filter": "All",
            "group_by": "Severity",
            "sort_by": "Severity",
            "expanded": True,
        }
        self.report_settings = {
            "group_by": "Severity",
            "include_resolved": True,
            "last_format": "PDF",
            "template": "Detailed Report",
            "scheduled_enabled": False,
            "scheduled_interval": "Weekly",
        }
        self.dashboard_state = {
            "layout": "Summary",
            "filter": "All",
            "saved_filters": {},
            "saved_layouts": {},
        }
        self.report_templates = self._default_report_templates()
        self.analytics_settings = {
            "active_view": "Default",
            "trend_window": "All",
            "show_resolved": True,
        }
        self.saved_analytics_views = {}
        self.kpi_configuration = {
            "target_completion": 100.0,
            "critical_weight": 4.0,
            "high_weight": 2.0,
            "medium_weight": 1.0,
            "low_weight": 0.5,
        }

    def detect(self, workspace, settings=None):
        """Run broad-phase clash detection against visible candidates."""

        active_settings = settings or self.settings
        candidates = self._candidates(workspace, active_settings)
        results = []

        for index, first in enumerate(candidates):
            for second in candidates[index + 1:]:
                result = self._detect_pair(first, second, active_settings)

                if result is not None:
                    results.append(result)

        return results

    def set_results(self, results):
        """Replace persistent clash results."""

        self.results = list(results)
        self.statistics = ClashStatistics.from_results(self.results)
        self.current_result_id = self.results[0].id if self.results else None

        if not self.groups and self.results:
            self.groups.append(ClashGroup("Detected Clashes", [item.id for item in self.results]))

    def add_result(self, result):
        """Store one clash result."""

        if result not in self.results:
            self.results.append(result)
            self.statistics = ClashStatistics.from_results(self.results)

        return result

    def remove_result(self, result):
        """Remove one clash result."""

        target = self.get_result(result)

        if target is None:
            return False

        self.results.remove(target)
        if self.current_result_id == target.id:
            self.current_result_id = self.results[0].id if self.results else None
        self.statistics = ClashStatistics.from_results(self.results)

        return True

    def visible_results(self):
        """Return visible clash results."""

        if not self.settings.visible:
            return []

        return [
            result for result in self.results
            if getattr(result, "visible", True)
        ]

    def get_result(self, result):
        """Return result by object or id."""

        if isinstance(result, ClashResult):
            return result if result in self.results else None

        for item in self.results:
            if item.id == result or item.name == result:
                return item

        return None

    def current_result(self):
        """Return the currently focused clash result."""

        return self.get_result(self.current_result_id)

    def open_result(self, result):
        """Set the active clash and return it."""

        target = self.get_result(result)

        if target is not None:
            self.current_result_id = target.id

        return target

    def next_result(self):
        """Focus the next clash result."""

        return self._step_result(1)

    def previous_result(self):
        """Focus the previous clash result."""

        return self._step_result(-1)

    def update_review(self, result, updates):
        """Apply review metadata to one clash result."""

        target = self.get_result(result)

        if target is None:
            return None

        for key, value in updates.items():
            if hasattr(target, key):
                setattr(target, key, value)

        target.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "updates": dict(updates),
        })
        self.statistics = ClashStatistics.from_results(self.results)

        return target

    def assign(self, result, updates):
        """Apply assignment metadata to one clash result."""

        return self.update_review(result, updates)

    def assign_many(self, results, updates):
        """Apply assignment metadata to multiple clash results."""

        updated = []

        for result in results:
            target = self.assign(result, updates)

            if target is not None:
                updated.append(target)

        return updated

    def dashboard_summary(self):
        """Return production dashboard summaries for clash coordination."""

        return {
            "overall": self._count_by(lambda item: "Total"),
            "severity": self._count_by(lambda item: item.severity),
            "status": self._count_by(lambda item: item.status),
            "assigned": self._count_by(lambda item: item.assigned_reviewer or "Unassigned"),
            "resolved": self._count_by(lambda item: "Resolved" if item.status == "Resolved" else "Open"),
            "open": self._count_by(lambda item: item.status if item.status != "Resolved" else "Resolved"),
            "discipline": self._count_by(lambda item: item.discipline or "Unassigned"),
            "reference": self._count_by(lambda item: item.entity_a_name or item.entity_b_name or "Unknown"),
            "recent": self.recent_activity(),
        }

    def analytics_summary(self, workspace=None):
        """Return clash analytics without changing detection results."""

        total = len(self.results)
        assigned = len([item for item in self.results if item.assigned_reviewer or item.owner])
        reviewed = len([item for item in self.results if item.status in ("In Review", "Resolved")])
        resolved = len([item for item in self.results if item.status == "Resolved"])

        return {
            "trends": self.historical_snapshots(),
            "severity_distribution": self._count_by(lambda item: item.severity),
            "discipline_statistics": self._count_by(lambda item: item.discipline or "Unassigned"),
            "reference_statistics": self._count_by(lambda item: item.entity_a_name or item.entity_b_name or "Unknown"),
            "resolution_statistics": self._count_by(lambda item: item.resolution_category or "Unassigned"),
            "review_progress": {
                "total": total,
                "review_queue": len([item for item in self.results if item.review_queue]),
                "reviewed": reviewed,
                "coverage": _percent(assigned, total),
            },
            "open_vs_closed": {"Open": total - resolved, "Closed": resolved},
            "issue_summary": self._issue_summary(workspace),
            "review_summary": self._review_summary(workspace),
        }

    def kpi_summary(self, workspace=None):
        """Return coordination KPI values for the dashboard."""

        total = len(self.results)
        resolved = len([item for item in self.results if item.status == "Resolved"])
        assigned = len([item for item in self.results if item.assigned_reviewer or item.owner])
        critical = len([item for item in self.results if item.severity == "Critical" or item.priority == "Critical"])
        clearance = [item for item in self.results if item.clash_type == "Clearance Clash"]
        issue_summary = self._issue_summary(workspace)
        completion = _percent(resolved, total)

        return {
            "project_health_score": max(0.0, min(100.0, completion - critical * 5.0)),
            "completion_percentage": completion,
            "review_coverage": _percent(assigned, total),
            "outstanding_issues": issue_summary.get("Open", 0) + issue_summary.get("In Progress", 0),
            "resolved_issues": issue_summary.get("Resolved", 0),
            "critical_clash_count": critical,
            "clearance_statistics": {
                "count": len(clearance),
                "resolved": len([item for item in clearance if item.status == "Resolved"]),
            },
            "reference_health": self._reference_health(workspace),
            "coordination_summary": {
                "total": total,
                "resolved": resolved,
                "open": total - resolved,
                "assigned": assigned,
            },
        }

    def historical_snapshots(self):
        """Return current and historical clash trend snapshots."""

        snapshots = []

        for result in self.results:
            snapshots.append({
                "timestamp": "Current",
                "clash": result.name,
                "status": result.status,
                "severity": result.severity,
            })
            for entry in result.history:
                snapshots.append({
                    "timestamp": entry.get("timestamp", ""),
                    "clash": result.name,
                    "status": entry.get("updates", {}).get("status", result.status),
                    "severity": result.severity,
                })

        return snapshots

    def recent_activity(self, limit=8):
        """Return recent clash history entries."""

        activity = []

        for result in self.results:
            for entry in result.history:
                activity.append({
                    "clash": result.name,
                    "timestamp": entry.get("timestamp", ""),
                    "updates": entry.get("updates", {}),
                })

        activity.sort(key=lambda item: item["timestamp"], reverse=True)

        return activity[:limit]

    def save_dashboard_filter(self, name, filters):
        """Persist a named dashboard filter."""

        clean = str(name or "").strip()

        if clean:
            self.dashboard_state.setdefault("saved_filters", {})[clean] = dict(filters)

        return clean

    def save_dashboard_layout(self, name, layout):
        """Persist a named dashboard layout."""

        clean = str(name or "").strip()

        if clean:
            self.dashboard_state.setdefault("saved_layouts", {})[clean] = dict(layout)

        return clean

    def save_analytics_view(self, name, view):
        """Persist a named analytics view."""

        clean = str(name or "").strip()

        if clean:
            self.saved_analytics_views[clean] = dict(view)

        return clean

    def link_issue(self, clash, issue):
        """Link a clash to an issue by id."""

        target = self.get_result(clash)

        if target is None:
            return None

        target.linked_issue_id = getattr(issue, "id", issue) or ""
        self.update_review(target, {"linked_issue_id": target.linked_issue_id})

        return target

    def link_review(self, clash, review):
        """Link a clash to a review item by id."""

        target = self.get_result(clash)

        if target is None:
            return None

        target.linked_review_id = getattr(review, "id", review) or ""
        self.update_review(target, {"linked_review_id": target.linked_review_id})

        return target

    def related_clashes(self, clash):
        """Return clashes related by issue, review, discipline or reference."""

        target = self.get_result(clash)

        if target is None:
            return []

        return [
            item for item in self.results
            if item is not target and (
                (target.linked_issue_id and item.linked_issue_id == target.linked_issue_id) or
                (target.linked_review_id and item.linked_review_id == target.linked_review_id) or
                (target.discipline and item.discipline == target.discipline) or
                (target.entity_a_name and item.entity_a_name == target.entity_a_name)
            )
        ]

    def report_template(self, name):
        """Return a report template by name."""

        return self.report_templates.get(name) or self.report_templates.get("Detailed Report")

    def filtered_results(self, search="", status="All", severity="All", group="All"):
        """Return clash results matching review-panel filters."""

        query = str(search or "").strip().lower()
        matched = list(self.results)

        if query:
            matched = [
                result for result in matched
                if query in " ".join([
                    result.name,
                    result.clash_type,
                    result.entity_a_name,
                    result.entity_b_name,
                    result.description,
                    result.comments,
                    result.assigned_reviewer,
                ]).lower()
            ]

        if status != "All":
            matched = [result for result in matched if result.status == status]

        if severity != "All":
            matched = [result for result in matched if result.severity == severity]

        if group != "All":
            group_item = self.get_group(group)
            if group_item is not None:
                allowed = set(group_item.result_ids)
                matched = [result for result in matched if result.id in allowed]

        return matched

    def sorted_results(self, results, sort_by="Severity"):
        """Return clash results sorted for UI and reports."""

        priority = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

        if sort_by == "Status":
            return sorted(results, key=lambda item: (item.status, item.name))
        if sort_by == "Reviewer":
            return sorted(results, key=lambda item: (item.assigned_reviewer, item.name))
        if sort_by == "Type":
            return sorted(results, key=lambda item: (item.clash_type, item.name))
        if sort_by == "Name":
            return sorted(results, key=lambda item: item.name)

        return sorted(results, key=lambda item: (priority.get(item.severity, 2), item.name))

    def grouped_results(self, results, group_by="Severity"):
        """Return grouped clash results for reports and tree views."""

        grouped = {}

        for result in results:
            key = self._group_key(result, group_by)
            grouped.setdefault(key, []).append(result)

        return grouped

    def get_group(self, group):
        """Return a clash group by object, id or name."""

        if isinstance(group, ClashGroup):
            return group if group in self.groups else None

        for item in self.groups:
            if item.id == group or item.name == group:
                return item

        return None

    def to_dict(self):
        """Return JSON-safe clash manager data."""

        return {
            "settings": self.settings.to_dict(),
            "statistics": self.statistics.to_dict(),
            "results": [result.to_dict() for result in self.results],
            "groups": [group.to_dict() for group in self.groups],
            "current_result_id": self.current_result_id,
            "dock_state": dict(self.dock_state),
            "report_settings": dict(self.report_settings),
            "dashboard_state": dict(self.dashboard_state),
            "report_templates": dict(self.report_templates),
            "analytics_settings": dict(self.analytics_settings),
            "saved_analytics_views": dict(self.saved_analytics_views),
            "kpi_configuration": dict(self.kpi_configuration),
        }

    def from_dict(self, data):
        """Restore clash manager data."""

        data = data or {}
        self.settings = ClashSettings.from_dict(data.get("settings", {}))
        self.results = [ClashResult.from_dict(item) for item in data.get("results", [])]
        self.groups = [ClashGroup.from_dict(item) for item in data.get("groups", [])]
        self.statistics = ClashStatistics.from_results(self.results)
        self.current_result_id = data.get("current_result_id")
        self.dock_state.update(data.get("dock_state", {}))
        self.report_settings.update(data.get("report_settings", {}))
        self.dashboard_state.update(data.get("dashboard_state", {}))
        self.report_templates.update(data.get("report_templates", {}))
        self.analytics_settings.update(data.get("analytics_settings", {}))
        self.saved_analytics_views.update(data.get("saved_analytics_views", {}))
        self.kpi_configuration.update(data.get("kpi_configuration", {}))

    def _step_result(self, delta):

        if not self.results:
            self.current_result_id = None
            return None

        current = self.current_result()
        index = self.results.index(current) if current in self.results else 0
        index = (index + delta) % len(self.results)
        self.current_result_id = self.results[index].id

        return self.results[index]

    def _group_key(self, result, group_by):

        if group_by == "Category":
            return result.category or "Uncategorized"
        if group_by == "Reference":
            return result.entity_a_name or result.entity_b_name or "Unknown Reference"
        if group_by == "Collection":
            return getattr(result, "collection_name", "") or "Unassigned"
        if group_by == "Status":
            return result.status
        if group_by == "Discipline":
            return result.discipline or "Unassigned"
        if group_by == "Owner":
            return result.owner or "Unassigned"

        return result.severity

    def _count_by(self, key):

        counts = {}

        for result in self.results:
            value = key(result) or "Unassigned"
            counts[value] = counts.get(value, 0) + 1

        return counts

    def _issue_summary(self, workspace):

        manager = getattr(workspace, "issue_manager", None)

        if manager is None:
            return {}

        counts = {}
        linked = {item.linked_issue_id for item in self.results if item.linked_issue_id}

        for issue in manager.issues:
            if issue.id in linked:
                counts[issue.status] = counts.get(issue.status, 0) + 1

        return counts

    def _review_summary(self, workspace):

        manager = getattr(workspace, "review_manager", None)

        if manager is None:
            return {}

        counts = {}
        linked = {item.linked_review_id for item in self.results if item.linked_review_id}

        for review in manager.items:
            if review.id in linked:
                counts[review.status] = counts.get(review.status, 0) + 1

        return counts

    def _reference_health(self, workspace):

        manager = getattr(workspace, "reference_manager", None)

        if manager is None:
            return {"loaded": 0, "total": 0, "health": 0.0}

        models = list(getattr(manager, "models", []))
        total = len(models)
        loaded = len([model for model in models if getattr(model, "status", "") == "Loaded"])

        return {"loaded": loaded, "total": total, "health": _percent(loaded, total)}

    def _default_report_templates(self):

        return {
            "Executive Report": {
                "name": "Executive Report",
                "group_by": "Severity",
                "detail": "summary",
                "include_comments": False,
            },
            "Coordination Report": {
                "name": "Coordination Report",
                "group_by": "Status",
                "detail": "detailed",
                "include_comments": True,
            },
            "Discipline Report": {
                "name": "Discipline Report",
                "group_by": "Discipline",
                "detail": "detailed",
                "include_comments": True,
            },
            "Summary Report": {
                "name": "Summary Report",
                "group_by": "Severity",
                "detail": "summary",
                "include_comments": False,
            },
            "Detailed Report": {
                "name": "Detailed Report",
                "group_by": "Severity",
                "detail": "detailed",
                "include_comments": True,
            },
        }

    def _candidates(self, workspace, settings):

        candidates = []

        if settings.include_references:
            candidates.extend(workspace.visible_references())

        if settings.include_native:
            candidates.extend(workspace.visible_3d_entities())

        if settings.selection_only:
            selected = set(getattr(workspace.selection, "selected", []))
            candidates = [item for item in candidates if item in selected]

        return [
            item for item in candidates
            if self._passes_filters(workspace, item, settings)
        ]

    def _passes_filters(self, workspace, entity, settings):

        if settings.layer_filter:
            layer_name = getattr(entity, "layer_name", "") or ""

            if settings.layer_filter != layer_name:
                return False

        if settings.category_filter:
            model = workspace.reference_manager.get_model(getattr(entity, "model_id", None))
            category = getattr(model, "category", "") if model is not None else getattr(entity, "category", "")

            if settings.category_filter != category:
                return False

        if settings.collection_filter:
            collection = workspace.scene_collection_manager.entity_collection(entity)
            name = getattr(collection, "name", "")

            if settings.collection_filter != name:
                return False

        return True

    def _detect_pair(self, first, second, settings):

        first_box = getattr(first, "bounding_box3d", BoundingBox3D())
        second_box = getattr(second, "bounding_box3d", BoundingBox3D())

        if not first_box.valid or not second_box.valid:
            return None

        if not _boxes_touch(first_box, second_box, settings.clearance):
            return None

        bounds = _combined_box(first_box, second_box)
        clash_type = self._clash_type(first, second, first_box, second_box, settings)

        return ClashResult(
            clash_type,
            first,
            second,
            bounds.center,
            bounds,
            description=f"{clash_type}: {_entity_name(first)} vs {_entity_name(second)}",
        )

    def _clash_type(self, first, second, first_box, second_box, settings):

        first_ref = getattr(first, "is_reference", False)
        second_ref = getattr(second, "is_reference", False)

        if first_ref or second_ref:
            return "Reference Clash"

        if _same_box(first_box, second_box):
            return "Duplicate Geometry"

        if settings.clearance > 0.0:
            return "Clearance Clash"

        return "Hard Clash"


def _boxes_touch(first, second, clearance=0.0):

    return (
        first.min.x <= second.max.x + clearance and
        first.max.x + clearance >= second.min.x and
        first.min.y <= second.max.y + clearance and
        first.max.y + clearance >= second.min.y and
        first.min.z <= second.max.z + clearance and
        first.max.z + clearance >= second.min.z
    )


def _same_box(first, second):

    return (
        first.min.distance_to(second.min) <= 1e-6 and
        first.max.distance_to(second.max) <= 1e-6
    )


def _combined_box(first, second):

    box = BoundingBox3D()

    for point in first.corners() + second.corners():
        box.add(point)

    return box


def _entity_name(entity):

    return getattr(entity, "name", None) or getattr(entity, "type_name", "Entity")


def _percent(value, total):

    if not total:
        return 100.0

    return round((float(value) / float(total)) * 100.0, 2)


def _vector_to_data(vector):

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def _vector_from_data(data):

    data = data or {}

    return Vector3(data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))


def _box_to_data(box):

    return {
        "valid": box.valid,
        "min": _vector_to_data(box.min),
        "max": _vector_to_data(box.max),
    }


def _box_from_data(data):

    data = data or {}
    box = BoundingBox3D()

    if data.get("valid", False):
        box.add(_vector_from_data(data.get("min")))
        box.add(_vector_from_data(data.get("max")))

    return box
