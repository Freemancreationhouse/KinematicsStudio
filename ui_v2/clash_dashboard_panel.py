from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.commands import (
    LinkClashIssueCommand,
    LinkClashReviewCommand,
    SaveClashAnalyticsViewCommand,
    SaveClashDashboardFilterCommand,
    SaveClashDashboardLayoutCommand,
    UpdateClashAssignmentCommand,
    UpdateClashKPIConfigurationCommand,
    UpdateClashReportSettingsCommand,
    UpdateClashReportTemplateCommand,
)
from engine.export import ClashReportGenerator


class ClashDashboardPanel(QWidget):
    """Production coordination dashboard for existing clash results."""

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self.report_generator = ClashReportGenerator()
        self._refreshing = False
        self._build()
        self.refresh()

    # --------------------------------

    def _build(self):

        layout = QVBoxLayout(self)
        self.overall = QLabel("")
        self.open_summary = QLabel("")
        self.resolved_summary = QLabel("")
        self.health_score = QLabel("")
        self.completion = QLabel("")
        self.review_coverage = QLabel("")
        self.issue_summary = QLabel("")
        layout.addWidget(self.overall)
        layout.addWidget(self.open_summary)
        layout.addWidget(self.resolved_summary)
        layout.addWidget(self.health_score)
        layout.addWidget(self.completion)
        layout.addWidget(self.review_coverage)
        layout.addWidget(self.issue_summary)

        filters = QHBoxLayout()
        self.dashboard_filter = QComboBox()
        self.dashboard_filter.addItem("All")
        self.save_filter_button = QPushButton("Save Filter")
        self.save_layout_button = QPushButton("Save Layout")
        self.save_analytics_button = QPushButton("Save Analytics View")
        filters.addWidget(QLabel("Saved Filter"))
        filters.addWidget(self.dashboard_filter)
        filters.addWidget(self.save_filter_button)
        filters.addWidget(self.save_layout_button)
        filters.addWidget(self.save_analytics_button)
        layout.addLayout(filters)

        self.summary_tree = QTreeWidget()
        self.summary_tree.setColumnCount(2)
        self.summary_tree.setHeaderLabels(["Summary", "Count"])
        layout.addWidget(self.summary_tree)

        self.analytics_tree = QTreeWidget()
        self.analytics_tree.setColumnCount(2)
        self.analytics_tree.setHeaderLabels(["Analytics / KPI", "Value"])
        layout.addWidget(self.analytics_tree)

        assignment = QFormLayout()
        self.owner = QLineEdit()
        self.due_date = QLineEdit()
        self.priority = QComboBox()
        self.priority.addItems(["Low", "Normal", "High", "Critical"])
        self.status = QComboBox()
        self.status.addItems(["Open", "In Review", "Resolved", "Ignored"])
        self.resolution_category = QLineEdit()
        self.approval_state = QComboBox()
        self.approval_state.addItems(["Pending", "Approved", "Rejected", "Needs Work"])
        self.discipline = QLineEdit()
        self.watch_list = QCheckBox("Watch")
        self.review_queue = QCheckBox("Queue")
        assignment.addRow("Owner", self.owner)
        assignment.addRow("Due Date", self.due_date)
        assignment.addRow("Priority", self.priority)
        assignment.addRow("Status", self.status)
        assignment.addRow("Resolution Category", self.resolution_category)
        assignment.addRow("Approval State", self.approval_state)
        assignment.addRow("Discipline", self.discipline)
        assignment.addRow("Watch List", self.watch_list)
        assignment.addRow("Review Queue", self.review_queue)
        layout.addLayout(assignment)

        assign_actions = QHBoxLayout()
        self.assign_button = QPushButton("Assign Clash")
        self.reassign_button = QPushButton("Reassign Clash")
        self.batch_assign_button = QPushButton("Batch Assignment")
        assign_actions.addWidget(self.assign_button)
        assign_actions.addWidget(self.reassign_button)
        assign_actions.addWidget(self.batch_assign_button)
        layout.addLayout(assign_actions)

        link_actions = QHBoxLayout()
        self.link_issue_button = QPushButton("Link Issue")
        self.link_review_button = QPushButton("Link Review")
        self.issue_nav_button = QPushButton("Issue Navigation")
        self.review_nav_button = QPushButton("Review Navigation")
        self.related_nav_button = QPushButton("Related Clashes")
        link_actions.addWidget(self.link_issue_button)
        link_actions.addWidget(self.link_review_button)
        link_actions.addWidget(self.issue_nav_button)
        link_actions.addWidget(self.review_nav_button)
        link_actions.addWidget(self.related_nav_button)
        layout.addLayout(link_actions)

        report_layout = QHBoxLayout()
        self.template = QComboBox()
        self.template.addItems([
            "Executive Report",
            "Coordination Report",
            "Discipline Report",
            "Summary Report",
            "Detailed Report",
        ])
        self.scheduled = QCheckBox("Scheduled")
        self.schedule_interval = QComboBox()
        self.schedule_interval.addItems(["Daily", "Weekly", "Monthly"])
        self.save_template_button = QPushButton("Save Template")
        self.pdf_button = QPushButton("Report PDF")
        self.csv_button = QPushButton("Report CSV")
        report_layout.addWidget(QLabel("Template"))
        report_layout.addWidget(self.template)
        report_layout.addWidget(self.scheduled)
        report_layout.addWidget(self.schedule_interval)
        report_layout.addWidget(self.save_template_button)
        report_layout.addWidget(self.pdf_button)
        report_layout.addWidget(self.csv_button)
        layout.addLayout(report_layout)

        self.recent_activity = QTextEdit()
        self.recent_activity.setReadOnly(True)
        self.recent_activity.setFixedHeight(82)
        layout.addWidget(QLabel("Recent Activity"))
        layout.addWidget(self.recent_activity)

        self.dashboard_filter.currentTextChanged.connect(self._apply_saved_filter)
        self.save_filter_button.clicked.connect(self.save_dashboard_filter)
        self.save_layout_button.clicked.connect(self.save_dashboard_layout)
        self.save_analytics_button.clicked.connect(self.save_analytics_view)
        self.assign_button.clicked.connect(self.assign_clash)
        self.reassign_button.clicked.connect(self.assign_clash)
        self.batch_assign_button.clicked.connect(self.batch_assign)
        self.link_issue_button.clicked.connect(self.link_current_issue)
        self.link_review_button.clicked.connect(self.link_current_review)
        self.issue_nav_button.clicked.connect(self.navigate_issue)
        self.review_nav_button.clicked.connect(self.navigate_review)
        self.related_nav_button.clicked.connect(self.navigate_related_clash)
        self.save_template_button.clicked.connect(self.save_report_template)
        self.pdf_button.clicked.connect(lambda: self.export_report("pdf"))
        self.csv_button.clicked.connect(lambda: self.export_report("csv"))

    # --------------------------------

    def refresh(self):
        """Refresh dashboard summaries and controls."""

        if self._refreshing:
            return

        self._refreshing = True
        manager = self.workspace.clash_manager
        summary = manager.dashboard_summary()
        analytics = manager.analytics_summary(self.workspace)
        kpis = manager.kpi_summary(self.workspace)
        stats = manager.statistics
        self.overall.setText(f"Overall: {stats.total} clashes")
        self.open_summary.setText(f"Open Summary: {stats.unresolved} unresolved")
        self.resolved_summary.setText(
            f"Resolved Summary: {summary['resolved'].get('Resolved', 0)} resolved"
        )
        self.health_score.setText(f"Project Health Score: {kpis['project_health_score']:.2f}")
        self.completion.setText(f"Completion: {kpis['completion_percentage']:.2f}%")
        self.review_coverage.setText(f"Review Coverage: {kpis['review_coverage']:.2f}%")
        self.issue_summary.setText(
            f"Issues: {kpis['outstanding_issues']} outstanding / {kpis['resolved_issues']} resolved"
        )
        self._refresh_filters()
        self._refresh_summary_tree(summary)
        self._refresh_analytics_tree(analytics, kpis)
        self._refresh_recent(summary["recent"])
        self._load_report_settings()
        self._refreshing = False

    # --------------------------------

    def assign_clash(self):
        """Assign or reassign the current clash through the Command System."""

        result = self.workspace.clash_manager.current_result()

        if result is None:
            return None

        self._execute_assignment([result])

        return result

    # --------------------------------

    def batch_assign(self):
        """Assign all filtered or selected clashes through one command."""

        selected = [
            item for item in self.workspace.selection.selected
            if getattr(item, "is_clash", False)
        ]
        targets = selected or list(self.workspace.clash_manager.results)

        if not targets:
            return []

        self._execute_assignment(targets)

        return targets

    # --------------------------------

    def link_current_issue(self, issue=None):
        """Link the current clash to an existing issue."""

        clash = self.workspace.clash_manager.current_result()
        target_issue = issue or self._first_issue()

        if clash is None or target_issue is None:
            return None

        self.workspace.command_manager.execute(
            LinkClashIssueCommand(self.workspace, clash, target_issue)
        )
        self._changed()

        return target_issue

    # --------------------------------

    def link_current_review(self, review=None):
        """Link the current clash to an existing review item."""

        clash = self.workspace.clash_manager.current_result()
        target_review = review or self._first_review()

        if clash is None or target_review is None:
            return None

        self.workspace.command_manager.execute(
            LinkClashReviewCommand(self.workspace, clash, target_review)
        )
        self._changed()

        return target_review

    # --------------------------------

    def navigate_issue(self):
        """Select the issue linked to the current clash."""

        clash = self.workspace.clash_manager.current_result()

        if clash is None:
            return None

        issue = self.workspace.issue_manager.get(clash.linked_issue_id)

        if issue is not None:
            self.workspace.selection.select(issue)
            self._changed()

        return issue

    # --------------------------------

    def navigate_review(self):
        """Return the review item linked to the current clash."""

        clash = self.workspace.clash_manager.current_result()

        if clash is None:
            return None

        review = self.workspace.review_manager.get(clash.linked_review_id)
        self._changed()

        return review

    # --------------------------------

    def navigate_related_clash(self):
        """Focus the first related clash."""

        clash = self.workspace.clash_manager.current_result()
        related = self.workspace.clash_manager.related_clashes(clash)

        if related:
            self.workspace.clash_manager.open_result(related[0])
            self.workspace.selection.select(related[0])
            self._changed()
            return related[0]

        return None

    # --------------------------------

    def save_dashboard_filter(self, name=None):
        """Save dashboard filter settings through the Command System."""

        chosen = name

        if chosen is None:
            chosen, ok = QInputDialog.getText(self, "Save Dashboard Filter", "Filter name")

            if not ok:
                return None

        filters = {
            "status": self.status.currentText(),
            "priority": self.priority.currentText(),
            "owner": self.owner.text(),
            "discipline": self.discipline.text(),
        }
        self.workspace.command_manager.execute(
            SaveClashDashboardFilterCommand(self.workspace, chosen, filters)
        )
        self._changed()

        return chosen

    # --------------------------------

    def save_dashboard_layout(self, name=None):
        """Save dashboard layout metadata through the Command System."""

        chosen = name

        if chosen is None:
            chosen, ok = QInputDialog.getText(self, "Save Dashboard Layout", "Layout name")

            if not ok:
                return None

        layout = {
            "layout": self.workspace.clash_manager.dashboard_state.get("layout", "Summary"),
            "filter": self.dashboard_filter.currentText(),
            "template": self.template.currentText(),
        }
        self.workspace.command_manager.execute(
            SaveClashDashboardLayoutCommand(self.workspace, chosen, layout)
        )
        self._changed()

        return chosen

    # --------------------------------

    def save_analytics_view(self, name=None):
        """Save analytics view metadata through the Command System."""

        chosen = name

        if chosen is None:
            chosen, ok = QInputDialog.getText(self, "Save Analytics View", "View name")

            if not ok:
                return None

        view = {
            "trend_window": self.workspace.clash_manager.analytics_settings.get("trend_window", "All"),
            "show_resolved": self.workspace.clash_manager.analytics_settings.get("show_resolved", True),
            "template": self.template.currentText(),
        }
        self.workspace.command_manager.execute(
            SaveClashAnalyticsViewCommand(self.workspace, chosen, view)
        )
        self._changed()

        return chosen

    # --------------------------------

    def save_report_template(self):
        """Save the selected report template settings."""

        name = self.template.currentText()
        template = {
            "name": name,
            "group_by": "Discipline" if name == "Discipline Report" else "Severity",
            "detail": "summary" if name in ("Executive Report", "Summary Report") else "detailed",
            "include_comments": name not in ("Executive Report", "Summary Report"),
        }
        self.workspace.command_manager.execute(
            UpdateClashReportTemplateCommand(self.workspace, name, template)
        )
        self.workspace.command_manager.execute(UpdateClashReportSettingsCommand(self.workspace, {
            "template": name,
            "scheduled_enabled": self.scheduled.isChecked(),
            "scheduled_interval": self.schedule_interval.currentText(),
        }))
        self._changed()

        return template

    # --------------------------------

    def export_report(self, format_name, path=None):
        """Export a clash report using the selected template."""

        target = path or self._report_path(format_name)

        if not target:
            return None

        self.save_report_template()
        self.workspace.command_manager.execute(UpdateClashReportSettingsCommand(self.workspace, {
            "last_format": format_name.upper(),
            "template": self.template.currentText(),
        }))

        return self.report_generator.export(
            self.workspace,
            target,
            format_name,
            self.workspace.clash_manager.results,
            template_name=self.template.currentText(),
        )

    # --------------------------------

    def _execute_assignment(self, targets):

        before = [self._assignment_state(result) for result in targets]
        after = {
            "owner": self.owner.text(),
            "due_date": self.due_date.text(),
            "priority": self.priority.currentText(),
            "status": self.status.currentText(),
            "resolution_category": self.resolution_category.text(),
            "approval_state": self.approval_state.currentText(),
            "discipline": self.discipline.text(),
            "watch_list": self.watch_list.isChecked(),
            "review_queue": self.review_queue.isChecked(),
        }
        self.workspace.command_manager.execute(
            UpdateClashAssignmentCommand(self.workspace, targets, before, after)
        )
        self._changed()

    def _assignment_state(self, result):

        return {
            "owner": result.owner,
            "due_date": result.due_date,
            "priority": result.priority,
            "status": result.status,
            "resolution_category": result.resolution_category,
            "approval_state": result.approval_state,
            "discipline": result.discipline,
            "watch_list": result.watch_list,
            "review_queue": result.review_queue,
        }

    def _refresh_summary_tree(self, summary):

        self.summary_tree.clear()

        for section in (
            "severity",
            "status",
            "assigned",
            "resolved",
            "open",
            "discipline",
            "reference",
        ):
            parent = QTreeWidgetItem([section.replace("_", " ").title(), ""])
            self.summary_tree.addTopLevelItem(parent)

            for name, count in sorted(summary[section].items()):
                parent.addChild(QTreeWidgetItem([str(name), str(count)]))

            parent.setExpanded(True)

        self.summary_tree.resizeColumnToContents(0)

    def _refresh_analytics_tree(self, analytics, kpis):

        self.analytics_tree.clear()

        sections = {
            "Severity Distribution": analytics["severity_distribution"],
            "Discipline Statistics": analytics["discipline_statistics"],
            "Reference Statistics": analytics["reference_statistics"],
            "Resolution Statistics": analytics["resolution_statistics"],
            "Open vs Closed": analytics["open_vs_closed"],
            "Issue Summary": analytics["issue_summary"],
            "Review Summary": analytics["review_summary"],
            "Coordination KPIs": {
                "Project Health": kpis["project_health_score"],
                "Completion": kpis["completion_percentage"],
                "Review Coverage": kpis["review_coverage"],
                "Critical Clashes": kpis["critical_clash_count"],
                "Outstanding Issues": kpis["outstanding_issues"],
                "Resolved Issues": kpis["resolved_issues"],
                "Reference Health": kpis["reference_health"].get("health", 0.0),
            },
        }

        for section, values in sections.items():
            parent = QTreeWidgetItem([section, ""])
            self.analytics_tree.addTopLevelItem(parent)

            for name, value in sorted(values.items()):
                parent.addChild(QTreeWidgetItem([str(name), str(value)]))

            parent.setExpanded(True)

        trend_parent = QTreeWidgetItem(["Clash Trends", str(len(analytics["trends"]))])
        self.analytics_tree.addTopLevelItem(trend_parent)
        trend_parent.setExpanded(True)
        self.analytics_tree.resizeColumnToContents(0)

    def _refresh_recent(self, recent):

        lines = []

        for item in recent:
            updates = ", ".join(sorted(item["updates"].keys()))
            lines.append(f"{item['timestamp']}  {item['clash']}  {updates}")

        self.recent_activity.setPlainText("\n".join(lines))

    def _refresh_filters(self):

        current = self.dashboard_filter.currentText()
        self.dashboard_filter.blockSignals(True)
        self.dashboard_filter.clear()
        self.dashboard_filter.addItem("All")

        for name in sorted(self.workspace.clash_manager.dashboard_state.get("saved_filters", {})):
            self.dashboard_filter.addItem(name)

        self.dashboard_filter.setCurrentText(current or "All")
        self.dashboard_filter.blockSignals(False)

    def _first_issue(self):

        issues = getattr(self.workspace.issue_manager, "issues", [])

        return issues[0] if issues else None

    def _first_review(self):

        reviews = getattr(self.workspace.review_manager, "items", [])

        return reviews[0] if reviews else None

    def _apply_saved_filter(self, name):

        if self._refreshing or name == "All":
            return

        filters = self.workspace.clash_manager.dashboard_state.get("saved_filters", {}).get(name, {})
        self.status.setCurrentText(filters.get("status", "Open"))
        self.priority.setCurrentText(filters.get("priority", "Normal"))
        self.owner.setText(filters.get("owner", ""))
        self.discipline.setText(filters.get("discipline", ""))

    def _load_report_settings(self):

        settings = self.workspace.clash_manager.report_settings
        self.template.setCurrentText(settings.get("template", "Detailed Report"))
        self.scheduled.setChecked(bool(settings.get("scheduled_enabled", False)))
        self.schedule_interval.setCurrentText(settings.get("scheduled_interval", "Weekly"))

    def _report_path(self, format_name):

        extension = format_name.lower()
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {extension.upper()} Clash Dashboard Report",
            f"clash_dashboard_report.{extension}",
            f"{extension.upper()} Files (*.{extension})",
        )

        return path

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
