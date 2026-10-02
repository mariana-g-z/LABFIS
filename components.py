"""Reusable UI components for Lab Manager."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit,
    QSizePolicy, QScrollArea, QAbstractItemView, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from styles import COLORS as C

# ── Helpers ───────────────────────────────────────────────────────────────────

def _lbl(text, style="", wrap=False):
    l = QLabel(text)
    if style: l.setStyleSheet(style)
    if wrap:  l.setWordWrap(True)
    return l

def _btn(text, style="", cursor=True):
    b = QPushButton(text)
    if style:  b.setStyleSheet(style)
    if cursor: b.setCursor(Qt.PointingHandCursor)
    return b

def _frame(style="", layout_cls=QVBoxLayout, margins=(0,0,0,0), spacing=0):
    f = QFrame()
    if style: f.setStyleSheet(style)
    lay = layout_cls(f)
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return f, lay

def make_button(text, style_class="primary", large=False):
    b = QPushButton(text)
    b.setProperty("class", style_class + (" large" if large else ""))
    b.setCursor(Qt.PointingHandCursor)
    return b

def make_separator():
    l = QFrame()
    l.setFrameShape(QFrame.HLine)
    l.setStyleSheet(f"background:{C['border']};border:none;max-height:1px;")
    return l

def add_shadow(widget, blur=18, opacity=0.08, y=2):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, y)
    s.setColor(QColor(0, 0, 0, int(opacity * 255)))
    widget.setGraphicsEffect(s)

def _card_style(radius=10):
    return f"QFrame{{background:white;border:1px solid {C['border']};border-radius:{radius}px;}}"

# ── Badges ────────────────────────────────────────────────────────────────────

_BADGE_COLORS = {
    "Activo":        (C["green_bg"],  C["green_fg"]),
    "Devuelto":      (C["blue_bg"],   C["blue_fg"]),
    "Vencido":       (C["red_bg"],    C["red_fg"]),
    "Disponible":    (C["green_bg"],  C["green_fg"]),
    "Agotado":       (C["red_bg"],    C["red_fg"]),
    "Bajo Stock":    (C["yellow_bg"], C["yellow_fg"]),
    "Inactivo":      (C["red_bg"],    C["red_fg"]),
    "Becario":       (C["blue_bg"],   C["blue_fg"]),
    "Administrador": (C["purple_bg"], C["purple_fg"]),
    "Préstamo":      (C["orange_bg"], C["orange_fg"]),
    "Devolución":    (C["green_bg"],  C["green_fg"]),
}

def status_badge(text):
    bg, fg = _BADGE_COLORS.get(text, (C["muted"], C["muted_fg"]))
    l = QLabel(text)
    l.setAlignment(Qt.AlignCenter)
    l.setFixedHeight(24)
    l.setStyleSheet(
        f"background:{bg};color:{fg};border-radius:12px;"
        f"font-size:11px;font-weight:700;padding:0 10px;letter-spacing:.3px;"
    )
    return l

# ── Widgets ───────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label, value, color):
        super().__init__()
        self.setFixedHeight(120); self.setMinimumWidth(180)
        self.setStyleSheet(
            f"QFrame{{background:white;border:1px solid {C['border']};"
            f"border-radius:10px;border-left:4px solid {color};}}"
        )
        add_shadow(self, blur=16, opacity=0.06, y=2)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,16,20,16); lay.setSpacing(6)
        lay.addWidget(_lbl(value, f"font-size:30px;font-weight:700;color:{C['foreground']};background:transparent; border: none;"))
        lay.addWidget(_lbl(label, f"font-size:13px;color:{C['muted_fg']};background:transparent; border: none;"))
        lay.addStretch()


class SectionHeader(QWidget):
    def __init__(self, title, subtitle="", action_btn=None):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        col = QVBoxLayout(); col.setSpacing(4)
        col.addWidget(_lbl(title, f"font-size:22px;font-weight:700;color:{C['foreground']};"))
        if subtitle:
            col.addWidget(_lbl(subtitle, f"color:{C['muted_fg']};font-size:13px;"))
        lay.addLayout(col); lay.addStretch()
        if action_btn: lay.addWidget(action_btn)


class CardWidget(QFrame):
    def __init__(self, title=None):
        super().__init__()
        self.setStyleSheet(_card_style())
        add_shadow(self, blur=14, opacity=0.05, y=2)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0,0,0,0); self._lay.setSpacing(0)
        if title:
            hdr = QWidget()
            hdr.setStyleSheet(
                f"background:white;border-bottom:1px solid {C['border']};"
                f"border-top-left-radius:10px;border-top-right-radius:10px;border-radius:0;"
            )
            hl = QHBoxLayout(hdr); hl.setContentsMargins(20,14,20,14)
            hl.addWidget(_lbl(title, f"font-size:15px;font-weight:600;color:{C['foreground']}; border: none;"))
            self._lay.addWidget(hdr)

    def body_layout(self):
        body = QWidget(); body.setStyleSheet("background:transparent;")
        bl = QVBoxLayout(body); bl.setContentsMargins(20,16,20,16)
        self._lay.addWidget(body)
        return bl, body

    def add_widget(self, w): self._lay.addWidget(w)


class LabTable(QTableWidget):
    # Ordenados de más específico a más general para que el match largo gane
    _ICONS = {
       "ver historial": "🗒",
        "historial":     "🗒",
        "ver detalle":   "⌕",
        "detalle":       "⌕",
        "desactivar":    "⛔",
        "dar de baja":   "⛔",
        "activar":       "✔",
        "reactivar":     "✔",
        "reabastecer":   "▣",
        "reset pw":      "⚿",
        "resetear":      "⟳",
        "restablecer":   "⟳",
        "editar":        "✎",
        "devolver":      "↩",
        "eliminar":      "✕",
        "exportar":      "↓",
        "crear":         "＋",
        "ver":           "⌕"
    }
    _TIPS = {
        "ver historial": "Ver Historial", "historial":    "Ver Historial",
        "ver detalle":   "Ver Detalle",   "detalle":      "Ver Detalle",
        "desactivar":    "Desactivar",    "dar de baja":  "Dar de Baja",
        "activar":       "Activar",       "reactivar":    "Reactivar",
        "reabastecer":   "Reabastecer",
        "reset pw":      "Resetear Contraseña",
        "resetear":      "Resetear",      "restablecer":  "Restablecer",
        "editar":        "Editar",
        "devolver":      "Devolver",
        "eliminar":      "Eliminar",
        "exportar":      "Exportar",
        "crear":         "Crear",
        "ver":           "Ver Detalle",
    }

    def __init__(self, columns):
        super().__init__()
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setFocusPolicy(Qt.NoFocus)
        self.verticalHeader().setDefaultSectionSize(54)  # taller rows for icon buttons
        self.setMinimumHeight(300)
        self.setStyleSheet(f"""
            QTableWidget{{background:white;border:none;
                alternate-background-color:{C['muted']};gridline-color:transparent;
                selection-background-color:{C['primary_light']};}}
            QTableWidget::item{{padding:10px 16px;border-bottom:1px solid {C['border']};color:{C['foreground']};}}
            QTableWidget::item:selected{{background:{C['primary_light']};color:{C['foreground']};}}
            QHeaderView::section{{background:{C['muted']};color:{C['muted_fg']};font-weight:600;
                font-size:11px;text-transform:uppercase;letter-spacing:.5px;
                padding:10px 16px;border:none;border-bottom:2px solid {C['border']};
                border-right:1px solid {C['border']};}}
            QHeaderView::section:last{{border-right:none;}}
            QTableWidget QWidget {{ background: white; border: none; }}
            QTableWidget QPushButton {{ padding: 0; }}
        """)

    def set_badge_item(self, row, col, text):
        badge = status_badge(text)
        badge.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(w); lay.setContentsMargins(12,4,12,4)
        lay.addWidget(badge); lay.addStretch()
        self.setCellWidget(row, col, w)

    def add_item(self, row, col, text, mono=False):
        item = QTableWidgetItem(str(text) if text is not None else "")
        if mono:
            item.setFont(QFont("Consolas", 12))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.setItem(row, col, item)

    def add_actions(self, row, col, actions):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(w); lay.setContentsMargins(6,4,6,4); lay.setSpacing(4)
        for label, cb, danger in actions:
            key = label.lower().strip()
            icon = next((ic for k, ic in self._ICONS.items() if k in key), label[:2])
            tip  = next((t  for k, t  in self._TIPS.items()  if k in key), label)
            b = QPushButton(icon)
            b.setToolTip(tip); b.setCursor(Qt.PointingHandCursor); b.setFixedSize(30,30)
            b.setStyleSheet(
                f"QPushButton{{background:{C['red_bg']};border:1.5px solid {C['destructive']};"
                f"color:{C['destructive']};border-radius:6px;font-size:14px;font-weight:700;}}"
                f"QPushButton:hover{{background:{C['destructive']};color:white;}}"
                if danger else
                f"QPushButton{{background:{C['blue_bg']};border:1px solid {C['blue_fg']};"
                f"color:{C['blue_fg']};border-radius:6px;font-size:14px;font-weight:600;}}"
                f"QPushButton:hover{{background:{C['blue_fg']};color:white;}}"
            )
            if cb: b.clicked.connect(lambda checked=False, _cb=cb: _cb())
            lay.addWidget(b)
        lay.addStretch()
        self.setCellWidget(row, col, w)


class ConfirmDialog(QDialog):
    def __init__(self, parent, title, message, confirm_text="Confirmar", danger=False):
        super().__init__(parent)
        self.setWindowTitle(title); self.setModal(True)
        self.setFixedWidth(440); self.setStyleSheet("background:white;border-radius:12px;")
        lay = QVBoxLayout(self); lay.setContentsMargins(32,28,32,28); lay.setSpacing(16)

        row = QHBoxLayout()
        row.addWidget(_lbl(title, f"font-size:18px;font-weight:700;color:{C['foreground']};"))
        row.addStretch(); lay.addLayout(row)

        lay.addWidget(make_separator())
        lay.addWidget(_lbl(message, f"color:{C['muted_fg']};font-size:14px;", wrap=True))
        lay.addSpacing(8)

        btns = QHBoxLayout(); btns.setSpacing(12)
        cancel = _btn("Cancelar",
            f"QPushButton{{background:{C['muted']};border:1.5px solid {C['border']};"
            f"color:{C['foreground']};border-radius:6px;padding:10px 20px;font-size:14px;}}"
            f"QPushButton:hover{{background:{C['border']};}}")
        cancel.clicked.connect(self.reject); btns.addWidget(cancel)

        clr = C["destructive"] if danger else C["primary"]
        hov = C["destructive_hover"] if danger else C["primary_hover"]
        ok = _btn(confirm_text,
            f"QPushButton{{background:{clr};color:white;border:none;border-radius:6px;"
            f"padding:10px 20px;font-size:14px;font-weight:600;}}"
            f"QPushButton:hover{{background:{hov};}}")
        ok.clicked.connect(self.accept); btns.addWidget(ok)
        lay.addLayout(btns)


class Sidebar(QFrame):
    page_changed = Signal(str)

    def __init__(self, role="becario", username="Usuario"):
        super().__init__()
        self.setObjectName("sidebar"); self.setFixedWidth(230)
        self.setStyleSheet(f"QFrame#sidebar{{background:white;border-right:1px solid {C['border']};border-radius:0;}}")
        self._buttons = {}; self._active = None
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Header
        hdr = QWidget(); hdr.setFixedHeight(72)
        hdr.setStyleSheet(f"background:white;border-bottom:1px solid {C['border']};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16,0,16,0); hl.setSpacing(12)
        ico = _lbl("⚗", f"background:{C['primary']};color:white;border-radius:10px;font-size:18px;")
        ico.setFixedSize(40,40); ico.setAlignment(Qt.AlignCenter); hl.addWidget(ico)
        vl = QVBoxLayout(); vl.setSpacing(2)
        vl.addWidget(_lbl("Lab Manager", f"font-weight:700;font-size:14px;color:{C['foreground']};"))
        vl.addWidget(_lbl(role.capitalize(), f"font-size:11px;color:{C['muted_fg']};"))
        hl.addLayout(vl); lay.addWidget(hdr)

        # Nav
        nav_area = QScrollArea(); nav_area.setWidgetResizable(True)
        nav_area.setFrameShape(QFrame.NoFrame); nav_area.setStyleSheet("background:white;")
        nav_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_w = QWidget(); nav_w.setStyleSheet("background:white;")
        self._nav = QVBoxLayout(nav_w)
        self._nav.setContentsMargins(10,10,10,10); self._nav.setSpacing(2)
        nav_area.setWidget(nav_w); lay.addWidget(nav_area, 1)

        # Footer
        ftr = QWidget(); ftr.setFixedHeight(60)
        ftr.setStyleSheet(f"background:white;border-top:1px solid {C['border']};")
        fl = QVBoxLayout(ftr); fl.setContentsMargins(10,8,10,8)
        logout = _btn("  Cerrar Sesión",
            f"QPushButton{{background:transparent;color:{C['destructive']};text-align:left;"
            f"border:none;border-radius:8px;padding:8px 12px;font-size:14px;font-weight:500;}}"
            f"QPushButton:hover{{background:{C['red_bg']};}}")
        logout.clicked.connect(lambda: self.page_changed.emit("logout"))
        fl.addWidget(logout); lay.addWidget(ftr)

    def add_nav_item(self, icon, label, page_key):
        btn = _btn(f"  {icon}  {label}", self._style(False))
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setFixedHeight(42)
        btn.clicked.connect(lambda: self._click(page_key))
        self._nav.addWidget(btn)
        self._buttons[page_key] = btn

    def _style(self, active):
        if active:
            return (f"QPushButton{{background:{C['primary_light']};color:{C['primary']};"
                    f"text-align:left;border:none;border-radius:8px;padding:8px 12px;"
                    f"font-size:14px;font-weight:600;}}")
        return (f"QPushButton{{background:transparent;color:{C['foreground']};"
                f"text-align:left;border:none;border-radius:8px;padding:8px 12px;"
                f"font-size:14px;font-weight:400;}}"
                f"QPushButton:hover{{background:{C['muted']};}}")

    def _click(self, key):
        self.set_active(key); self.page_changed.emit(key)

    def set_active(self, key):
        if self._active and self._active in self._buttons:
            self._buttons[self._active].setStyleSheet(self._style(False))
        self._active = key
        if key in self._buttons:
            self._buttons[key].setStyleSheet(self._style(True))


class SearchBar(QLineEdit):
    def __init__(self, placeholder="Buscar..."):
        super().__init__()
        self.setPlaceholderText(f"  {placeholder}"); self.setFixedHeight(42)
        self.setStyleSheet(
            f"QLineEdit{{background:white;border:1.5px solid {C['border']};"
            f"border-radius:8px;padding:8px 16px;font-size:14px;}}"
            f"QLineEdit:focus{{border:2px solid {C['ring']};}}"
        )


class StepIndicator(QWidget):
    def __init__(self, steps, current=0):
        super().__init__(); self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self); lay.setAlignment(Qt.AlignCenter); lay.setSpacing(6)
        for i, _ in enumerate(steps):
            if i > 0:
                lay.addWidget(_lbl("───", f"color:{C['border']};font-size:14px;letter-spacing:-2px;"))
            circle = _lbl(str(i+1))
            circle.setFixedSize(30,30); circle.setAlignment(Qt.AlignCenter)
            if i == current:
                circle.setStyleSheet(f"background:{C['primary']};color:white;border-radius:15px;font-weight:700;font-size:13px;")
            elif i < current:
                circle.setStyleSheet(f"background:{C['green_bg']};color:{C['green_fg']};border-radius:15px;font-weight:700;font-size:13px;")
            else:
                circle.setStyleSheet(f"background:{C['muted']};color:{C['muted_fg']};border-radius:15px;font-size:13px;border:1.5px solid {C['border']};")
            lay.addWidget(circle)


class InfoRow(QWidget):
    def __init__(self, label, value):
        super().__init__(); self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        lbl = _lbl(label, f"color:{C['muted_fg']};font-size:13px;"); lbl.setFixedWidth(160)
        lay.addWidget(lbl)
        lay.addWidget(_lbl(value, f"color:{C['foreground']};font-weight:500;"))
        lay.addStretch()
