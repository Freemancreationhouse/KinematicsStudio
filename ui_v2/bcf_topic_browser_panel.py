from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.bcf import BCFComment
from engine.commands import UpdateBCFTopicCommand


class BCFTopicBrowserPanel(QWidget):
    """Dockable browser for BCF projects, topics, comments and viewpoints."""

    PROJECT_COLUMNS = ["Project", "Topics", "Version"]
    TOPIC_COLUMNS = ["Title", "Type", "Status", "Priority", "Assignee", "Comments", "Viewpoints"]

    def __init__(self, workspace, on_change=None):

        super().__init__()

        self.workspace = workspace
        self.on_change = on_change
        self._refreshing = False
        self._last_topic_id = ""
        self._build()
        self._load_state()
        self.refresh()

    def _build(self):

        layout = QVBoxLayout(self)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search BCF topics")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Open", "In Review", "Resolved", "Closed"])
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "Low", "Normal", "High", "Critical"])
        self.grouping = QComboBox()
        self.grouping.addItems(["Project", "Status", "Priority", "Assignee"])
        filters.addWidget(QLabel("Search"))
        filters.addWidget(self.search)
        filters.addWidget(QLabel("Status"))
        filters.addWidget(self.status_filter)
        filters.addWidget(QLabel("Priority"))
        filters.addWidget(self.priority_filter)
        filters.addWidget(QLabel("Group"))
        filters.addWidget(self.grouping)
        layout.addLayout(filters)

        self.project_tree = QTreeWidget()
        self.project_tree.setColumnCount(len(self.PROJECT_COLUMNS))
        self.project_tree.setHeaderLabels(self.PROJECT_COLUMNS)
        layout.addWidget(self.project_tree)

        self.topic_tree = QTreeWidget()
        self.topic_tree.setColumnCount(len(self.TOPIC_COLUMNS))
        self.topic_tree.setHeaderLabels(self.TOPIC_COLUMNS)
        self.topic_tree.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.topic_tree, 1)

        self.summary = QLabel("")
        layout.addWidget(self.summary)

        toolbar = QHBoxLayout()
        self.navigate_button = QPushButton("Navigate")
        self.sync_button = QPushButton("Sync Selection")
        self.comment_button = QPushButton("Add Comment")
        self.status_button = QPushButton("Status")
        self.priority_button = QPushButton("Priority")
        self.assign_button = QPushButton("Assign")

        for button in (
            self.navigate_button,
            self.sync_button,
            self.comment_button,
            self.status_button,
            self.priority_button,
            self.assign_button,
        ):
            toolbar.addWidget(button)

        layout.addLayout(toolbar)

        self.search.textChanged.connect(self.refresh)
        self.status_filter.currentTextChanged.connect(self.refresh)
        self.priority_filter.currentTextChanged.connect(self.refresh)
        self.grouping.currentTextChanged.connect(self.refresh)
        self.navigate_button.clicked.connect(self.navigate_topic)
        self.sync_button.clicked.connect(self.sync_selection)
        self.comment_button.clicked.connect(self.add_comment)
        self.status_button.clicked.connect(self.change_status)
        self.priority_button.clicked.connect(self.change_priority)
        self.assign_button.clicked.connect(self.assign_topic)

    def refresh(self):
        """Refresh project and topic rows."""

        if self._refreshing:
            return

        self._refreshing = True
        self._save_state()
        self.project_tree.clear()
        self.topic_tree.clear()

        for project in self.workspace.bcf_manager.projects:
            self._add_project_row(project)

        self._add_topic_rows()
        self.summary.setText(self._summary_text())
        self.project_tree.resizeColumnToContents(0)
        self.topic_tree.resizeColumnToContents(0)
        self._refreshing = False

    def selected_topic(self):
        """Return the selected BCF topic."""

        item = self.topic_tree.currentItem()

        if item is None:
            return self.workspace.bcf_manager.get_topic(self._last_topic_id)

        topic = self.workspace.bcf_manager.get_topic(item.data(0, Qt.UserRole))

        if topic is not None:
            self._last_topic_id = topic.id
        else:
            topic = self.workspace.bcf_manager.get_topic(self._last_topic_id)

        return topic

    def navigate_topic(self):
        """Select and focus the current BCF topic."""

        topic = self.selected_topic()

        if topic is None:
            return None

        self.workspace.selection.clear()
        self.workspace.selection.select(topic)
        self.workspace.bcf_manager.restore_viewpoint(topic, getattr(self, "camera", None))
        self._changed(topic)

        return topic

    def sync_selection(self):
        """Synchronize selection from the selected BCF topic."""

        topic = self.selected_topic()

        if topic is None:
            return []

        selected = self.workspace.bcf_manager.sync_selection(self.workspace, topic)

        if self.on_change:
            self.on_change()

        return selected

    def add_comment(self, text=None, author=""):
        """Add a comment to the selected BCF topic through the Command System."""

        topic = self.selected_topic()

        if topic is None:
            return None

        comment_text = text

        if comment_text is None:
            comment_text, ok = QInputDialog.getText(self, "BCF Comment", "Comment")
            if not ok:
                return None

        before = {"comments": list(topic.comments)}
        after = {"comments": list(topic.comments) + [BCFComment(comment_text, author, topic.status)]}
        self.workspace.command_manager.execute(UpdateBCFTopicCommand(topic, before, after))
        self._changed(topic)

        return after["comments"][-1]

    def change_status(self, status=None):
        """Change selected topic status through the Command System."""

        return self._change_field("status", status, ["Open", "In Review", "Resolved", "Closed"])

    def change_priority(self, priority=None):
        """Change selected topic priority through the Command System."""

        return self._change_field("priority", priority, ["Low", "Normal", "High", "Critical"])

    def assign_topic(self, assignee=None):
        """Assign selected topic through the Command System."""

        topic = self.selected_topic()

        if topic is None:
            return None

        value = assignee

        if value is None:
            value, ok = QInputDialog.getText(self, "Assign BCF Topic", "Assignee", text=topic.assignee)
            if not ok:
                return None

        self.workspace.command_manager.execute(UpdateBCFTopicCommand(
            topic,
            {"assignee": topic.assignee},
            {"assignee": value},
        ))
        self._changed(topic)

        return value

    def _change_field(self, field, value, choices):

        topic = self.selected_topic()

        if topic is None:
            return None

        new_value = value

        if new_value is None:
            new_value, ok = QInputDialog.getItem(
                self,
                f"BCF Topic {field.title()}",
                field.title(),
                choices,
                max(0, choices.index(getattr(topic, field)) if getattr(topic, field) in choices else 0),
                False,
            )
            if not ok:
                return None

        self.workspace.command_manager.execute(UpdateBCFTopicCommand(
            topic,
            {field: getattr(topic, field)},
            {field: new_value},
        ))
        self._changed()

        return new_value

    def _selection_changed(self):

        if self._refreshing:
            return

        topic = self.selected_topic()

        if topic is not None:
            self._last_topic_id = topic.id
            self.workspace.selection.clear()
            self.workspace.selection.select(topic)

            if self.on_change:
                self.on_change()

    def _add_project_row(self, project):

        row = QTreeWidgetItem([
            project.name,
            str(len(project.topics)),
            project.metadata.version,
        ])
        row.setData(0, Qt.UserRole, project.id)
        self.project_tree.addTopLevelItem(row)

    def _add_topic_rows(self):

        grouping = self.grouping.currentText()

        if grouping == "Project":
            for project in self.workspace.bcf_manager.projects:
                parent = QTreeWidgetItem([project.name, "", "", "", "", "", ""])
                self.topic_tree.addTopLevelItem(parent)
                for topic in self._filtered_topics(project.topics):
                    parent.addChild(self._topic_row(topic))
                parent.setExpanded(True)
            return

        groups = {}

        for topic in self._filtered_topics(self.workspace.bcf_manager.topics()):
            key = getattr(topic, grouping.lower(), "") or "Unassigned"
            groups.setdefault(key, []).append(topic)

        for key, topics in sorted(groups.items()):
            parent = QTreeWidgetItem([key, "", "", "", "", "", ""])
            self.topic_tree.addTopLevelItem(parent)
            for topic in topics:
                parent.addChild(self._topic_row(topic))
            parent.setExpanded(True)

    def _topic_row(self, topic):

        row = QTreeWidgetItem([
            topic.title,
            topic.topic_type,
            topic.status,
            topic.priority,
            topic.assignee or "Unassigned",
            str(len(topic.comments)),
            str(len(topic.viewpoints)),
        ])
        row.setData(0, Qt.UserRole, topic.id)

        return row

    def _filtered_topics(self, topics):

        query = self.search.text().strip().lower()
        status = self.status_filter.currentText()
        priority = self.priority_filter.currentText()

        return [
            topic for topic in topics
            if (
                (not query or self._matches(topic, query)) and
                (status == "All" or topic.status == status) and
                (priority == "All" or topic.priority == priority)
            )
        ]

    def _matches(self, topic, query):

        return any(
            query in str(value).lower()
            for value in (
                topic.title,
                topic.description,
                topic.topic_type,
                topic.status,
                topic.priority,
                topic.assignee,
            )
        )

    def _summary_text(self):

        topics = self.workspace.bcf_manager.topics()
        open_count = len([topic for topic in topics if topic.status != "Closed"])

        return f"BCF Topics: {len(topics)} | Open: {open_count} | Projects: {len(self.workspace.bcf_manager.projects)}"

    def _load_state(self):

        state = self.workspace.bcf_manager.settings.get("browser_state", {})
        self.search.setText(state.get("search", ""))
        self.status_filter.setCurrentText(state.get("status", "All"))
        self.priority_filter.setCurrentText(state.get("priority", "All"))
        self.grouping.setCurrentText(state.get("grouping", "Project"))

    def _save_state(self):

        self.workspace.bcf_manager.settings["browser_state"] = {
            "search": self.search.text(),
            "status": self.status_filter.currentText(),
            "priority": self.priority_filter.currentText(),
            "grouping": self.grouping.currentText(),
        }

    def _changed(self, topic=None):

        self.refresh()
        self._select_topic(topic)

        if self.on_change:
            self.on_change()

    def _select_topic(self, topic):

        if topic is None:
            return

        self._last_topic_id = topic.id

        for index in range(self.topic_tree.topLevelItemCount()):
            parent = self.topic_tree.topLevelItem(index)

            if parent.data(0, Qt.UserRole) == topic.id:
                self.topic_tree.setCurrentItem(parent)
                return

            for child_index in range(parent.childCount()):
                child = parent.child(child_index)

                if child.data(0, Qt.UserRole) == topic.id:
                    self.topic_tree.setCurrentItem(child)
                    return
