from engine.clashes import ClashStatistics
from engine.commands.command import Command


class RunClashDetectionCommand(Command):
    """Undoable command for replacing clash results with a detection run."""

    def __init__(self, workspace, settings=None):

        self.workspace = workspace
        self.settings = settings
        self.before = list(workspace.clash_manager.results)
        self.before_settings = workspace.clash_manager.settings
        self.after = None

    def execute(self):
        """Run clash detection."""

        if self.settings is not None:
            self.workspace.clash_manager.settings = self.settings

        if self.after is None:
            self.after = self.workspace.clash_manager.detect(
                self.workspace,
                self.workspace.clash_manager.settings,
            )

        self.workspace.clash_manager.set_results(self.after)
        for result in self.workspace.clash_manager.results:
            self.workspace.assign_layer(result)

    def undo(self):
        """Restore previous clash results."""

        self.workspace.clash_manager.settings = self.before_settings
        self.workspace.clash_manager.set_results(self.before)
        for result in self.workspace.clash_manager.results:
            self.workspace.assign_layer(result)


class AddClashResultCommand(Command):
    """Undoable command for adding one clash result."""

    def __init__(self, workspace, result):

        self.workspace = workspace
        self.result = result

    def execute(self):
        """Add the clash result."""

        self.workspace.clash_manager.add_result(self.result)
        self.workspace.assign_layer(self.result)

    def undo(self):
        """Remove the clash result."""

        self.workspace.clash_manager.remove_result(self.result)
        self.workspace.selection.unregister_entity(self.result)
        self.workspace.unregister_layer_entity(self.result)


class RemoveClashResultCommand(Command):
    """Undoable command for removing one clash result."""

    def __init__(self, workspace, result):

        self.workspace = workspace
        self.result = result

    def execute(self):
        """Remove the clash result."""

        self.workspace.clash_manager.remove_result(self.result)
        self.workspace.selection.unregister_entity(self.result)
        self.workspace.unregister_layer_entity(self.result)

    def undo(self):
        """Restore the clash result."""

        self.workspace.clash_manager.add_result(self.result)
        self.workspace.assign_layer(self.result)


class UpdateClashSettingsCommand(Command):
    """Undoable command for updating clash detection settings."""

    def __init__(self, workspace, before, after):

        self.workspace = workspace
        self.before = before
        self.after = after

    def execute(self):
        """Apply clash settings."""

        self.workspace.clash_manager.settings = self.after

    def undo(self):
        """Restore clash settings."""

        self.workspace.clash_manager.settings = self.before


class UpdateClashReviewCommand(Command):
    """Undoable command for editing clash review metadata."""

    def __init__(self, workspace, result, before, after):

        self.workspace = workspace
        self.result = result
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply review metadata."""

        self.workspace.clash_manager.update_review(self.result, self.after)

    def undo(self):
        """Restore previous review metadata."""

        target = self.workspace.clash_manager.get_result(self.result)

        if target is None:
            return

        for key, value in self.before.items():
            if hasattr(target, key):
                setattr(target, key, value)

        self.workspace.clash_manager.statistics = ClashStatistics.from_results(
            self.workspace.clash_manager.results
        )


class UpdateClashAssignmentCommand(Command):
    """Undoable command for assigning one or more clash results."""

    def __init__(self, workspace, results, before, after):

        self.workspace = workspace
        self.results = list(results)
        self.before = [dict(item) for item in before]
        self.after = dict(after)

    def execute(self):
        """Apply assignment metadata."""

        self.workspace.clash_manager.assign_many(self.results, self.after)

    def undo(self):
        """Restore previous assignment metadata."""

        for result, state in zip(self.results, self.before):
            target = self.workspace.clash_manager.get_result(result)

            if target is None:
                continue

            for key, value in state.items():
                if hasattr(target, key):
                    setattr(target, key, value)

        self.workspace.clash_manager.statistics = ClashStatistics.from_results(
            self.workspace.clash_manager.results
        )


class SaveClashDashboardFilterCommand(Command):
    """Undoable command for saving dashboard filter presets."""

    def __init__(self, workspace, name, filters):

        self.workspace = workspace
        self.filter_name = name
        self.filters = dict(filters)
        self.before = dict(workspace.clash_manager.dashboard_state.get("saved_filters", {}))

    def execute(self):
        """Save the dashboard filter."""

        self.workspace.clash_manager.save_dashboard_filter(self.filter_name, self.filters)

    def undo(self):
        """Restore previous dashboard filters."""

        self.workspace.clash_manager.dashboard_state["saved_filters"] = dict(self.before)


class UpdateClashReportTemplateCommand(Command):
    """Undoable command for adding or updating a clash report template."""

    def __init__(self, workspace, name, template):

        self.workspace = workspace
        self.template_name = name
        self.template = dict(template)
        self.before = workspace.clash_manager.report_templates.get(name)

    def execute(self):
        """Store the report template."""

        self.workspace.clash_manager.report_templates[self.template_name] = dict(self.template)

    def undo(self):
        """Restore previous report template state."""

        if self.before is None:
            self.workspace.clash_manager.report_templates.pop(self.template_name, None)
        else:
            self.workspace.clash_manager.report_templates[self.template_name] = dict(self.before)


class UpdateClashReportSettingsCommand(Command):
    """Undoable command for updating clash report preferences."""

    def __init__(self, workspace, after):

        self.workspace = workspace
        self.before = dict(workspace.clash_manager.report_settings)
        self.after = dict(after)

    def execute(self):
        """Apply report preferences."""

        self.workspace.clash_manager.report_settings.update(self.after)

    def undo(self):
        """Restore previous report preferences."""

        self.workspace.clash_manager.report_settings = dict(self.before)


class LinkClashIssueCommand(Command):
    """Undoable command for linking a clash to an issue."""

    def __init__(self, workspace, clash, issue):

        self.workspace = workspace
        self.clash = clash
        self.issue = issue
        target = workspace.clash_manager.get_result(clash)
        issue_target = workspace.issue_manager.get(issue) if issue is not None else None
        self.before_clash = getattr(target, "linked_issue_id", "")
        self.before_issue = getattr(issue_target, "linked_entity", None)

    def execute(self):
        """Link clash and issue metadata."""

        target = self.workspace.clash_manager.link_issue(self.clash, self.issue)
        issue = self.workspace.issue_manager.get(self.issue)

        if target is not None and issue is not None:
            issue.linked_entity = target.id
            if target.status == "Resolved":
                issue.status = "Resolved"
            issue.touch()

    def undo(self):
        """Restore previous issue link metadata."""

        target = self.workspace.clash_manager.get_result(self.clash)
        issue = self.workspace.issue_manager.get(self.issue)

        if target is not None:
            target.linked_issue_id = self.before_clash

        if issue is not None:
            issue.linked_entity = self.before_issue
            issue.touch()


class LinkClashReviewCommand(Command):
    """Undoable command for linking a clash to a review item."""

    def __init__(self, workspace, clash, review):

        self.workspace = workspace
        self.clash = clash
        self.review = review
        target = workspace.clash_manager.get_result(clash)
        review_target = workspace.review_manager.get(review) if review is not None else None
        self.before_clash = getattr(target, "linked_review_id", "")
        self.before_status = getattr(review_target, "status", None)

    def execute(self):
        """Link clash and review metadata."""

        target = self.workspace.clash_manager.link_review(self.clash, self.review)
        review = self.workspace.review_manager.get(self.review)

        if target is not None and review is not None:
            review.status = target.status
            review.resolved = target.status == "Resolved"

    def undo(self):
        """Restore previous review link metadata."""

        target = self.workspace.clash_manager.get_result(self.clash)
        review = self.workspace.review_manager.get(self.review)

        if target is not None:
            target.linked_review_id = self.before_clash

        if review is not None and self.before_status is not None:
            review.status = self.before_status
            review.resolved = self.before_status == "Resolved"


class SaveClashAnalyticsViewCommand(Command):
    """Undoable command for saving analytics views."""

    def __init__(self, workspace, name, view):

        self.workspace = workspace
        self.view_name = name
        self.view = dict(view)
        self.before = dict(workspace.clash_manager.saved_analytics_views)

    def execute(self):
        """Save the analytics view."""

        self.workspace.clash_manager.save_analytics_view(self.view_name, self.view)

    def undo(self):
        """Restore previous analytics views."""

        self.workspace.clash_manager.saved_analytics_views = dict(self.before)


class SaveClashDashboardLayoutCommand(Command):
    """Undoable command for saving dashboard layouts."""

    def __init__(self, workspace, name, layout):

        self.workspace = workspace
        self.layout_name = name
        self.layout = dict(layout)
        self.before = dict(workspace.clash_manager.dashboard_state.get("saved_layouts", {}))

    def execute(self):
        """Save the dashboard layout."""

        self.workspace.clash_manager.save_dashboard_layout(self.layout_name, self.layout)

    def undo(self):
        """Restore previous dashboard layouts."""

        self.workspace.clash_manager.dashboard_state["saved_layouts"] = dict(self.before)


class UpdateClashKPIConfigurationCommand(Command):
    """Undoable command for updating KPI configuration."""

    def __init__(self, workspace, after):

        self.workspace = workspace
        self.before = dict(workspace.clash_manager.kpi_configuration)
        self.after = dict(after)

    def execute(self):
        """Apply KPI configuration."""

        self.workspace.clash_manager.kpi_configuration.update(self.after)

    def undo(self):
        """Restore previous KPI configuration."""

        self.workspace.clash_manager.kpi_configuration = dict(self.before)
