import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.import3d import ImportSettings
from ui_v2.import_options_dialog import ImportOptionsDialog


qt_app = QApplication.instance() or QApplication([])

dialog = ImportOptionsDialog(
    None,
    ImportSettings(
        units="meter",
        scale=2.5,
        up_axis="Y",
        forward_axis="-Z",
        center_model=True,
        merge_meshes=False,
        keep_hierarchy=False,
        generate_normals=False,
        generate_bounds=True,
        import_hidden_objects=True,
        remember_settings=True,
    ),
    "C:/refs/model.obj",
)

settings = dialog.settings()

assert settings.units == "meter"
assert settings.scale == 2.5
assert settings.up_axis == "Y"
assert settings.forward_axis == "-Z"
assert settings.center_model is True
assert settings.merge_meshes is False
assert settings.keep_hierarchy is False
assert settings.generate_normals is False
assert settings.generate_bounds is True
assert settings.import_hidden_objects is True
assert settings.remember_settings is True
assert "Scale" in dialog.preview_metadata.text()

print("3d-import-options-dialog-ok")
