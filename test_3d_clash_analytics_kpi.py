from engine.clashes import ClashResult
from engine.commands import (
    AddClashResultCommand,
    SaveClashAnalyticsViewCommand,
    SaveClashDashboardLayoutCommand,
    UpdateClashAssignmentCommand,
    UpdateClashKPIConfigurationCommand,
)
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace


workspace = Workspace()
first = ClashResult("Hard Clash", location=Vector3())
first.name = "Analytics A"
first.severity = "Critical"
second = ClashResult("Clearance Clash", location=Vector3(1.0, 0.0, 0.0), status="Resolved")
second.name = "Analytics B"
second.severity = "Low"
workspace.command_manager.execute(AddClashResultCommand(workspace, first))
workspace.command_manager.execute(AddClashResultCommand(workspace, second))
workspace.command_manager.execute(UpdateClashAssignmentCommand(
    workspace,
    [first],
    [{
        "owner": first.owner,
        "due_date": first.due_date,
        "priority": first.priority,
        "status": first.status,
        "resolution_category": first.resolution_category,
        "approval_state": first.approval_state,
        "discipline": first.discipline,
        "watch_list": first.watch_list,
        "review_queue": first.review_queue,
    }],
    {
        "owner": "Lead",
        "due_date": "2026-09-10",
        "priority": "Critical",
        "status": "In Review",
        "resolution_category": "Reroute",
        "approval_state": "Pending",
        "discipline": "MEP",
        "watch_list": True,
        "review_queue": True,
    },
))

analytics = workspace.clash_manager.analytics_summary(workspace)
kpis = workspace.clash_manager.kpi_summary(workspace)

assert analytics["severity_distribution"]["Critical"] == 1
assert analytics["discipline_statistics"]["MEP"] == 1
assert analytics["open_vs_closed"]["Closed"] == 1
assert analytics["review_progress"]["review_queue"] == 1
assert kpis["completion_percentage"] == 50.0
assert kpis["critical_clash_count"] == 1
assert kpis["clearance_statistics"]["count"] == 1

workspace.command_manager.execute(SaveClashAnalyticsViewCommand(
    workspace,
    "Default Analytics",
    {"trend_window": "All", "show_resolved": True},
))
workspace.command_manager.execute(SaveClashDashboardLayoutCommand(
    workspace,
    "Coordination Layout",
    {"layout": "Analytics", "filter": "All"},
))
workspace.command_manager.execute(UpdateClashKPIConfigurationCommand(
    workspace,
    {"critical_weight": 5.0},
))

assert "Default Analytics" in workspace.clash_manager.saved_analytics_views
assert "Coordination Layout" in workspace.clash_manager.dashboard_state["saved_layouts"]
assert workspace.clash_manager.kpi_configuration["critical_weight"] == 5.0

workspace.command_manager.undo()
assert workspace.clash_manager.kpi_configuration["critical_weight"] == 4.0

print("3d-clash-analytics-kpi-ok")
