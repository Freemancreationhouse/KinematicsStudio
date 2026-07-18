from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
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

from engine.commands import RunClashDetectionCommand, UpdateClashReviewCommand
from engine.export import ClashReportGenerator


class ClashManagerPanel(QWidget):
    """Dockable clash manager, review workflow and report launcher."""

    COLUMNS = ["Name", "Type", "Severity", "Priority", "Status", "Reviewer"]

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self.report_generator = ClashReportGenerator()
        self._refreshing = False
        self._build()
        self._load_state()
        self.refresh()

    # --------------------------------

    def _build(self):

        layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search clashes")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Open", "In Review", "Resolved", "Ignored"])
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.group_by = QComboBox()
        self.group_by.addItems(["Severity", "Status", "Category", "Reference", "Collection"])
        self.sort_by = QComboBox()
        self.sort_by.addItems(["Severity", "Status", "Reviewer", "Type", "Name"])

        for label, widget in (
            ("Search", self.search),
            ("Status", self.status_filter),
            ("Severity", self.severity_filter),
            ("Group", self.group_by),
            ("Sort", self.sort_by),
        ):
            filter_layout.addWidget(QLabel(label))
            filter_layout.addWidget(widget)

        layout.addLayout(filter_layout)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(self.COLUMNS))
        self.tree.setHeaderLabels(self.COLUMNS)
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.tree)

        self.summary = QLabel("")
        layout.addWidget(self.summary)

        nav = QHBoxLayout()
        self.run_button = QPushButton("Run")
        self.open_button = QPushButton("Open")
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.focus_button = QPushButton("Focus Camera")
        self.zoom_button = QPushButton("Zoom To")
        self.highlight_button = QPushButton("Highlight")
        self.expand_button = QPushButton("Expand")
        self.collapse_button = QPushButton("Collapse")

        for button in (
            self.run_button,
            self.open_button,
            self.previous_button,
            self.next_button,
            self.focus_button,
            self.zoom_button,
            self.highlight_button,
            self.expand_button,
            self.collapse_button,
        ):
            nav.addWidget(button)

        layout.addLayout(nav)

        review = QHBoxLayout()
        self.status_editor = QComboBox()
        self.status_editor.addItems(["Open", "In Review", "Resolved", "Ignored"])
        self.priority_editor = QComboBox()
        self.priority_editor.addItems(["Low", "Normal", "High", "Critical"])
        self.reviewer_editor = QLineEdit()
        self.reviewer_editor.setPlaceholderText("Assigned reviewer")
        review.addWidget(QLabel("Review"))
        review.addWidget(self.status_editor)
        review.addWidget(QLabel("Priority"))
        review.addWidget(self.priority_editor)
        review.addWidget(QLabel("Reviewer"))
        review.addWidget(self.reviewer_editor)
        layout.addLayout(review)

        self.comments = QTextEdit()
        self.comments.setPlaceholderText("Comments")
        self.comments.setFixedHeight(56)
        self.resolution_notes = QTextEdit()
        self.resolution_notes.setPlaceholderText("Resolution notes")
        self.resolution_notes.setFixedHeight(56)
        layout.addWidget(self.comments)
        layout.addWidget(self.resolution_notes)

        actions = QHBoxLayout()
        self.save_review_button = QPushButton("Save Review")
        self.pdf_button = QPushButton("Export PDF")
        self.csv_button = QPushButton("Export CSV")
        actions.addWidget(self.save_review_button)
        actions.addWidget(self.pdf_button)
        actions.addWidget(self.csv_button)
        layout.addLayout(actions)

        self.search.textChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.severity_filter.currentTextChanged.connect(self.refresh)
        self.group_by.currentTextChanged.connect(self.refresh)
        self.sort_by.currentTextChanged.connect(self.refresh)
        self.run_button.clicked.connect(self.run_detection)
        self.open_button.clicked.connect(self.open_clash)
        self.previous_button.clicked.connect(self.previous_clash)
        self.next_button.clicked.connect(self.next_clash)
        self.focus_button.clicked.connect(self.focus_camera)
        self.zoom_button.clicked.connect(self.zoom_to_clash)
        self.highlight_button.clicked.connect(self.highlight_clash)
        self.expand_button.clicked.connect(self.tree.expandAll)
        self.collapse_button.clicked.connect(self.tree.collapseAll)
        self.save_review_button.clicked.connect(self.save_review)
        self.pdf_button.clicked.connect(lambda: self.export_report("pdf"))
        self.csv_button.clicked.connect(lambda: self.export_report("csv"))

    # --------------------------------

    def refresh(self):
        """Refresh tree rows and summary statistics."""

        if self._refreshing:
            return

        self._refreshing = True
        self._save_state()
        self.tree.clear()
        manager = self.workspace.clash_manager
        results = self._filtered_sorted_results()

        for group, group_results in manager.grouped_results(results, self.group_by.currentText()).items():
            parent = QTreeWidgetItem([group, "", "", "", "", ""])
            parent.setData(0, Qt.UserRole, None)
            self.tree.addTopLevelItem(parent)

            for result in group_results:
                child = QTreeWidgetItem([
                    result.name,
                    result.clash_type,
                    result.severity,
                    result.priority,
                    result.status,
                    result.assigned_reviewer,
                ])
                child.setData(0, Qt.UserRole, result.id)
                parent.addChild(child)

                if result.id == manager.current_result_id:
                    child.setSelected(True)

            parent.setExpanded(bool(manager.dock_state.get("expanded", True)))

        self.tree.resizeColumnToContents(0)
        self.summary.setText(self._summary_text(results))
        self._load_review_fields(manager.current_result())
        self._refreshing = False

    # --------------------------------

    def run_detection(self):
        """Run existing clash detection through the Command System."""

        self.workspace.command_manager.execute(RunClashDetectionCommand(self.workspace))
        self._changed()

    # --------------------------------

    def open_clash(self):
        """Open the selected clash and synchronize selection."""

        result = self.selected_clash()

        if result is None:
            return None

        self.workspace.clash_manager.open_result(result)
        self.workspace.selection.select(result)
        self._changed()

        return result

    # --------------------------------

    def previous_clash(self):
        """Move to the previous clash result."""

        result = self.workspace.clash_manager.previous_result()
        self._select_and_change(result)

        return result

    # --------------------------------

    def next_clash(self):
        """Move to the next clash result."""

        result = self.workspace.clash_manager.next_result()
        self._select_and_change(result)

        return result

    # --------------------------------

    def focus_camera(self):
        """Focus the 3D camera on the active clash bounds."""

        result = self.selected_clash() or self.workspace.clash_manager.current_result()

        if result is None:
            return None

        self.workspace.clash_manager.open_result(result)
        self._set_camera_focus(result)
        self._changed()

        return result

    # --------------------------------

    def zoom_to_clash(self):
        """Zoom to the active clash bounds."""

        return self.focus_camera()

    # --------------------------------

    def highlight_clash(self):
        """Select the active clash for renderer highlighting."""

        result = self.selected_clash() or self.workspace.clash_manager.current_result()
        self._select_and_change(result)

        return result

    # --------------------------------

    def save_review(self):
        """Save review metadata through an undoable command."""

        result = self.selected_clash() or self.workspace.clash_manager.current_result()

        if result is None:
            return None

        before = self._review_state(result)
        after = {
            "status": self.status_editor.currentText(),
            "priority": self.priority_editor.currentText(),
            "assigned_reviewer": self.reviewer_editor.text(),
            "comments": self.comments.toPlainText(),
            "resolution_notes": self.resolution_notes.toPlainText(),
        }
        self.workspace.command_manager.execute(UpdateClashReviewCommand(self.workspace, result, before, after))
        self._changed()

        return result

    # --------------------------------

    def export_report(self, format_name, path=None):
        """Export visible clash results as a PDF or CSV report."""

        target = path or self._report_path(format_name)

        if not target:
            return None

        exported = self.report_generator.export(
            self.workspace,
            target,
            format_name,
            self._filtered_sorted_results(),
            self.group_by.currentText(),
        )
        self._changed()

        return exported

    # --------------------------------

    def selected_clash(self):
        """Return the selected clash result from the tree."""

        item = self.tree.currentItem()

        if item is None:
            return None

        result_id = item.data(0, Qt.UserRole)

        if not result_id:
            return None

        return self.workspace.clash_manager.get_result(result_id)

    # --------------------------------

    def _filtered_sorted_results(self):

        manager = self.workspace.clash_manager
        results = manager.filtered_results(
            self.search.text(),
            self.status_filter.currentText(),
            self.severity_filter.currentText(),
        )

        return manager.sorted_results(results, self.sort_by.currentText())

    def _selection_changed(self):

        if self._refreshing:
            return

        result = self.selected_clash()

        if result is not None:
            self.workspace.clash_manager.open_result(result)
            self.workspace.selection.select(result)
            self._load_review_fields(result)
            self._changed()

    def _load_review_fields(self, result):

        self.status_editor.setEnabled(result is not None)
        self.priority_editor.setEnabled(result is not None)
        self.reviewer_editor.setEnabled(result is not None)
        self.comments.setEnabled(result is not None)
        self.resolution_notes.setEnabled(result is not None)

        if result is None:
            self.reviewer_editor.clear()
            self.comments.clear()
            self.resolution_notes.clear()
            return

        self.status_editor.setCurrentText(result.status)
        self.priority_editor.setCurrentText(result.priority)
        self.reviewer_editor.setText(result.assigned_reviewer)
        self.comments.setPlainText(result.comments)
        self.resolution_notes.setPlainText(result.resolution_notes)

    def _select_and_change(self, result):

        if result is None:
            return

        self.workspace.selection.select(result)
        self._select_tree_result(result)
        self._changed()

    def _select_tree_result(self, result):

        for parent_index in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(parent_index)

            for child_index in range(parent.childCount()):
                child = parent.child(child_index)

                if child.data(0, Qt.UserRole) == result.id:
                    self.tree.setCurrentItem(child)
                    return

    def _set_camera_focus(self, result):

        camera = getattr(self.workspace, "camera3d", None)
        if camera is None:
            return

        bounds = result.bounding_box3d
        if bounds.valid and hasattr(camera, "target"):
            camera.target = bounds.center

    def _summary_text(self, results):

        stats = self.workspace.clash_manager.statistics

        return (
            f"Clashes: {len(results)} shown / {stats.total} total | "
            f"Open: {stats.unresolved} | Hard: {stats.hard} | "
            f"Clearance: {stats.clearance} | Reference: {stats.reference}"
        )

    def _review_state(self, result):

        return {
            "status": result.status,
            "priority": result.priority,
            "assigned_reviewer": result.assigned_reviewer,
            "comments": result.comments,
            "resolution_notes": result.resolution_notes,
        }

    def _report_path(self, format_name):

        extension = format_name.lower()
        title = f"Export Clash {extension.upper()} Report"
        path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            f"clash_report.{extension}",
            f"{extension.upper()} Files (*.{extension})",
        )

        return path

    def _save_state(self):

        manager = self.workspace.clash_manager
        manager.dock_state.update({
            "search": self.search.text(),
            "severity_filter": self.severity_filter.currentText(),
            "status_filter": self.status_filter.currentText(),
            "group_by": self.group_by.currentText(),
            "sort_by": self.sort_by.currentText(),
            "expanded": True,
        })

    def _load_state(self):

        state = self.workspace.clash_manager.dock_state
        self.search.setText(state.get("search", ""))
        self.status_filter.setCurrentText(state.get("status_filter", "All"))
        self.severity_filter.setCurrentText(state.get("severity_filter", "All"))
        self.group_by.setCurrentText(state.get("group_by", "Severity"))
        self.sort_by.setCurrentText(state.get("sort_by", "Severity"))

    def _changed(self):

        self.refresh()

        if self.on_change:
            self.on_change()
