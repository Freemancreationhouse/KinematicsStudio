from ui_v2.design_system import KINEMATICS_TOKENS


def _theme(surface, surface_alt, panel, panel_alt, text, muted, border, accent, focus):
    return f"""
QMainWindow{{
    background:{surface};
    color:{text};
}}

QWidget{{
    background:{panel};
    color:{text};
    font-family:{KINEMATICS_TOKENS["font_family"]};
    font-size:{KINEMATICS_TOKENS["font_size"]};
}}

QTabWidget::pane{{
    border:1px solid {border};
    background:{surface};
}}

QTabBar::tab{{
    background:{surface_alt};
    color:{muted};
    border:1px solid {border};
    border-bottom:0;
    padding:8px 14px;
    margin-right:2px;
    border-top-left-radius:{KINEMATICS_TOKENS["radius"]};
    border-top-right-radius:{KINEMATICS_TOKENS["radius"]};
}}

QTabBar::tab:selected{{
    background:{panel_alt};
    color:{text};
    border-top:2px solid {accent};
}}

QPushButton{{
    background:{panel_alt};
    color:{text};
    border:1px solid {border};
    border-radius:{KINEMATICS_TOKENS["radius"]};
    padding:7px 10px;
    min-height:28px;
}}

QPushButton:hover{{
    background:{surface_alt};
    border-color:{accent};
}}

QPushButton:pressed{{
    background:{accent};
    color:white;
}}

QPushButton:focus, QLineEdit:focus, QComboBox:focus{{
    border:1px solid {focus};
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox{{
    background:{surface};
    color:{text};
    border:1px solid {border};
    border-radius:{KINEMATICS_TOKENS["radius"]};
    padding:6px;
    selection-background-color:{accent};
}}

QDockWidget{{
    color:{text};
    titlebar-close-icon:none;
    titlebar-normal-icon:none;
}}

QDockWidget::title{{
    background:{surface_alt};
    color:{text};
    padding:7px;
    border-bottom:1px solid {border};
}}

QMenuBar, QMenu, QStatusBar, QToolBar{{
    background:{surface_alt};
    color:{text};
    border:0;
}}

QListWidget, QTreeWidget, QTextEdit{{
    background:{surface};
    color:{text};
    border:1px solid {border};
    border-radius:{KINEMATICS_TOKENS["radius"]};
}}

QListWidget::item:selected, QTreeWidget::item:selected{{
    background:{accent};
    color:white;
}}

QLabel{{
    color:{text};
}}

QScrollBar:vertical, QScrollBar:horizontal{{
    background:{surface};
    border:0;
    width:10px;
    height:10px;
}}

QScrollBar::handle{{
    background:{border};
    border-radius:5px;
}}
"""


DARK_THEME = _theme(
    KINEMATICS_TOKENS["surface"],
    KINEMATICS_TOKENS["surface_alt"],
    KINEMATICS_TOKENS["panel"],
    KINEMATICS_TOKENS["panel_alt"],
    KINEMATICS_TOKENS["text"],
    KINEMATICS_TOKENS["muted"],
    KINEMATICS_TOKENS["border"],
    KINEMATICS_TOKENS["accent"],
    KINEMATICS_TOKENS["focus"],
)

LIGHT_THEME = _theme(
    "#F6F8FB",
    "#E7ECF3",
    "#FFFFFF",
    "#EEF3F8",
    "#17202A",
    "#56616F",
    "#C8D1DC",
    "#1F78D1",
    "#0A66C2",
)

HIGH_CONTRAST_THEME = _theme(
    "#000000",
    "#101010",
    "#000000",
    "#151515",
    "#FFFFFF",
    "#E0E0E0",
    "#FFFFFF",
    "#00B7FF",
    "#FFFF00",
)


THEMES = {
    "Dark": DARK_THEME,
    "Light": LIGHT_THEME,
    "High Contrast": HIGH_CONTRAST_THEME,
}
