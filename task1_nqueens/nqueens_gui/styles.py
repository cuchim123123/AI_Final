"""Dark and Light theme stylesheets with complete palette coverage."""

DARK_THEME = """
/* Global defaults: ensure no native OS colors bleed through */
QWidget {
    background-color: #161B22;
    color: #E6EDF3;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 12px;
}

QMainWindow, QDialog {
    background-color: #0D1117;
    color: #E6EDF3;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #30363D;
    background-color: #161B22;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #21262D;
    border: 1px solid #30363D;
    border-bottom: none;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #8B949E;
}

QTabBar::tab:selected {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-bottom: 2px solid #58A6FF;
    color: #58A6FF;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #30363D;
    color: #C9D1D9;
}

/* Group Boxes / Cards */
QGroupBox {
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #30363D;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 16px;
    background-color: #161B22;
    color: #F0F6FC;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #161B22;
    color: #58A6FF;
}

/* Form Controls */
QLabel {
    background-color: transparent;
    color: #C9D1D9;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 6px 10px;
    color: #F0F6FC;
    selection-background-color: #1F6FEB;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #58A6FF;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #161B22;
    border: 1px solid #30363D;
    color: #F0F6FC;
    selection-background-color: #1F6FEB;
    selection-color: #FFFFFF;
    outline: none;
}

QCheckBox, QRadioButton {
    background-color: transparent;
    color: #E6EDF3;
    spacing: 6px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 3px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #1F6FEB;
    border-color: #58A6FF;
}

/* Buttons */
QPushButton {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #30363D;
    color: #F0F6FC;
    border-color: #8B949E;
}

QPushButton:pressed {
    background-color: #161B22;
}

QPushButton:disabled {
    background-color: #21262D;
    color: #484F58;
    border-color: #21262D;
}

QPushButton[class="primary"] {
    background-color: #1F6FEB;
    color: #FFFFFF;
    border: 1px solid #388BFD;
    font-weight: 600;
}

QPushButton[class="primary"]:hover {
    background-color: #388BFD;
}

QPushButton[class="success"] {
    background-color: #238636;
    color: #FFFFFF;
    border: 1px solid #2EA043;
    font-weight: 600;
}

QPushButton[class="success"]:hover {
    background-color: #2EA043;
}

QPushButton[class="danger"] {
    background-color: #DA3633;
    color: #FFFFFF;
    border: 1px solid #F85149;
    font-weight: 600;
}

QPushButton[class="danger"]:hover {
    background-color: #F85149;
}

/* Tables & Lists */
QTableWidget, QListWidget, QTextBrowser {
    background-color: #0D1117;
    border: 1px solid #30363D;
    gridline-color: #21262D;
    color: #E6EDF3;
    border-radius: 6px;
}

QTableWidget::item, QListWidget::item {
    padding: 6px;
    color: #E6EDF3;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #1F6FEB;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #161B22;
    padding: 7px;
    border: none;
    border-right: 1px solid #30363D;
    border-bottom: 2px solid #30363D;
    font-weight: 600;
    color: #8B949E;
}

/* Scroll Area & Splitters */
QScrollArea {
    border: none;
    background-color: transparent;
}

QSplitter::handle {
    background-color: #30363D;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background-color: #30363D;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background-color: #1F6FEB;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #F0F6FC;
    border: 2px solid #58A6FF;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #30363D;
    border-radius: 6px;
    text-align: center;
    background-color: #0D1117;
    height: 18px;
    color: #FFFFFF;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #1F6FEB;
    border-radius: 5px;
}

/* Menus & Tooltips */
QMenuBar {
    background-color: #0D1117;
    border-bottom: 1px solid #30363D;
    color: #E6EDF3;
}

QMenuBar::item:selected {
    background-color: #21262D;
}

QMenu {
    background-color: #161B22;
    border: 1px solid #30363D;
    color: #E6EDF3;
}

QMenu::item:selected {
    background-color: #1F6FEB;
    color: #FFFFFF;
}

QToolTip {
    background-color: #21262D;
    color: #F0F6FC;
    border: 1px solid #30363D;
    padding: 4px;
    border-radius: 4px;
}

QStatusBar {
    background-color: #0D1117;
    border-top: 1px solid #30363D;
    color: #8B949E;
}
"""

LIGHT_THEME = """
/* Explicit complete light palette */
QWidget {
    background-color: #FFFFFF;
    color: #212529;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 12px;
}

QMainWindow, QDialog {
    background-color: #F8F9FA;
    color: #212529;
}

QTabWidget::pane {
    border: 1px solid #DEE2E6;
    background-color: #FFFFFF;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #E9ECEF;
    border: 1px solid #DEE2E6;
    border-bottom: none;
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #495057;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    border-bottom: 2px solid #0D6EFD;
    color: #0D6EFD;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #F1F3F5;
    color: #212529;
}

QGroupBox {
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 16px;
    background-color: #FFFFFF;
    color: #2B303A;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #FFFFFF;
    color: #0D6EFD;
}

QLabel {
    background-color: transparent;
    color: #343A40;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #CED4DA;
    border-radius: 6px;
    padding: 6px 10px;
    color: #212529;
    selection-background-color: #0D6EFD;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #86B7FE;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #CED4DA;
    color: #212529;
    selection-background-color: #0D6EFD;
    selection-color: #FFFFFF;
}

QCheckBox, QRadioButton {
    background-color: transparent;
    color: #212529;
}

QPushButton {
    background-color: #E9ECEF;
    color: #212529;
    border: 1px solid #CED4DA;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #DEE2E6;
}

QPushButton[class="primary"] {
    background-color: #0D6EFD;
    color: #FFFFFF;
    border: 1px solid #0D6EFD;
    font-weight: 600;
}

QPushButton[class="success"] {
    background-color: #198754;
    color: #FFFFFF;
    border: 1px solid #198754;
    font-weight: 600;
}

QPushButton[class="danger"] {
    background-color: #DC3545;
    color: #FFFFFF;
    border: 1px solid #DC3545;
    font-weight: 600;
}

QTableWidget, QListWidget, QTextBrowser {
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    gridline-color: #E9ECEF;
    color: #212529;
    border-radius: 6px;
}

QTableWidget::item, QListWidget::item {
    color: #212529;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #0D6EFD;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #F8F9FA;
    padding: 7px;
    border: none;
    border-right: 1px solid #DEE2E6;
    border-bottom: 2px solid #CED4DA;
    font-weight: 600;
    color: #495057;
}

QSlider::groove:horizontal {
    height: 6px;
    background-color: #DEE2E6;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background-color: #0D6EFD;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #FFFFFF;
    border: 2px solid #0D6EFD;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QProgressBar {
    border: 1px solid #CED4DA;
    border-radius: 6px;
    text-align: center;
    background-color: #E9ECEF;
    height: 18px;
    color: #212529;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #0D6EFD;
    border-radius: 5px;
}

QMenuBar {
    background-color: #F8F9FA;
    border-bottom: 1px solid #DEE2E6;
    color: #212529;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    color: #212529;
}

QMenu::item:selected {
    background-color: #0D6EFD;
    color: #FFFFFF;
}

QToolTip {
    background-color: #212529;
    color: #FFFFFF;
    border: 1px solid #CED4DA;
    padding: 4px;
    border-radius: 4px;
}

QStatusBar {
    background-color: #F8F9FA;
    border-top: 1px solid #DEE2E6;
    color: #6C757D;
}
"""

MAIN_STYLE = DARK_THEME  # Default to dark theme to seamlessly match modern OS dark mode
