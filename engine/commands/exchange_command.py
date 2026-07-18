from engine.commands.command import Command


class SaveExchangeProfileCommand(Command):
    """Undoable command for saving one exchange profile."""

    def __init__(self, workspace, name, profile):

        self.workspace = workspace
        self.profile_name = name
        self.profile = dict(profile)
        self.before = workspace.import_manager.validation_manager.profiles.get(name)

    def execute(self):
        """Store the profile."""

        self.workspace.import_manager.validation_manager.save_profile(self.profile_name, self.profile)

    def undo(self):
        """Restore the previous profile state."""

        profiles = self.workspace.import_manager.validation_manager.profiles

        if self.before is None:
            profiles.pop(self.profile_name, None)
        else:
            profiles[self.profile_name] = dict(self.before)


class UpdateExchangeSettingsCommand(Command):
    """Undoable command for updating exchange dialog or validation settings."""

    def __init__(self, workspace, key, before, after):

        self.workspace = workspace
        self.key = key
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply exchange settings."""

        self.workspace.import_manager.adapter_settings[self.key] = dict(self.after)

    def undo(self):
        """Restore previous exchange settings."""

        if self.before:
            self.workspace.import_manager.adapter_settings[self.key] = dict(self.before)
        else:
            self.workspace.import_manager.adapter_settings.pop(self.key, None)


class StoreExchangeValidationReportCommand(Command):
    """Undoable command for storing the latest validation report."""

    def __init__(self, workspace, report):

        self.workspace = workspace
        self.report = report
        manager = workspace.import_manager.validation_manager
        self.before = (
            manager.previous_report
            if manager.last_report is report and manager.previous_report is not None
            else manager.last_report
        )

    def execute(self):
        """Store the report."""

        self.workspace.import_manager.validation_manager.last_report = self.report

    def undo(self):
        """Restore the previous report."""

        self.workspace.import_manager.validation_manager.last_report = self.before
