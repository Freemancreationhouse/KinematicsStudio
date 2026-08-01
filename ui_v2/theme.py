from __future__ import annotations

from ui_v2.design_system import KINEMATICS_TOKENS as T


def _theme(
    *,
    background: str,
    background_secondary: str,
    panel: str,
    dock: str,
    card: str,
    viewport: str,
    ribbon: str,
    text: str,
    text_secondary: str,
    muted: str,
    disabled: str,
    border: str,
    border_strong: str,
    hover: str,
    selection: str,
    accent: str,
    focus: str,
    warning: str,
    error: str,
    success: str,
) -> str:
    """Build an application-wide stylesheet from reusable design tokens."""

    return f"""
QMainWindow {{
    background-color: {background};
    color: {text};
}}

QWidget {{
    background-color: {panel};
    color: {text};
    font-family: {T["font_family"]};
    font-size: {T["font_size_md"]};
    selection-background-color: {selection};
    selection-color: #FFFFFF;
}}

QWidget:disabled {{
    color: {disabled};
}}

QFrame {{
    background-color: {panel};
    border: none;
}}

QFrame[card="true"] {{
    background-color: {card};
    border: 1px solid {border};
    border-radius: {T["radius_card"]};
}}

QMenuBar {{
    background-color: {background_secondary};
    color: {text_secondary};
    border-bottom: 1px solid {border};
    spacing: {T["space_2"]};
    padding: {T["space_1"]} {T["space_2"]};
}}

QMenuBar::item {{
    background-color: transparent;
    border-radius: {T["radius_button"]};
    padding: {T["space_1"]} {T["space_2"]};
}}

QMenuBar::item:selected {{
    background-color: {hover};
    color: {text};
}}

QMenu {{
    background-color: {panel};
    color: {text};
    border: 1px solid {border_strong};
    border-radius: {T["radius_panel"]};
    padding: {T["space_1"]};
}}

QMenu::item {{
    border-radius: {T["radius_button"]};
    padding: {T["space_2"]} {T["space_4"]};
}}

QMenu::item:selected {{
    background-color: {hover};
    color: {text};
}}

QToolBar {{
    background-color: {background_secondary};
    border: none;
    spacing: {T["space_1"]};
    padding: {T["space_1"]};
}}

QToolButton,
QPushButton {{
    background-color: {card};
    color: {text};
    border: 1px solid {border_strong};
    border-radius: {T["radius_button"]};
    min-height: 24px;
    padding: {T["space_1"]} {T["space_3"]};
    font-weight: {T["font_weight_medium"]};
}}

QToolButton:hover,
QPushButton:hover {{
    background-color: {hover};
    border-color: {selection};
    color: {text};
}}

QToolButton:pressed,
QPushButton:pressed {{
    background-color: {selection};
    border-color: {selection};
    color: #FFFFFF;
}}

QToolButton:checked,
QPushButton:checked {{
    background-color: {accent};
    border-color: {selection};
    color: #FFFFFF;
}}

QToolButton:disabled,
QPushButton:disabled {{
    background-color: {background_secondary};
    border-color: {border};
    color: {disabled};
}}

QToolButton:focus,
QPushButton:focus,
QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QTreeView:focus,
QListView:focus,
QTableView:focus {{
    border: 1px solid {focus};
}}

QLineEdit,
QTextEdit,
QPlainTextEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {{
    background-color: {background};
    color: {text};
    border: 1px solid {border_strong};
    border-radius: {T["radius_button"]};
    min-height: 24px;
    padding: {T["space_1"]} {T["space_2"]};
}}

QLineEdit:hover,
QTextEdit:hover,
QPlainTextEdit:hover,
QComboBox:hover,
QSpinBox:hover,
QDoubleSpinBox:hover {{
    border-color: {selection};
}}

QLineEdit:disabled,
QTextEdit:disabled,
QPlainTextEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {{
    background-color: {background_secondary};
    border-color: {border};
    color: {disabled};
}}

QLineEdit[commandLine="true"] {{
    background-color: {viewport};
    border-color: {border_strong};
    font-family: {T["font_mono"]};
    font-size: {T["font_size_md"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {panel};
    color: {text};
    border: 1px solid {border_strong};
    selection-background-color: {hover};
    selection-color: {text};
    outline: none;
}}

QCheckBox,
QRadioButton {{
    color: {text_secondary};
    spacing: {T["space_2"]};
}}

QCheckBox::indicator,
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border_strong};
    background-color: {background};
}}

QCheckBox::indicator {{
    border-radius: {T["space_1"]};
}}

QRadioButton::indicator {{
    border-radius: 8px;
}}

QCheckBox::indicator:hover,
QRadioButton::indicator:hover {{
    border-color: {selection};
}}

QCheckBox::indicator:checked,
QRadioButton::indicator:checked {{
    background-color: {accent};
    border-color: {selection};
}}

QSlider::groove:horizontal {{
    background-color: {background};
    border: 1px solid {border};
    border-radius: 3px;
    height: 6px;
}}

QSlider::handle:horizontal {{
    background-color: {selection};
    border: 1px solid {focus};
    border-radius: 6px;
    margin: -4px 0;
    width: 12px;
}}

QTabWidget::pane {{
    background-color: {panel};
    border: 1px solid {border};
    border-radius: {T["radius_panel"]};
}}

QTabBar::tab {{
    background-color: {background_secondary};
    color: {muted};
    border: 1px solid {border};
    border-bottom: none;
    border-top-left-radius: {T["radius_button"]};
    border-top-right-radius: {T["radius_button"]};
    min-height: 24px;
    padding: {T["space_1"]} {T["space_3"]};
    margin-right: 2px;
}}

QTabBar::tab:hover {{
    background-color: {hover};
    color: {text};
}}

QTabBar::tab:selected {{
    background-color: {card};
    color: {text};
    border-top: 2px solid {selection};
}}

QDockWidget {{
    background-color: {dock};
    color: {text};
    border: 1px solid {border};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {background_secondary};
    color: {text};
    border-bottom: 1px solid {border};
    padding: {T["space_2"]} {T["space_3"]};
    font-weight: {T["font_weight_semibold"]};
}}

QGroupBox {{
    background-color: {panel};
    border: 1px solid {border};
    border-radius: {T["radius_panel"]};
    margin-top: {T["space_4"]};
    padding: {T["space_3"]};
    font-weight: {T["font_weight_semibold"]};
}}

QGroupBox::title {{
    color: {text_secondary};
    subcontrol-origin: margin;
    left: {T["space_3"]};
    padding: 0 {T["space_1"]};
}}

QListWidget,
QTreeWidget,
QTableWidget,
QListView,
QTreeView,
QTableView {{
    background-color: {background};
    alternate-background-color: {background_secondary};
    color: {text};
    border: 1px solid {border};
    border-radius: {T["radius_panel"]};
    outline: none;
    show-decoration-selected: 1;
}}

QListWidget::item,
QTreeWidget::item,
QTableWidget::item,
QListView::item,
QTreeView::item {{
    min-height: 24px;
    padding: {T["space_1"]} {T["space_2"]};
    border-radius: {T["radius_button"]};
}}

QListWidget::item:hover,
QTreeWidget::item:hover,
QTableWidget::item:hover,
QListView::item:hover,
QTreeView::item:hover {{
    background-color: {hover};
}}

QListWidget::item:selected,
QTreeWidget::item:selected,
QTableWidget::item:selected,
QListView::item:selected,
QTreeView::item:selected {{
    background-color: {selection};
    color: #FFFFFF;
}}

QHeaderView::section {{
    background-color: {background_secondary};
    color: {text_secondary};
    border: none;
    border-right: 1px solid {border};
    border-bottom: 1px solid {border};
    min-height: 24px;
    padding: {T["space_1"]} {T["space_2"]};
    font-weight: {T["font_weight_semibold"]};
}}

QStatusBar {{
    background-color: {background_secondary};
    color: {text_secondary};
    border-top: 1px solid {border};
}}

QStatusBar QLabel {{
    background-color: transparent;
    color: {text_secondary};
    border-left: 1px solid {border};
    padding: 0 {T["space_2"]};
    min-height: 22px;
}}

QLabel {{
    background-color: transparent;
    color: {text};
}}

QLabel[muted="true"] {{
    color: {muted};
}}

QSplitter::handle {{
    background-color: {border};
}}

QSplitter::handle:hover {{
    background-color: {selection};
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: {background_secondary};
    border: none;
    width: 10px;
    margin: 0;
}}

QScrollBar:horizontal {{
    background-color: {background_secondary};
    border: none;
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {{
    background-color: {border_strong};
    border-radius: 5px;
    min-height: 24px;
    min-width: 24px;
}}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {{
    background-color: {muted};
}}

QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {{
    background: none;
    border: none;
    height: 0;
    width: 0;
}}

QToolTip {{
    background-color: {card};
    color: {text};
    border: 1px solid {border_strong};
    border-radius: {T["radius_button"]};
    padding: {T["space_2"]};
    font-family: {T["font_family"]};
    font-size: {T["font_size_sm"]};
}}

QProgressBar {{
    background-color: {background};
    border: 1px solid {border};
    border-radius: {T["radius_button"]};
    color: {text};
    text-align: center;
    min-height: 16px;
}}

QProgressBar::chunk {{
    background-color: {accent};
    border-radius: {T["radius_button"]};
}}

QDialog {{
    background-color: {panel};
    color: {text};
}}

QMessageBox {{
    background-color: {panel};
    color: {text};
}}

QFrame#Ribbon,
QWidget#Ribbon,
QFrame#RibbonBar {{
    background-color: {ribbon};
}}

QFrame#WorkspaceViewportFrame,
QWidget#WorkspaceViewportArea {{
    background-color: {viewport};
}}

QFrame#PropertiesSidebar,
QFrame#WorkspaceDockRail {{
    background-color: {dock};
}}

*[state="warning"] {{
    color: {warning};
}}

*[state="error"] {{
    color: {error};
}}

*[state="success"] {{
    color: {success};
}}
"""


DARK_THEME = _theme(
    background=T["background_primary"],
    background_secondary=T["background_secondary"],
    panel=T["panel"],
    dock=T["dock"],
    card=T["card"],
    viewport=T["viewport"],
    ribbon=T["ribbon"],
    text=T["text_primary"],
    text_secondary=T["text_secondary"],
    muted=T["text_muted"],
    disabled=T["text_disabled"],
    border=T["border"],
    border_strong=T["border_strong"],
    hover=T["hover"],
    selection=T["selection"],
    accent=T["accent"],
    focus=T["focus"],
    warning=T["warning"],
    error=T["error"],
    success=T["success"],
)

LIGHT_THEME = _theme(
    background="#F4F6F8",
    background_secondary="#E7EBF0",
    panel="#FFFFFF",
    dock="#EEF1F5",
    card="#F8FAFC",
    viewport="#F1F3F6",
    ribbon="#EDF1F6",
    text="#151A20",
    text_secondary="#303844",
    muted="#647080",
    disabled="#9AA4B2",
    border="#CBD3DD",
    border_strong="#AEB8C5",
    hover="#DCE6F2",
    selection="#2F80ED",
    accent="#1F78D1",
    focus="#0A66C2",
    warning="#9A6500",
    error="#B33A3A",
    success="#1F8F55",
)

HIGH_CONTRAST_THEME = _theme(
    background="#000000",
    background_secondary="#101010",
    panel="#000000",
    dock="#080808",
    card="#151515",
    viewport="#000000",
    ribbon="#101010",
    text="#FFFFFF",
    text_secondary="#FFFFFF",
    muted="#E0E0E0",
    disabled="#808080",
    border="#FFFFFF",
    border_strong="#FFFFFF",
    hover="#1F3A4A",
    selection="#00B7FF",
    accent="#00B7FF",
    focus="#FFFF00",
    warning="#FFD54F",
    error="#FF5252",
    success="#69F0AE",
)


THEMES = {
    "Dark": DARK_THEME,
    "Light": LIGHT_THEME,
    "High Contrast": HIGH_CONTRAST_THEME,
}
