"""Global stylesheet and color constants for Lab Manager."""

C = COLORS = {
    "primary":"#f08914","primary_hover":"#d4770e","primary_dark":"#b5650c",
    "primary_fg":"#ffffff","primary_light":"#fff3e0",
    "destructive":"#dc2626","destructive_hover":"#b91c1c",
    "background":"#f1f5f9","card":"#ffffff","border":"#e2e8f0",
    "muted":"#f8fafc","muted_fg":"#64748b","foreground":"#0f172a",
    "input_bg":"#ffffff","ring":"#f08914",
    "green_bg":"#dcfce7","green_fg":"#14532d",
    "blue_bg":"#dbeafe","blue_fg":"#1e3a8a",
    "red_bg":"#fee2e2","red_fg":"#7f1d1d",
    "yellow_bg":"#fef9c3","yellow_fg":"#713f12",
    "purple_bg":"#f3e8ff","purple_fg":"#581c87",
    "orange_bg":"#ffedd5","orange_fg":"#9a3412",
    "stat_blue":"#1d4ed8","stat_blue_dark":"#1e40af","stat_blue_light":"#dbeafe",
    "stat_green":"#16a34a","stat_green_dark":"#15803d","stat_green_light":"#dcfce7",
    "stat_purple":"#7c3aed","stat_purple_dark":"#6d28d9","stat_purple_light":"#ede9fe",
    "stat_orange":"#ea580c","stat_orange_dark":"#c2410c","stat_orange_light":"#ffedd5",
    "stat_indigo":"#4f46e5","stat_indigo_dark":"#4338ca","stat_indigo_light":"#e0e7ff",
    "stat_red":"#ef4444","stat_red_dark":"#dc2626","stat_red_light":"#fee2e2",
    "sidebar":"#ffffff","sidebar_border":"#e2e8f0",
}

def _v(k): return COLORS[k]

MAIN_STYLE = f"""
QWidget{{border:none;font-family:'SF Pro Display','Helvetica Neue',Arial,sans-serif;font-size:14px;color:{C['foreground']};background:{C['background']};}}
QMainWindow{{background:{C['background']};}}
QLabel{{border:none;background:transparent;color:{C['foreground']};outline:none;}}
QScrollBar:vertical{{background:transparent;width:6px;margin:4px 0;border-radius:3px;}}
QScrollBar::handle:vertical{{background:{C['border']};border-radius:3px;min-height:32px;}}
QScrollBar::handle:vertical:hover{{background:{C['muted_fg']};}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QScrollBar:horizontal{{height:6px;background:transparent;border-radius:3px;margin:0 4px;}}
QScrollBar::handle:horizontal{{background:{C['border']};border-radius:3px;}}
QScrollBar::handle:horizontal:hover{{background:{C['muted_fg']};}}
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}
QPushButton{{border:none;padding:9px 18px;font-size:14px;font-weight:500;border-radius:6px;background:{C['muted']};color:{C['foreground']};}}
QLineEdit,QComboBox,QSpinBox,QTextEdit,QDateEdit{{background:{C['input_bg']};border:1.5px solid {C['border']};border-radius:6px;padding:8px 12px;font-size:14px;color:{C['foreground']};selection-background-color:{C['primary']};}}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QTextEdit:focus,QDateEdit:focus{{border:2px solid {C['ring']};outline:none;}}
QLineEdit:disabled,QComboBox:disabled,QSpinBox:disabled{{background:{C['muted']};color:{C['muted_fg']};}}
QComboBox::drop-down{{border:none;width:30px;}}
QComboBox::down-arrow{{image:none;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:5px solid {C['muted_fg']};}}
QComboBox QAbstractItemView{{background:white;border:1.5px solid {C['border']};border-radius:6px;selection-background-color:{C['primary_light']};selection-color:{C['foreground']};outline:none;padding:4px;}}
QComboBox QAbstractItemView::item{{padding:8px 12px;border-radius:4px;}}
QTableWidget{{background:{C['card']};border:none;gridline-color:{C['border']};selection-background-color:{C['primary_light']};selection-color:{C['foreground']};alternate-background-color:{C['muted']};}}
QTableWidget::item{{padding:10px 16px;border:none;}}
QTableWidget::item:selected{{background:{C['primary_light']};color:{C['foreground']};}}
QHeaderView::section{{background:{C['muted']};color:{C['muted_fg']};font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.5px;padding:10px 16px;border:none;border-right:1px solid {C['border']};border-bottom:2px solid {C['border']};}}
QHeaderView::section:last{{border-right:none;}}
QFrame#sidebar{{background:{C['sidebar']};border-right:1px solid {C['sidebar_border']};}}
QCheckBox{{spacing:10px;color:{C['foreground']};}}
QCheckBox::indicator{{width:17px;height:17px;border:2px solid {C['border']};border-radius:4px;background:white;}}
QCheckBox::indicator:checked{{background:{C['primary']};border-color:{C['primary']};}}
QRadioButton{{spacing:10px;color:{C['foreground']};}}
QRadioButton::indicator{{width:17px;height:17px;border:2px solid {C['border']};border-radius:9px;background:white;}}
QRadioButton::indicator:checked{{background:{C['primary']};border-color:{C['primary']};}}
QProgressBar{{border:none;background:{C['muted']};border-radius:4px;text-align:center;font-size:12px;color:{C['muted_fg']};}}
QProgressBar::chunk{{background:{C['primary']};border-radius:4px;}}
QToolTip{{background:{C['foreground']};color:white;border:none;border-radius:6px;padding:6px 10px;font-size:13px;}}
QDialog{{background:{C['background']};}}
QMessageBox{{background:{C['card']};}}
QMessageBox QPushButton{{min-width:80px;padding:8px 16px;}}
QGroupBox{{border:1.5px solid {C['border']};border-radius:8px;margin-top:14px;font-weight:600;font-size:13px;color:{C['muted_fg']};background:{C['card']};}}
QGroupBox::title{{subcontrol-origin:margin;subcontrol-position:top left;padding:0 8px;left:12px;color:{C['muted_fg']};}}
"""
