from engine.commands.command import Command
from engine.import3d import ImportSettings
from engine.references3d import ReferenceModel


class AddReferenceModelCommand(Command):
    """Undoable command for adding a reference model."""

    def __init__(self, workspace, model):

        self.workspace = workspace
        self.model = model

    def execute(self):
        """Add the reference model."""

        self.workspace.reference_manager.add_model(self.model)

    def undo(self):
        """Remove the reference model."""

        self.workspace.reference_manager.remove_model(self.model)


class RemoveReferenceModelCommand(Command):
    """Undoable command for removing a reference model."""

    def __init__(self, workspace, model):

        self.workspace = workspace
        self.model = model
        self.instances = []

    def execute(self):
        """Remove the reference model."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is None:
            return

        self.instances = [
            instance for instance in self.workspace.reference_manager.instances
            if instance.model_id == target.id
        ]
        self.workspace.reference_manager.remove_model(target)

    def undo(self):
        """Restore the reference model."""

        self.workspace.reference_manager.add_model(self.model)
        for instance in self.instances:
            self.workspace.reference_manager.add_instance(instance)
            self.workspace.assign_layer(instance)


class AddReferenceInstanceCommand(Command):
    """Undoable command for adding a reference instance."""

    def __init__(self, workspace, instance):

        self.workspace = workspace
        self.instance = instance

    def execute(self):
        """Add the reference instance and select it."""

        self.workspace.reference_manager.add_instance(self.instance)
        self.workspace.assign_layer(self.instance)
        self.workspace.selection.select(self.instance)

    def undo(self):
        """Remove the reference instance."""

        self.workspace.reference_manager.remove_instance(self.instance)
        self.workspace.selection.unregister_entity(self.instance)
        self.workspace.unregister_layer_entity(self.instance)


class RemoveReferenceInstanceCommand(Command):
    """Undoable command for removing a reference instance."""

    def __init__(self, workspace, instance):

        self.workspace = workspace
        self.instance = instance

    def execute(self):
        """Remove the reference instance."""

        self.workspace.reference_manager.remove_instance(self.instance)
        self.workspace.selection.unregister_entity(self.instance)
        self.workspace.unregister_layer_entity(self.instance)

    def undo(self):
        """Restore the reference instance."""

        self.workspace.reference_manager.add_instance(self.instance)
        self.workspace.assign_layer(self.instance)


class UpdateReferenceModelCommand(Command):
    """Undoable command for updating reference model state."""

    def __init__(self, model, before, after):

        self.model = model
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply model state."""

        self._apply(self.after)

    def undo(self):
        """Restore model state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.model, key, value)


class UpdateReferenceInstanceCommand(Command):
    """Undoable command for updating reference instance state."""

    def __init__(self, instance, before, after):

        self.instance = instance
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply instance state."""

        self._apply(self.after)

    def undo(self):
        """Restore instance state."""

        self._apply(self.before)

    def _apply(self, state):

        for key, value in state.items():
            setattr(self.instance, key, value)


class ReloadReferenceCommand(Command):
    """Undoable placeholder command for reloading a reference."""

    def __init__(self, workspace, model):

        self.workspace = workspace
        self.model = model
        self.before_status = None

    def execute(self):
        """Reload the reference model."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is None:
            return

        if self.before_status is None:
            self.before_status = target.status

        self.workspace.reference_manager.reload(target)

    def undo(self):
        """Restore previous status."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None:
            target.status = self.before_status


class UnloadReferenceCommand(Command):
    """Undoable command for unloading a reference."""

    def __init__(self, workspace, model):

        self.workspace = workspace
        self.model = model
        self.before_status = None

    def execute(self):
        """Unload the reference model."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is None:
            return

        if self.before_status is None:
            self.before_status = target.status

        self.workspace.reference_manager.unload(target)

    def undo(self):
        """Restore previous status."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None:
            target.status = self.before_status


class AddCoordinationRuleCommand(Command):
    """Undoable command for adding a coordination rule."""

    def __init__(self, workspace, rule):

        self.workspace = workspace
        self.rule = rule

    def execute(self):
        """Add the coordination rule."""

        self.workspace.coordination_manager.add_rule(self.rule)

    def undo(self):
        """Remove the coordination rule."""

        if self.rule in self.workspace.coordination_manager.rules:
            self.workspace.coordination_manager.rules.remove(self.rule)


class SetReferenceIsolationCommand(Command):
    """Undoable command for changing reference isolation state."""

    def __init__(self, workspace, model=None):

        self.workspace = workspace
        self.model = model
        self.before = list(workspace.reference_manager.isolated_model_ids)
        self.after = None

    def execute(self):
        """Apply reference isolation."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is None:
            self.after = []
        else:
            self.after = [target.id]

        self.workspace.reference_manager.isolated_model_ids = list(self.after)

    def undo(self):
        """Restore previous reference isolation."""

        self.workspace.reference_manager.isolated_model_ids = list(self.before)


class UpdateReferenceLayerMappingCommand(Command):
    """Undoable command for reference layer mapping changes."""

    def __init__(self, workspace, model, layer_name, before, after):

        self.workspace = workspace
        self.model = model
        self.layer_name = layer_name
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply reference layer mapping state."""

        self.workspace.reference_manager.update_layer_mapping(
            self.model,
            self.layer_name,
            **self.after,
        )

    def undo(self):
        """Restore previous reference layer mapping state."""

        self.workspace.reference_manager.update_layer_mapping(
            self.model,
            self.layer_name,
            **self.before,
        )


class UpdateReferenceStyleCommand(Command):
    """Undoable command for reference display style changes."""

    def __init__(self, workspace, model, before, after):

        self.workspace = workspace
        self.model = model
        self.before = dict(before)
        self.after = dict(after)

    def execute(self):
        """Apply reference style overrides."""

        self.workspace.reference_manager.update_style_overrides(
            self.model,
            **self.after,
        )

    def undo(self):
        """Restore previous reference style overrides."""

        self.workspace.reference_manager.update_style_overrides(
            self.model,
            **self.before,
        )


class SaveReferenceDisplayPresetCommand(Command):
    """Undoable command for storing a reference display preset."""

    def __init__(self, workspace, model, name):

        self.workspace = workspace
        self.model = model
        self.preset_name = name
        target = workspace.reference_manager.get_model(model)
        self.before = dict(getattr(target, "display_presets", {}))
        self.before_preset = getattr(target.style_overrides, "preset_name", "Default") if target else "Default"

    def execute(self):
        """Save the display preset."""

        self.workspace.reference_manager.save_display_preset(self.model, self.preset_name)

    def undo(self):
        """Restore previous display presets."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None:
            target.display_presets = dict(self.before)
            target.style_overrides.preset_name = self.before_preset


class UpdateCoordinationUICommand(Command):
    """Undoable command for coordination UI settings and rules."""

    def __init__(self, workspace, model, before, after, rule=None, conflict=None):

        self.workspace = workspace
        self.model = model
        self.before = dict(before)
        self.after = dict(after)
        self.rule = rule
        self.conflict = conflict
        self.rule_added = False
        self.conflict_added = False

    def execute(self):
        """Apply coordination UI settings."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None:
            target.coordination_ui_settings.update(self.after)

        if self.rule is not None and self.rule not in self.workspace.coordination_manager.rules:
            self.workspace.coordination_manager.add_rule(self.rule)
            self.rule_added = True

        if self.conflict is not None and self.conflict not in self.workspace.coordination_manager.conflicts:
            self.workspace.coordination_manager.conflicts.append(self.conflict)
            self.conflict_added = True

    def undo(self):
        """Restore previous coordination UI settings."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None:
            target.coordination_ui_settings.update(self.before)

        if self.rule_added and self.rule in self.workspace.coordination_manager.rules:
            self.workspace.coordination_manager.rules.remove(self.rule)

        if self.conflict_added and self.conflict in self.workspace.coordination_manager.conflicts:
            self.workspace.coordination_manager.conflicts.remove(self.conflict)


class ImportReferenceCommand(Command):
    """Undoable command for importing an external 3D reference file."""

    def __init__(self, workspace, import_manager, path, name=None, settings=None, transform=None):

        self.workspace = workspace
        self.import_manager = import_manager
        self.path = path
        self.reference_name = name
        self.settings = settings or ImportSettings()
        self.transform = transform
        self.result = None
        self.model = None
        self.instance = None

    def execute(self):
        """Import and store the reference model and first instance."""

        if self.model is None:
            self.result = self.import_manager.read(self.path, self.settings)
            self.model = self.workspace.reference_manager.create_imported_model(
                self.result,
                self.reference_name,
                self.settings,
            )
            self.instance = self.workspace.reference_manager.create_instance(
                self.model,
                self.transform,
                self.model.name,
            )
        else:
            self.workspace.reference_manager.add_model(self.model)
            self.workspace.reference_manager.add_instance(self.instance)

        self.workspace.assign_layer(self.instance)
        self.workspace.selection.select(self.instance)

    def undo(self):
        """Remove the imported reference."""

        self.workspace.reference_manager.remove_model(self.model)
        self.workspace.selection.unregister_entity(self.instance)
        self.workspace.unregister_layer_entity(self.instance)


class ReloadImportedReferenceCommand(Command):
    """Undoable command for re-reading an imported reference file."""

    def __init__(self, workspace, import_manager, model, settings=None):

        self.workspace = workspace
        self.import_manager = import_manager
        self.model = model
        self.settings = settings
        self.before = None
        self.result = None

    def execute(self):
        """Reload import data for an existing model."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is None:
            return

        if self.before is None:
            self.before = target.to_dict()

        settings = self.settings or target.import_settings
        self.result = self.import_manager.read(target.path, settings)
        target.apply_import_result(self.result, settings)

    def undo(self):
        """Restore previous import data."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None and self.before is not None:
            self._restore_model(target, self.before)

    def _restore_model(self, target, data):

        restored = ReferenceModel.from_dict(data)
        target.__dict__.update(restored.__dict__)


class ReplaceReferenceCommand(Command):
    """Undoable command for replacing a reference file with another path."""

    def __init__(self, workspace, import_manager, model, path, settings=None):

        self.workspace = workspace
        self.import_manager = import_manager
        self.model = model
        self.path = path
        self.settings = settings
        self.before = None
        self.result = None

    def execute(self):
        """Replace import data for an existing model."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is None:
            return

        if self.before is None:
            self.before = target.to_dict()

        settings = self.settings or target.import_settings
        self.result = self.import_manager.read(self.path, settings)
        target.apply_import_result(self.result, settings)

    def undo(self):
        """Restore the previous reference data."""

        target = self.workspace.reference_manager.get_model(self.model)

        if target is not None and self.before is not None:
            restored = ReferenceModel.from_dict(self.before)
            target.__dict__.update(restored.__dict__)
