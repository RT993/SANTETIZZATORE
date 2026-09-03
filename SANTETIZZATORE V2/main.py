import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QStackedWidget, QToolButton, QGridLayout, QScrollArea, QScroller, QComboBox, QLineEdit, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QTimer, QEasingCurve, pyqtProperty, pyqtSignal, QSize, QRectF, QPointF, QUrl,
    QParallelAnimationGroup, QSequentialAnimationGroup, QPauseAnimation,
)
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QPainter, QLinearGradient, QBrush, QFontDatabase, QIcon, QPen, QPixmap, QRadialGradient, QPainterPath, QMovie
from PyQt5.QtWebEngineWidgets import QWebEngineView
import math
import feedparser
import webbrowser
import requests
import re
import json
import html
import datetime
import os

try:
    from PyQt5.QtMultimedia import QAudioRecorder, QAudioEncoderSettings, QMultimedia
    AUDIO_RECORDING_AVAILABLE = True
except ImportError:
    # QtMultimedia's audio backend isn't guaranteed on every platform (e.g. a
    # Raspberry Pi image without the right Qt multimedia/gstreamer plugins) -
    # degrade PregaScreen's voice recorder to a friendly message instead of
    # crashing the whole app at import time.
    AUDIO_RECORDING_AVAILABLE = False

# --- Vetrata theme ---
# The app's shared dark "stained glass" visual language: a deep navy
# background with soft colored glows, frosted-glass tiles/cards, warm
# gold accents, Spectral for headings and IBM Plex Mono for small
# data-readout labels (dates, timestamps, badges).

VETRATA_BG = QColor(14, 16, 24)
VETRATA_GLOW_BLUE = QColor(96, 116, 214)
VETRATA_GLOW_GOLD = QColor(200, 162, 74)
VETRATA_GLOW_PURPLE = QColor(72, 52, 140)

VETRATA_TEXT = QColor(242, 238, 226)          # warm cream - primary text
VETRATA_TEXT_DIM = QColor(169, 176, 196)      # body copy on cards
VETRATA_LABEL = QColor(143, 151, 174)         # muted blue-grey - small labels
VETRATA_GOLD = QColor(200, 162, 74)           # accent gold
VETRATA_GOLD_BRIGHT = QColor(253, 240, 207)   # text on gold-tinted glass

VETRATA_GLASS_BORDER = QColor(255, 255, 255, 51)
VETRATA_GLASS_BORDER_MUTED = QColor(255, 255, 255, 26)
VETRATA_GOLD_BORDER = QColor(255, 224, 160, 87)


def _vetrata_font_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def load_vetrata_fonts():
    # Bundled locally (SIL OFL) rather than fetched at runtime - this app
    # targets a Raspberry Pi kiosk that may have no internet at all.
    base = _vetrata_font_dir()
    families = {
        "Spectral": ["Spectral-Regular.ttf", "Spectral-Medium.ttf", "Spectral-SemiBold.ttf", "Spectral-Bold.ttf"],
        "IBMPlexMono": ["IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "IBMPlexMono-SemiBold.ttf", "IBMPlexMono-Bold.ttf"],
    }
    for folder, filenames in families.items():
        for filename in filenames:
            path = os.path.join(base, folder, filename)
            if os.path.exists(path):
                QFontDatabase.addApplicationFont(path)


# Static weight files register under distinct Qt family names for
# anything above Regular/Bold (verified against each file's own name
# table - Qt has no notion of a variable font's weight axis here).
_SPECTRAL_FAMILIES = {
    "regular": "Spectral", "medium": "Spectral Medium",
    "semibold": "Spectral SemiBold", "bold": "Spectral",
}
_PLEX_MONO_FAMILIES = {
    "regular": "IBM Plex Mono", "medium": "IBM Plex Mono Medium",
    "semibold": "IBM Plex Mono SemiBold", "bold": "IBM Plex Mono",
}


def spectral(size, weight="regular", italic=False):
    font = QFont(_SPECTRAL_FAMILIES.get(weight, "Spectral"), size)
    font.setBold(weight == "bold")
    font.setItalic(italic)
    return font


def plex_mono(size, weight="regular", letter_spacing=None):
    font = QFont(_PLEX_MONO_FAMILIES.get(weight, "IBM Plex Mono"), size)
    font.setBold(weight == "bold")
    if letter_spacing is not None:
        font.setLetterSpacing(QFont.AbsoluteSpacing, letter_spacing)
    return font


def click_through(widget):
    """Let clicks fall through a decorative child (a label sitting on top
    of a clickable GlassCard/VetrataPill) to the widget behind it - Qt
    delivers mouse events to whatever is topmost at that pixel, so
    without this a tap on a card's own title label would never reach
    the card's clicked signal."""
    widget.setAttribute(Qt.WA_TransparentForMouseEvents)
    return widget


def rgba_css(color):
    """QSS's color: property doesn't understand Qt's #AARRGGBB hex form,
    so any partially-transparent QColor needs to go through rgba(...)."""
    if color.alpha() >= 255:
        return color.name()
    return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255:.3f})"


def paint_vetrata_background(painter, rect):
    """Fill rect with the Vetrata base color plus its three soft glows -
    the shared background for every screen in this theme."""
    painter.fillRect(rect, VETRATA_BG)
    w, h = rect.width(), rect.height()
    glows = [
        (0.12 * w, -0.08 * h, 0.70 * w, VETRATA_GLOW_BLUE, 107),
        (0.96 * w, 0.08 * h, 0.58 * w, VETRATA_GLOW_GOLD, 77),
        (0.60 * w, 1.15 * h, 0.66 * w, VETRATA_GLOW_PURPLE, 115),
    ]
    for cx, cy, radius, color, alpha in glows:
        grad = QRadialGradient(cx, cy, radius)
        bright = QColor(color)
        bright.setAlpha(alpha)
        fade = QColor(color)
        fade.setAlpha(0)
        grad.setColorAt(0, bright)
        grad.setColorAt(1, fade)
        painter.fillRect(rect, QBrush(grad))


class GlassCard(QWidget):
    """A frosted-glass tile: a translucent rounded rect with a diagonal
    sheen, a hairline border and a soft drop shadow. Qt widgets have no
    real backdrop-filter/blur (that needs compositor access to whatever
    is behind the widget, which the QWidget paint model doesn't expose),
    so this fakes the "glass" read with a bright-to-dim gradient fill
    instead - visually close, and far cheaper to render repeatedly on a
    Raspberry Pi than a true per-frame blur would be.
    """
    _VARIANTS = {
        "default": {
            "stops": [(0.0, QColor(255, 255, 255, 51)), (0.58, QColor(255, 255, 255, 13)), (1.0, QColor(255, 255, 255, 23))],
            "border": VETRATA_GLASS_BORDER,
            "shadow": True,
        },
        "accent": {
            "stops": [(0.0, QColor(255, 225, 160, 77)), (0.60, QColor(200, 162, 74, 26)), (1.0, QColor(255, 235, 190, 36))],
            "border": VETRATA_GOLD_BORDER,
            "shadow": True,
        },
        "muted": {
            "stops": [(0.0, QColor(255, 255, 255, 26)), (1.0, QColor(255, 255, 255, 8))],
            "border": VETRATA_GLASS_BORDER_MUTED,
            "shadow": False,
        },
    }

    clicked = pyqtSignal()

    def __init__(self, variant="default", radius=26, clickable=False, parent=None):
        super().__init__(parent)
        self._variant = self._VARIANTS.get(variant, self._VARIANTS["default"])
        self._radius = radius
        self._pressed_inside = False
        if clickable:
            self.setCursor(Qt.PointingHandCursor)
        if self._variant["shadow"]:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(28)
            effect.setOffset(0, 10)
            effect.setColor(QColor(8, 10, 18, 82))
            self.setGraphicsEffect(effect)

    def mousePressEvent(self, event):
        self._pressed_inside = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pressed_inside and self.rect().contains(event.pos()):
            self.clicked.emit()
        self._pressed_inside = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75)
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        for stop, color in self._variant["stops"]:
            grad.setColorAt(stop, color)
        painter.fillPath(path, QBrush(grad))
        pen = QPen(self._variant["border"])
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.drawPath(path)
        super().paintEvent(event)


def draw_tile_glyph(painter, kind, rect, color, weight=5.5):
    """Draw one of the home-menu's small monoline icons, hand-drawn with
    QPainterPath instead of bundling bitmap icon assets - they scale
    crisply at any size and match the theme's exact palette for free.
    Each glyph is authored in a fixed 100x100 unit box, then scaled and
    translated to fit `rect`."""
    painter.save()
    scale = min(rect.width(), rect.height()) / 100.0
    painter.translate(rect.x() + (rect.width() - 100 * scale) / 2, rect.y() + (rect.height() - 100 * scale) / 2)
    painter.scale(scale, scale)
    pen = QPen(color, weight)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if kind == "saint":
        # Halo, head, and robe shoulders.
        painter.drawEllipse(QRectF(30, 12, 40, 15))
        painter.drawEllipse(QRectF(39, 28, 22, 22))
        robe = QPainterPath()
        robe.moveTo(28, 88)
        robe.cubicTo(28, 56, 72, 56, 72, 88)
        painter.drawPath(robe)
    elif kind == "book":
        spine = QPainterPath()
        spine.moveTo(50, 26)
        spine.lineTo(50, 80)
        painter.drawPath(spine)
        left_page = QPainterPath()
        left_page.moveTo(50, 32)
        left_page.cubicTo(36, 24, 20, 27, 15, 34)
        left_page.lineTo(15, 74)
        left_page.cubicTo(20, 67, 36, 66, 50, 74)
        painter.drawPath(left_page)
        right_page = QPainterPath()
        right_page.moveTo(50, 32)
        right_page.cubicTo(64, 24, 80, 27, 85, 34)
        right_page.lineTo(85, 74)
        right_page.cubicTo(80, 67, 64, 66, 50, 74)
        painter.drawPath(right_page)
    elif kind == "candle":
        flame = QPainterPath()
        flame.moveTo(50, 14)
        flame.cubicTo(60, 27, 60, 40, 50, 46)
        flame.cubicTo(40, 40, 40, 27, 50, 14)
        flame.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.drawPath(flame)
        painter.setBrush(Qt.NoBrush)
        base = QPainterPath()
        base.addRoundedRect(QRectF(41, 52, 18, 34), 4, 4)
        painter.drawPath(base)
    elif kind == "vatican":
        dome = QPainterPath()
        dome.moveTo(22, 78)
        dome.cubicTo(22, 40, 78, 40, 78, 78)
        painter.drawPath(dome)
        painter.drawLine(QPointF(18, 82), QPointF(82, 82))
        painter.drawLine(QPointF(50, 12), QPointF(50, 34))
        painter.drawLine(QPointF(40, 20), QPointF(60, 20))
    elif kind == "bell":
        body = QPainterPath()
        body.moveTo(30, 72)
        body.cubicTo(30, 34, 70, 34, 70, 72)
        body.lineTo(76, 80)
        body.lineTo(24, 80)
        body.closeSubpath()
        painter.drawPath(body)
        painter.drawEllipse(QPointF(50, 89), 5, 5)
        painter.drawArc(QRectF(42, 18, 16, 16), 0, 360 * 16)
    elif kind == "pin":
        pin = QPainterPath()
        pin.moveTo(50, 87)
        pin.cubicTo(32, 66, 24, 51, 24, 39)
        pin.cubicTo(24, 20, 36, 10, 50, 10)
        pin.cubicTo(64, 10, 76, 20, 76, 39)
        pin.cubicTo(76, 51, 68, 66, 50, 87)
        pin.closeSubpath()
        painter.drawPath(pin)
        painter.drawEllipse(QPointF(50, 39), 10, 10)

    painter.restore()


class TileIcon(QWidget):
    """A small fixed-size widget that paints one draw_tile_glyph() icon."""
    def __init__(self, kind, color, size=40, parent=None):
        super().__init__(parent)
        self.kind = kind
        self.color = color
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        draw_tile_glyph(painter, self.kind, QRectF(self.rect()), self.color)
        super().paintEvent(event)


class VetrataPill(QWidget):
    """A rounded pill button in glass or gold-filled style, used for
    filter chips, the back button, and secondary actions."""
    clicked = pyqtSignal()

    def __init__(self, filled=False, radius=999, parent=None):
        super().__init__(parent)
        self._filled = filled
        self._radius = radius
        self._pressed_inside = False

    def mousePressEvent(self, event):
        self._pressed_inside = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pressed_inside and self.rect().contains(event.pos()):
            self.clicked.emit()
        self._pressed_inside = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.75, 0.75, -0.75, -0.75)
        radius = min(self._radius, rect.height() / 2)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        if self._filled:
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0.0, QColor(255, 232, 175, 242))
            grad.setColorAt(1.0, QColor(200, 162, 74, 217))
            painter.fillPath(path, QBrush(grad))
            pen = QPen(QColor(255, 255, 255, 140))
        else:
            painter.fillPath(path, QBrush(QColor(255, 255, 255, 20)))
            pen = QPen(QColor(255, 255, 255, 46))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.drawPath(path)
        super().paintEvent(event)


class ShineLabel(QWidget):
    def __init__(self, text, font, color):
        super().__init__()
        self.text = text
        self.font = font
        self.color = color
        self._opacity = 1.0
        self._scale = 1.0
        self._shine_pos = -0.5
        self.setMinimumHeight(80)
        self.setMinimumWidth(400)

    def setOpacity(self, opacity):
        self._opacity = opacity
        self.update()

    def getOpacity(self):
        return self._opacity

    def setScale(self, scale):
        self._scale = scale
        self.update()

    def getScale(self):
        return self._scale

    def setShinePos(self, pos):
        self._shine_pos = pos
        self.update()

    def getShinePos(self):
        return self._shine_pos

    opacity = pyqtProperty(float, fget=getOpacity, fset=setOpacity)
    scale = pyqtProperty(float, fget=getScale, fset=setScale)
    shine_pos = pyqtProperty(float, fget=getShinePos, fset=setShinePos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.setFont(self.font)
        # Draw text base
        painter.setPen(QColor(self.color))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)
        # Draw shine (only once, not looping)
        if -0.2 <= self._shine_pos <= 1.2:
            # The sweep animates shine_pos from -0.5 to 1.5 so it travels
            # fully on/off the label, but QGradient stops must lie in
            # [0, 1] - the old single-sided max()/min() clamps here still
            # let shine_pos-0.1/shine_pos+0.1 go negative or past 1 for
            # part of that range, which Qt was silently rejecting.
            def stop(x):
                return min(1.0, max(0.0, x))
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0, QColor(255, 255, 255, 0))
            grad.setColorAt(stop(self._shine_pos - 0.1), QColor(255, 255, 255, 0))
            grad.setColorAt(stop(self._shine_pos), QColor(255, 255, 255, 180))
            grad.setColorAt(stop(self._shine_pos + 0.1), QColor(255, 255, 255, 0))
            grad.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.setCompositionMode(QPainter.CompositionMode_Screen)
            painter.drawRect(self.rect())
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

class CinematicIntro(QWidget):
    def __init__(self, on_finished=None):
        super().__init__()
        self.setWindowTitle("SANTETIZZATORE")
        self.setFixedSize(1080, 720)
        self.on_finished = on_finished

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        # Main Title
        self.title_label = ShineLabel("SANTETIZZATORE", spectral(40, "semibold"), VETRATA_GOLD.name())
        self.title_label.setFixedHeight(80)

        # Subtitle
        credit_font = QFont("Arial", 13)
        self.credit_label = ShineLabel("Ora pro nobis", credit_font, VETRATA_LABEL.name())
        self.credit_label.setFixedHeight(30)

        # Thin gold loading bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(
            """
            QProgressBar { background: rgba(255,255,255,0.15); border: none; border-radius: 2px; }
            QProgressBar::chunk { background: #c8a24a; border-radius: 2px; }
            """
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.credit_label)
        layout.addSpacing(20)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        # Animations
        self.anim_title_opacity = QPropertyAnimation(self.title_label, b"opacity")
        self.anim_title_opacity.setDuration(900)
        self.anim_title_opacity.setStartValue(0.0)
        self.anim_title_opacity.setEndValue(1.0)
        self.anim_title_opacity.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_title_scale = QPropertyAnimation(self.title_label, b"scale")
        self.anim_title_scale.setDuration(900)
        self.anim_title_scale.setStartValue(0.7)
        self.anim_title_scale.setEndValue(1.0)
        self.anim_title_scale.setEasingCurve(QEasingCurve.OutBack)

        self.anim_shine = QPropertyAnimation(self.title_label, b"shine_pos")
        self.anim_shine.setDuration(1200)
        self.anim_shine.setStartValue(-0.5)
        self.anim_shine.setEndValue(1.5)
        self.anim_shine.setEasingCurve(QEasingCurve.InOutCubic)

        self.anim_credit = QPropertyAnimation(self.credit_label, b"opacity")
        self.anim_credit.setDuration(700)
        self.anim_credit.setStartValue(0.0)
        self.anim_credit.setEndValue(1.0)
        self.anim_credit.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_progress = QPropertyAnimation(self.progress, b"value")
        self.anim_progress.setDuration(2000)
        self.anim_progress.setStartValue(0)
        self.anim_progress.setEndValue(100)
        self.anim_progress.setEasingCurve(QEasingCurve.InOutCubic)

        # Animation sequence
        self.anim_title_opacity.finished.connect(self.anim_title_scale.start)
        self.anim_title_scale.finished.connect(self.anim_shine.start)
        self.anim_shine.finished.connect(self.anim_credit.start)
        self.anim_credit.finished.connect(self.anim_progress.start)
        self.anim_progress.finished.connect(self.close_after_delay)

        # Start
        self.anim_title_opacity.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

    def close_after_delay(self):
        QTimer.singleShot(1000, self.finish)

    def finish(self):
        if self.on_finished:
            self.on_finished()
        self.close()

# --- Onboarding Screen ---
class OnboardingScreen(QWidget):
    def __init__(self, theme_toggle_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignVCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignVCenter)
        layout.setContentsMargins(32, 32, 32, 32)

        # Welcome title, with a soft gold glow
        title = QLabel("Benvenuto in SANTETIZZATORE")
        title.setFont(spectral(34, "semibold"))
        title.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        title.setAlignment(Qt.AlignHCenter)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(36)
        glow.setColor(QColor(200, 162, 74, 160))
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        layout.addWidget(title)
        layout.addSpacing(10)

        motto = QLabel("Ora pro nobis")
        motto.setFont(QFont("Arial", 16))
        motto.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
        motto.setAlignment(Qt.AlignHCenter)
        layout.addWidget(motto)
        layout.addSpacing(36)

        self.cont_btn = QPushButton("Continua")
        self.cont_btn.setFont(QFont("Arial", 15, QFont.Bold))
        self.cont_btn.setMinimumHeight(48)
        self.cont_btn.setMaximumWidth(200)
        self.cont_btn.setCursor(Qt.PointingHandCursor)
        self.cont_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,232,175,0.95), stop:1 rgba(200,162,74,0.85));
                color: #1a1710;
                border: 1px solid rgba(255,255,255,0.55);
                border-radius: 24px;
                font-weight: bold;
                font-size: 15px;
                min-height: 48px;
                max-width: 200px;
                padding: 6px 24px;
            }
            QPushButton:pressed {
                background: #c8a24a;
            }
        """)
        self.cont_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.cont_btn, alignment=Qt.AlignHCenter)
        layout.addSpacing(4)

        main_layout.addLayout(layout)
        self.setLayout(main_layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
    from PyQt5.QtCore import pyqtSignal
    clicked = pyqtSignal()

# --- Main Menu Screen ---
PROMEMORIA_TIMES = [
    ("Preghiera del mattino", "07:00"),
    ("Preghiera di mezzogiorno", "12:00"),
    ("Preghiera della sera", "16:00"),
    ("Preghiera della notte", "20:00"),
]


class MainMenuScreen(QWidget):
    def __init__(self, promemoria_callback=None, vatican_callback=None, saint_callback=None, prega_callback=None, bible_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.promemoria_callback = promemoria_callback
        self.vatican_callback = vatican_callback
        self.saint_callback = saint_callback
        self.prega_callback = prega_callback
        self.bible_callback = bible_callback
        self.vatican_headline = None

        self.saints = self._load_json("saints.json")
        self.readings = self._load_json("bible_readings.json")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(28, 20, 28, 20)
        header_wrap = QWidget()
        header_wrap.setLayout(header)
        header_wrap.setStyleSheet("background: transparent; border-bottom: 1px solid rgba(255,255,255,0.1);")

        title_row = QHBoxLayout()
        title_row.setSpacing(14)
        wordmark = QLabel("SANTETIZZATORE")
        wordmark.setFont(spectral(26, "semibold"))
        wordmark.setStyleSheet(f"color: {VETRATA_GOLD.name()}; background: transparent;")
        title_row.addWidget(wordmark, alignment=Qt.AlignBottom)
        motto = QLabel("Ora pro nobis")
        motto.setFont(QFont("Arial", 15))
        motto.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
        title_row.addWidget(motto, alignment=Qt.AlignBottom)
        header.addLayout(title_row)
        header.addStretch()

        clock_row = QHBoxLayout()
        clock_row.setSpacing(20)
        self.date_label = QLabel()
        self.date_label.setFont(plex_mono(14))
        self.date_label.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
        clock_row.addWidget(self.date_label, alignment=Qt.AlignBottom)
        self.time_label = QLabel()
        self.time_label.setFont(plex_mono(18))
        self.time_label.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        clock_row.addWidget(self.time_label, alignment=Qt.AlignBottom)
        header.addLayout(clock_row)

        layout.addWidget(header_wrap)
        layout.addStretch(1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.setContentsMargins(20, 18, 20, 18)

        TILE_HEIGHT = 148

        tiles = [
            ("Santo del giorno", "saint", "default", self._today_saint_name, self.saint_clicked),
            ("Letture bibliche", "book", "default", self._today_reading_ref, self.bible_clicked),
            ("Prega", "candle", "accent", "Intenzione personale", self.prega_clicked),
            ("Dal Vaticano", "vatican", "default", self._vatican_subtitle, self.vatican_clicked),
            ("Promemoria", "bell", "default", self._next_reminder_text, self.reminder_clicked),
            ("Trova chiese", "pin", "muted", "Richiede connessione", None),
        ]
        self.tile_subtitles = {}
        for idx, (title_text, icon_kind, variant, subtitle, callback) in enumerate(tiles):
            row, col = idx // 3, idx % 3
            card = GlassCard(variant=variant, clickable=callback is not None)
            card.setFixedHeight(TILE_HEIGHT)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(20, 18, 20, 18)
            card_layout.setSpacing(16)

            title_color = VETRATA_GOLD_BRIGHT if variant == "accent" else (
                QColor(240, 240, 250, 107) if variant == "muted" else VETRATA_TEXT)
            icon_color = VETRATA_GOLD_BRIGHT if variant == "accent" else (
                QColor(240, 240, 250, 107) if variant == "muted" else VETRATA_GOLD)
            icon = click_through(TileIcon(icon_kind, icon_color, size=38))
            card_layout.addWidget(icon, alignment=Qt.AlignTop)

            text_col = QVBoxLayout()
            text_col.setSpacing(5)
            text_col.addStretch()
            title_lbl = QLabel(title_text)
            title_lbl.setFont(spectral(21))
            title_lbl.setStyleSheet(f"color: {rgba_css(title_color)}; background: transparent;")
            title_lbl.setWordWrap(True)
            text_col.addWidget(click_through(title_lbl))
            subtitle_lbl = QLabel(subtitle if isinstance(subtitle, str) else "")
            subtitle_lbl.setFont(QFont("Arial", 13))
            sub_color = QColor(253, 240, 207, 191) if variant == "accent" else (
                QColor(240, 240, 250, 87) if variant == "muted" else QColor(240, 240, 250, 173))
            subtitle_lbl.setStyleSheet(f"color: {rgba_css(sub_color)}; background: transparent;")
            subtitle_lbl.setWordWrap(True)
            text_col.addWidget(click_through(subtitle_lbl))
            card_layout.addLayout(text_col, 1)

            if callable(subtitle):
                self.tile_subtitles[title_text] = (subtitle_lbl, subtitle)
            if callback:
                card.clicked.connect(callback)
            grid.addWidget(card, row, col)
        layout.addLayout(grid)
        layout.addStretch(2)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()
        self.refresh()

    def _load_json(self, filename):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def _today_key(self):
        return datetime.datetime.now().strftime("%m-%d")

    def _today_saint_name(self):
        day_key = self._today_key()
        saint = next((s for s in self.saints if s.get("day") == day_key), None)
        if not saint and day_key == "02-29":
            saint = next((s for s in self.saints if s.get("day") == "02-28"), None)
        return saint["name"] if saint else "—"

    def _today_reading_ref(self):
        day_key = self._today_key()
        reading = next((r for r in self.readings if r.get("day") == day_key), None)
        if not reading and day_key == "02-29":
            reading = next((r for r in self.readings if r.get("day") == "02-28"), None)
        return reading.get("reference", "—") if reading else "—"

    def _vatican_subtitle(self):
        return self.vatican_headline or "Ultime notizie dal Papa"

    def _next_reminder_text(self):
        now = datetime.datetime.now().time()
        for label, time_str in PROMEMORIA_TIMES:
            h, m = (int(x) for x in time_str.split(":"))
            if (h, m) >= (now.hour, now.minute):
                return f"{label} · {time_str}"
        label, time_str = PROMEMORIA_TIMES[0]
        return f"{label} · {time_str}"

    def set_vatican_headline(self, headline):
        self.vatican_headline = headline
        self.refresh()

    def refresh(self):
        # Re-reads today's saint/reading and the next reminder time - call
        # whenever the menu becomes visible again, so nothing goes stale
        # across midnight or a long idle period on the kiosk.
        for title_text, (label, getter) in self.tile_subtitles.items():
            label.setText(getter())

    def _update_clock(self):
        now = datetime.datetime.now()
        self.date_label.setText(now.strftime("%d.%m.%Y"))
        self.time_label.setText(now.strftime("%H:%M"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

    def saint_clicked(self):
        if self.saint_callback:
            self.saint_callback()
    def bible_clicked(self):
        if self.bible_callback:
            self.bible_callback()
    def reminder_clicked(self):
        if self.promemoria_callback:
            self.promemoria_callback()
    def vatican_clicked(self):
        if self.vatican_callback:
            self.vatican_callback()
    def prega_clicked(self):
        if self.prega_callback:
            self.prega_callback()

# --- Promemoria Screen ---
class PromemoriaScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        # Centered card
        card = GlassCard(variant="default", radius=28)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 40, 48, 44)
        card_layout.setSpacing(28)
        # Top bar: back icon + title
        top_bar = QHBoxLayout()
        top_bar.setSpacing(18)
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(64, 64)
            back_icon.setStyleSheet("background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22); border-radius: 32px;")
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Promemoria")
        title.setFont(spectral(26))
        title.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        top_bar.addWidget(click_through(title), alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        card_layout.addLayout(top_bar)
        # Analog clock
        clock = AnalogClock()
        card_layout.addWidget(clock, alignment=Qt.AlignHCenter)
        # Reminders
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(24)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        for i, (label, time) in enumerate(PROMEMORIA_TIMES):
            font = QFont("Arial", 20, QFont.Normal)
            lbl = QLabel(label)
            lbl.setFont(font)
            lbl.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
            time_lbl = QLabel(time)
            time_lbl.setFont(plex_mono(20))
            time_lbl.setStyleSheet(f"color: {VETRATA_GOLD.name()}; background: transparent;")
            time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            switch = IOSSwitch(checked=True)
            switch.setFixedSize(60, 38)
            grid.addWidget(click_through(lbl), i, 0, alignment=Qt.AlignVCenter)
            grid.addWidget(click_through(time_lbl), i, 1, alignment=Qt.AlignVCenter)
            grid.addWidget(switch, i, 2, alignment=Qt.AlignVCenter)
        card_layout.addLayout(grid)
        card_layout.addStretch()
        margin = QVBoxLayout()
        margin.setContentsMargins(60, 40, 60, 40)
        margin.addWidget(card)
        outer_layout.addLayout(margin)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

class AnalogClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setMaximumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        import datetime
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        side = min(rect.width(), rect.height())
        center = rect.center()
        # Draw clock face - a frosted-glass dial matching GlassCard's look
        painter.setBrush(QColor(255, 255, 255, 23))
        painter.setPen(QPen(QColor(255, 255, 255, 51), 1.5))
        painter.drawEllipse(center, side//2-4, side//2-4)
        # Draw ticks
        painter.setPen(QPen(QColor(240, 240, 250, 130), 2))
        for i in range(60):
            angle = i * 6
            r1 = side//2-16
            r2 = side//2-8 if i%5==0 else side//2-12
            x1 = center.x() + r1 * math.cos(math.radians(angle-90))
            y1 = center.y() + r1 * math.sin(math.radians(angle-90))
            x2 = center.x() + r2 * math.cos(math.radians(angle-90))
            y2 = center.y() + r2 * math.sin(math.radians(angle-90))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        # Draw hands
        now = datetime.datetime.now()
        hour = now.hour % 12 + now.minute/60.0
        minute = now.minute + now.second/60.0
        second = now.second
        # Hour hand
        painter.setPen(QPen(QColor(242, 238, 226), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(center.x() + 0.45*side*math.cos(math.radians(hour*30-90)), center.y() + 0.45*side*math.sin(math.radians(hour*30-90))))
        # Minute hand
        painter.setPen(QPen(QColor(200, 162, 74), 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(center.x() + 0.65*side*math.cos(math.radians(minute*6-90)), center.y() + 0.65*side*math.sin(math.radians(minute*6-90))))
        # Second hand
        painter.setPen(QPen(QColor(255, 224, 160), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(center.x() + 0.7*side*math.cos(math.radians(second*6-90)), center.y() + 0.7*side*math.sin(math.radians(second*6-90))))
        # Center dot
        painter.setBrush(QColor(200, 162, 74))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, 7, 7)
        painter.end()

class IOSSwitch(QWidget):
    def __init__(self, parent=None, checked=True):
        super().__init__(parent)
        self.setFixedSize(44, 28)
        self._checked = checked
        self._thumb_pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"thumb_pos", self)
        self._anim.setDuration(120)
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._anim.stop()
            self._anim.setStartValue(self._thumb_pos)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            self.clicked.emit(self._checked)

    def sizeHint(self):
        return QSize(44, 28)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Track
        track_rect = QRectF(2, 7, 40, 14)
        if self._checked or self._thumb_pos > 0:
            grad = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
            grad.setColorAt(0, QColor(76, 217, 100) if self._thumb_pos > 0.5 else QColor(229, 229, 234))
            grad.setColorAt(1, QColor(76, 217, 100) if self._thumb_pos > 0.5 else QColor(229, 229, 234))
            painter.setBrush(QBrush(grad))
        else:
            painter.setBrush(QColor(229, 229, 234))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 7, 7)
        # Thumb
        x = 2 + self._thumb_pos * 20
        thumb_rect = QRectF(x, 4, 20, 20)
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawEllipse(thumb_rect)
        # Shadow
        painter.setBrush(QColor(0, 0, 0, 18))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(x, 22, 20, 4))

    def get_thumb_pos(self):
        return self._thumb_pos
    def set_thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()
    thumb_pos = pyqtProperty(float, fget=get_thumb_pos, fset=set_thumb_pos)

    # Signal for toggling
    from PyQt5.QtCore import pyqtSignal
    clicked = pyqtSignal(bool)

# --- News Vaticano Screen ---
class NewsVaticanoScreen(QWidget):
    def __init__(self, back_callback=None, open_in_app_browser=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.open_in_app_browser = open_in_app_browser
        self.entries = []
        self.latest_headline = None
        self.active_filter = "Tutto"

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(28, 20, 28, 20)
        outer_layout.setSpacing(16)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(18)
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(64, 64)
            back_icon.setStyleSheet("background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22); border-radius: 32px;")
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Dal Vaticano")
        title.setFont(spectral(28))
        title.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()

        self.filter_buttons = {}
        for label in ("Tutto", "Udienze"):
            pill = VetrataPill(filled=(label == self.active_filter))
            pill.setFixedHeight(48)
            pill.setMinimumWidth(90)
            pill.setCursor(Qt.PointingHandCursor)
            text_lbl = QLabel(label, pill)
            text_color = QColor(26, 23, 16) if label == self.active_filter else QColor(240, 240, 250, 191)
            text_lbl.setStyleSheet(f"color: {rgba_css(text_color)}; background: transparent; font-weight: 600;")
            text_lbl.setFont(QFont("Arial", 15))
            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(18, 0, 18, 0)
            pill_layout.addWidget(click_through(text_lbl), alignment=Qt.AlignCenter)
            pill.clicked.connect(lambda l=label: self._set_filter(l))
            self.filter_buttons[label] = (pill, text_lbl)
            top_bar.addWidget(pill)
        outer_layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.viewport().setStyleSheet("background: transparent;")
        QScroller.grabGesture(scroll.viewport(), QScroller.LeftMouseButtonGesture)
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        news_layout = QVBoxLayout(content)
        news_layout.setSpacing(14)
        news_layout.setContentsMargins(0, 0, 0, 4)
        self.news_layout = news_layout
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner_movie = QMovie("assets/loading_spinner.gif")
        self.spinner.setMovie(self.spinner_movie)
        self.spinner_movie.start()
        self.news_layout.addWidget(self.spinner)

        self.load_news()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

    def _set_filter(self, label):
        if label == self.active_filter:
            return
        self.active_filter = label
        for name, (pill, text_lbl) in self.filter_buttons.items():
            pill._filled = (name == label)
            text_lbl.setStyleSheet(
                f"color: {rgba_css(QColor(26, 23, 16) if name == label else QColor(240, 240, 250, 191))}; "
                "background: transparent; font-weight: 600;"
            )
            pill.update()
        self._render_entries()

    def load_news(self):
        feed_url = "https://www.vaticannews.va/it.rss.xml"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as e:
            print("Network or fetch error:", e)
            feed = feedparser.parse("")
        self.spinner_movie.stop()
        self.entries = feed.entries[:10]
        self.latest_headline = self.entries[0].title if self.entries else None
        self._render_entries()

    def _matches_filter(self, entry):
        if self.active_filter == "Tutto":
            return True
        haystack = (getattr(entry, "title", "") + " " + getattr(entry, "summary", "")).lower()
        return "udienz" in haystack

    def _render_entries(self):
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            widget = item.widget()
            if widget:
                # takeAt() only detaches from the layout - the widget stays
                # visible at its last geometry until deleteLater()'s
                # deferred deletion actually runs, so hide it now too.
                widget.hide()
                widget.deleteLater()

        if not self.entries:
            msg = QLabel("Nessuna notizia disponibile.")
            msg.setFont(QFont("Arial", 14, QFont.Bold))
            msg.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
            self.news_layout.addWidget(msg)
            return

        shown = [e for e in self.entries if self._matches_filter(e)]
        if not shown:
            msg = QLabel("Nessuna notizia in questa categoria.")
            msg.setFont(QFont("Arial", 14, QFont.Bold))
            msg.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
            self.news_layout.addWidget(msg)
            return

        for entry in shown:
            card = GlassCard(variant="default", radius=22, clickable=True)
            link = entry.link
            card.clicked.connect(lambda checked=False, url=link: self.open_in_app_browser(url) if self.open_in_app_browser else webbrowser.open(url))
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(22, 20, 22, 20)
            card_layout.setSpacing(20)

            img_url = None
            if 'media_content' in entry and entry.media_content:
                img_url = entry.media_content[0].get('url')
            elif 'media_thumbnail' in entry and entry.media_thumbnail:
                img_url = entry.media_thumbnail[0].get('url')
            thumb_w, thumb_h = 140, 100
            img_label = QLabel()
            img_label.setFixedSize(thumb_w, thumb_h)
            img_label.setStyleSheet("background: rgba(255,255,255,0.08); border-radius: 14px;")
            if img_url:
                try:
                    img_data = requests.get(img_url, timeout=5).content
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    rounded = QPixmap(thumb_w, thumb_h)
                    rounded.fill(Qt.transparent)
                    p = QPainter(rounded)
                    p.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, thumb_w, thumb_h, 14, 14)
                    p.setClipPath(path)
                    p.drawPixmap(0, 0, pixmap.scaled(thumb_w, thumb_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    p.end()
                    img_label.setPixmap(rounded)
                except Exception as e:
                    print("Image load error:", e)
            card_layout.addWidget(click_through(img_label), alignment=Qt.AlignTop)

            content_layout = QVBoxLayout()
            content_layout.setSpacing(6)
            if hasattr(entry, 'published'):
                date_lbl = QLabel(entry.published)
                date_lbl.setFont(plex_mono(12, letter_spacing=1))
                date_lbl.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
                content_layout.addWidget(click_through(date_lbl))
            title_lbl = QLabel(entry.title)
            title_lbl.setFont(spectral(22))
            title_lbl.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
            title_lbl.setWordWrap(True)
            content_layout.addWidget(click_through(title_lbl))
            summary_text = entry.summary
            summary_text = re.sub(r'<a [^>]*>\s*Leggi tutto\s*</a>', '', summary_text, flags=re.IGNORECASE)
            summary_text = re.sub(r'Leggi tutto', '', summary_text, flags=re.IGNORECASE)
            summary = QLabel(summary_text)
            summary.setFont(QFont("Arial", 14))
            summary.setStyleSheet(f"color: {VETRATA_TEXT_DIM.name()}; background: transparent;")
            summary.setWordWrap(True)
            content_layout.addWidget(click_through(summary))
            card_layout.addLayout(content_layout, 1)

            open_pill = VetrataPill(filled=False)
            click_through(open_pill)
            open_pill.setFixedSize(90, 48)
            open_text = QLabel("Apri", open_pill)
            open_text.setStyleSheet(f"color: {rgba_css(QColor(246, 243, 234))}; background: transparent; font-weight: 600;")
            open_text.setFont(QFont("Arial", 15))
            open_pill_layout = QHBoxLayout(open_pill)
            open_pill_layout.setContentsMargins(0, 0, 0, 0)
            open_pill_layout.addWidget(click_through(open_text), alignment=Qt.AlignCenter)
            card_layout.addWidget(open_pill, alignment=Qt.AlignTop)

            self.news_layout.addWidget(card)

# --- Saint of the Day Screen ---
class SaintOfTheDayScreen(QWidget):
    # A rectangle this narrow stays clear of the ring at every scroll
    # position - the previous near-full-diameter content box was wider
    # than the square that can actually be inscribed in the circle
    # (max side ~= diameter / sqrt(2)), so its corners poked past the
    # curve no matter what was in it.
    CIRCLE_DIAMETER = 600
    CONTENT_WIDTH = 320
    CONTENT_HEIGHT = 480
    AVATAR_DIAMETER = 170

    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.saint_name = ""
        self.saint_image = None
        self.saint_description = ""
        self.circle_diameter = self.CIRCLE_DIAMETER
        self.circle_center = (self.width() // 2, self.height() // 2)

        # Back button - 64x64 touch target (icon stays visually smaller,
        # centered inside it) for comfortable tapping on a touchscreen.
        self.back_btn = ClickableLabel(self)
        pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.back_btn.setPixmap(pixmap)
        self.back_btn.setAlignment(Qt.AlignCenter)
        self.back_btn.setFixedSize(64, 64)
        self.back_btn.setStyleSheet("background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22); border-radius: 32px;")
        self.back_btn.move(24, 24)
        if back_callback:
            self.back_btn.clicked.connect(back_callback)
        self.back_btn.raise_()

        # Content column: avatar photo, name, subtitle, festivity badge,
        # then a scrollable bio. Everything is capped to CONTENT_WIDTH so
        # it fits inside the circle instead of overflowing its corners.
        self.circle_widget = QWidget(self)
        self.circle_widget.setFixedSize(self.CONTENT_WIDTH, self.CONTENT_HEIGHT)
        self.circle_widget.setStyleSheet("background: transparent;")
        circle_layout = QVBoxLayout(self.circle_widget)
        circle_layout.setContentsMargins(0, 8, 0, 8)
        circle_layout.setSpacing(0)
        circle_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(self.AVATAR_DIAMETER, self.AVATAR_DIAMETER)
        self.avatar_label.setStyleSheet("background: transparent;")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        circle_layout.addWidget(self.avatar_label, alignment=Qt.AlignHCenter)
        circle_layout.addSpacing(10)

        self.name_label = QLabel()
        self.name_label.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        self.name_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFixedWidth(self.CONTENT_WIDTH)
        circle_layout.addWidget(self.name_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setFont(QFont("Arial", 13, QFont.StyleItalic))
        self.subtitle_label.setStyleSheet(f"color: {VETRATA_TEXT_DIM.name()}; background: transparent;")
        self.subtitle_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setFixedWidth(self.CONTENT_WIDTH)
        circle_layout.addWidget(self.subtitle_label)

        circle_layout.addSpacing(8)
        self.festa_label = QLabel()
        self.festa_label.setFont(plex_mono(12, letter_spacing=1))
        self.festa_label.setStyleSheet(
            f"color: {rgba_css(VETRATA_GOLD_BRIGHT)}; background: rgba(200,162,74,0.28); "
            "border: 1px solid rgba(255,224,160,0.4); padding: 3px 12px; border-radius: 4px;"
        )
        self.festa_label.setAlignment(Qt.AlignCenter)
        self.festa_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        circle_layout.addWidget(self.festa_label, alignment=Qt.AlignHCenter)
        circle_layout.addSpacing(10)

        # Scrollable bio - the one part of the card whose length varies a
        # lot, so it scrolls instead of ever overflowing past the circle.
        # QScroller adds touch/kinetic drag-to-scroll for the touchscreen.
        self.circle_scroll = QScrollArea()
        self.circle_scroll.setAttribute(Qt.WA_TranslucentBackground, True)
        self.circle_scroll.setWidgetResizable(True)
        self.circle_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.circle_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.circle_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,90); border-radius: 5px; min-height: 24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """)
        self.circle_scroll.viewport().setStyleSheet("background: transparent;")
        QScroller.grabGesture(self.circle_scroll.viewport(), QScroller.LeftMouseButtonGesture)
        self.circle_desc_widget = QWidget()
        self.circle_desc_widget.setStyleSheet("background: transparent;")
        self.circle_desc_layout = QVBoxLayout(self.circle_desc_widget)
        self.circle_desc_layout.setContentsMargins(4, 0, 4, 4)
        self.circle_desc_layout.setAlignment(Qt.AlignTop)
        self.circle_desc_label = QLabel()
        self.circle_desc_label.setFont(QFont("Arial", 15))
        self.circle_desc_label.setStyleSheet(f"color: {rgba_css(QColor(235, 232, 224, 224))}; background: transparent; line-height: 1.5;")
        self.circle_desc_label.setWordWrap(True)
        self.circle_desc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.circle_desc_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.circle_desc_layout.addWidget(self.circle_desc_label)
        self.circle_scroll.setWidget(self.circle_desc_widget)
        circle_layout.addWidget(self.circle_scroll, stretch=1)

        # Entrance choreography: the ring and each content element fade in
        # in sequence when the screen is (re)loaded, instead of a
        # continuous looping effect. Each widget gets its own opacity
        # effect, created once and reused on every replay.
        self._ring_opacity = 1.0
        self._avatar_opacity = QGraphicsOpacityEffect(self.avatar_label)
        self.avatar_label.setGraphicsEffect(self._avatar_opacity)
        self._name_opacity = QGraphicsOpacityEffect(self.name_label)
        self.name_label.setGraphicsEffect(self._name_opacity)
        self._subtitle_opacity = QGraphicsOpacityEffect(self.subtitle_label)
        self.subtitle_label.setGraphicsEffect(self._subtitle_opacity)
        self._festa_opacity = QGraphicsOpacityEffect(self.festa_label)
        self.festa_label.setGraphicsEffect(self._festa_opacity)
        self._bio_opacity = QGraphicsOpacityEffect(self.circle_scroll)
        self.circle_scroll.setGraphicsEffect(self._bio_opacity)
        self._entrance_group = None

        # "Luce radente": a one-time light sweep across the ring, played
        # once the entrance cascade finishes on the very first load only
        # (a per-app-run welcome flourish, not a repeating effect).
        self._shine_pos = -0.5
        self._shine_anim = None
        self._is_first_load = True

        self._position_content()
        self.load_saint()

    def get_ring_opacity(self):
        return self._ring_opacity

    def set_ring_opacity(self, value):
        self._ring_opacity = value
        self.update()

    ring_opacity = pyqtProperty(float, get_ring_opacity, set_ring_opacity)

    def get_shine_pos(self):
        return self._shine_pos

    def set_shine_pos(self, value):
        self._shine_pos = value
        self.update()

    shine_pos = pyqtProperty(float, get_shine_pos, set_shine_pos)

    def _play_entrance_animation(self):
        if self._entrance_group is not None:
            self._entrance_group.stop()

        self._ring_opacity = 0.0
        for effect in (self._avatar_opacity, self._name_opacity, self._subtitle_opacity,
                       self._festa_opacity, self._bio_opacity):
            effect.setOpacity(0.0)

        group = QParallelAnimationGroup(self)

        ring_anim = QPropertyAnimation(self, b"ring_opacity", self)
        ring_anim.setDuration(1000)
        ring_anim.setStartValue(0.0)
        ring_anim.setEndValue(1.0)
        ring_anim.setEasingCurve(QEasingCurve.OutCubic)
        group.addAnimation(ring_anim)

        # (effect, delay before starting, fade duration) - each element
        # rises in a little after the previous one. The bio gets an
        # especially slow, late fade since it's the final "reveal" and
        # was still reading as rushed at shorter durations.
        stagger = [
            (self._avatar_opacity, 400, 900),
            (self._name_opacity, 900, 800),
            (self._subtitle_opacity, 1300, 750),
            (self._festa_opacity, 1650, 750),
            (self._bio_opacity, 2050, 1400),
        ]
        for effect, delay_ms, duration_ms in stagger:
            seq = QSequentialAnimationGroup(self)
            if delay_ms:
                seq.addPause(delay_ms)
            fade = QPropertyAnimation(effect, b"opacity", self)
            fade.setDuration(duration_ms)
            fade.setStartValue(0.0)
            fade.setEndValue(1.0)
            fade.setEasingCurve(QEasingCurve.OutCubic)
            seq.addAnimation(fade)
            group.addAnimation(seq)

        # Gated on actual visibility, not just "first call": load_saint()
        # also runs once at construction time while the screen is still
        # hidden behind the stack, and an animation that starts and
        # finishes off-screen would silently burn the one-time flag
        # before the user ever sees it.
        if self._is_first_load and self.isVisible():
            self._is_first_load = False
            group.finished.connect(self._play_shine_sweep)

        self._entrance_group = group
        group.start()

    def _play_shine_sweep(self):
        # Matches the ~2.1s sweep pass from the original mockup (35% of
        # its 6s CSS cycle was the visible motion, the rest just a hold
        # off-screen before looping - here there's no loop, just the one
        # pass at that same speed).
        anim = QPropertyAnimation(self, b"shine_pos", self)
        anim.setDuration(2100)
        anim.setStartValue(-0.5)
        anim.setEndValue(1.5)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._shine_anim = anim
        anim.start()

    def _position_content(self):
        self.circle_center = (self.width() // 2, self.height() // 2)
        self.circle_widget.move(
            self.circle_center[0] - self.circle_widget.width() // 2,
            self.circle_center[1] - self.circle_widget.height() // 2,
        )
        self.back_btn.raise_()
        self.circle_widget.raise_()

    def resizeEvent(self, event):
        self._position_content()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        # Draw glowing accent ring - fades and grows in on entrance
        # (ring_opacity animates 0 -> 1 via _play_entrance_animation),
        # otherwise sits at rest fully visible.
        d = self.circle_diameter
        center = self.circle_center
        ring_scale = 0.9 + 0.1 * self._ring_opacity
        ring_half = (d / 2 + 12) * ring_scale
        ring_rect = QRectF(center[0] - ring_half, center[1] - ring_half, ring_half * 2, ring_half * 2)
        grad = QRadialGradient(center[0], center[1], d//2 + 12)
        grad.setColorAt(0.7, QColor(200, 162, 74, 120))
        grad.setColorAt(1.0, QColor(200, 162, 74, 0))
        painter.setOpacity(self._ring_opacity)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(ring_rect)
        painter.setOpacity(1.0)
        # Draw main circle - a frosted-glass disc matching GlassCard's
        # gradient recipe, just circular instead of rounded-rect.
        circle_path = QPainterPath()
        circle_path.addEllipse(center[0] - d//2, center[1] - d//2, d, d)
        glass_grad = QLinearGradient(center[0] - d//2, center[1] - d//2, center[0] + d//2, center[1] + d//2)
        glass_grad.setColorAt(0.0, QColor(255, 255, 255, 31))
        glass_grad.setColorAt(0.58, QColor(20, 22, 31, 235))
        glass_grad.setColorAt(1.0, QColor(255, 255, 255, 15))
        painter.fillPath(circle_path, QBrush(glass_grad))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 224, 160, 130), 2))
        painter.drawEllipse(center[0] - d//2, center[1] - d//2, d, d)
        # "Luce radente" - a one-time diagonal light sweep across the
        # circle, played once on the very first load (see
        # _play_shine_sweep). shine_pos sits at -0.5 (out of the drawn
        # range below) whenever it isn't actively animating.
        if -0.5 < self._shine_pos < 1.5:
            painter.save()
            clip_path = QPainterPath()
            clip_path.addEllipse(center[0] - d//2, center[1] - d//2, d, d)
            painter.setClipPath(clip_path)
            painter.translate(center[0], center[1])
            painter.rotate(18)
            painter.translate(-center[0], -center[1])
            band_width = d * 0.35
            travel = d + band_width
            x = (center[0] - d/2 - band_width/2) + self._shine_pos * travel
            shine_grad = QLinearGradient(x, 0, x + band_width, 0)
            shine_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
            shine_grad.setColorAt(0.5, QColor(255, 255, 255, 70))
            shine_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(shine_grad))
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(center[0] - d), int(center[1] - d), int(d * 2), int(d * 2))
            painter.restore()
        painter.end()
        super().paintEvent(event)

    @staticmethod
    def _circular_pixmap(source, diameter):
        """Crop/scale source to a centered circular portrait of the given
        diameter, instead of stretching it to fill a much larger area
        (the old behavior blew tiny scraped thumbnails up to 600px and
        left them badly blurred)."""
        scaled = source.scaled(diameter, diameter, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        if scaled.width() != diameter or scaled.height() != diameter:
            x = max(0, (scaled.width() - diameter) // 2)
            y = max(0, (scaled.height() - diameter) // 2)
            scaled = scaled.copy(x, y, diameter, diameter)
        rounded = QPixmap(diameter, diameter)
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, diameter, diameter)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 224, 160), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, diameter - 2, diameter - 2)
        painter.end()
        return rounded

    @staticmethod
    def _fit_label_font(label, text, max_width, start_pt=26, min_pt=16, max_lines=2):
        """Shrink the label's font until `text` wraps to at most
        `max_lines` lines within max_width, instead of letting a long
        name overflow or get truncated."""
        pt = start_pt
        while pt > min_pt:
            font = spectral(pt, "semibold")
            metrics = QFontMetrics(font)
            bounds = metrics.boundingRect(0, 0, max_width, 4000, Qt.TextWordWrap, text)
            if bounds.height() <= metrics.lineSpacing() * max_lines + 4:
                label.setFont(font)
                return
            pt -= 1
        label.setFont(spectral(min_pt, "semibold"))

    def _show_message(self, text, fallback_pixmap):
        self.avatar_label.setPixmap(self._circular_pixmap(fallback_pixmap, self.AVATAR_DIAMETER))
        self.name_label.setText("")
        self.subtitle_label.hide()
        self.festa_label.hide()
        self.circle_desc_label.setFont(QFont("Arial", 15))
        self.circle_desc_label.setText(text)
        self.saint_image = fallback_pixmap
        self._play_entrance_animation()

    def load_saint(self):
        saints_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saints.json")
        today = datetime.datetime.now()
        day_key = today.strftime("%m-%d")
        fallback_pixmap = QPixmap("assets/santi.jpg")
        self.saint_image = fallback_pixmap
        self.saint_name = ""
        self.saint_description = ""
        self.subtitle_label.hide()
        self.festa_label.hide()
        try:
            if not os.path.exists(saints_file):
                self._show_message("Dati dei santi non trovati. Esegui lo scraper per generare saints.json.", fallback_pixmap)
                return
            with open(saints_file, "r", encoding="utf-8") as f:
                saints = json.load(f)
            saint = next((s for s in saints if s["day"] == day_key), None)
            if not saint and day_key == "02-29":
                # saints.json has no leap-day entry; fall back to Feb 28's saint
                # rather than showing "no saint found" once every four years.
                saint = next((s for s in saints if s["day"] == "02-28"), None)
            if not saint:
                self._show_message(f"Nessun santo trovato per oggi ({day_key}).", fallback_pixmap)
                return

            self.saint_name = saint["name"]
            self.saint_description = saint["bio"]
            festa = saint.get("festivity", "")
            subtitle = saint.get("subtitle", "")

            self._fit_label_font(self.name_label, self.saint_name, self.CONTENT_WIDTH)
            self.name_label.setText(self.saint_name)

            if subtitle:
                self.subtitle_label.setText(subtitle)
                self.subtitle_label.show()
            if festa:
                self.festa_label.setText(festa)
                self.festa_label.show()

            self.circle_desc_label.setFont(QFont("Arial", 15))
            self.circle_desc_label.setText(self.saint_description)

            image_rel_path = saint.get("image")
            if image_rel_path:
                image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_rel_path)
                if os.path.exists(image_path):
                    loaded = QPixmap(image_path)
                    if not loaded.isNull():
                        self.saint_image = loaded
            self.avatar_label.setPixmap(self._circular_pixmap(self.saint_image, self.AVATAR_DIAMETER))
            self._play_entrance_animation()
        except Exception as e:
            self._show_message(f"Errore nel caricamento del santo: {e}", fallback_pixmap)

# --- In-App Browser Screen ---
class InAppBrowserScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setStyleSheet(f"background: {VETRATA_BG.name()};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(28, 16, 28, 16)
        top_bar.setSpacing(18)
        top_bar_wrap = QWidget()
        top_bar_wrap.setLayout(top_bar)
        top_bar_wrap.setStyleSheet(f"background: {VETRATA_BG.name()}; border-bottom: 1px solid rgba(255,255,255,0.1);")
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(64, 64)
            back_icon.setStyleSheet("background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22); border-radius: 32px;")
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Leggi la notizia")
        title.setFont(spectral(22))
        title.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        layout.addWidget(top_bar_wrap)
        # Web view
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

    def load_url(self, url):
        self.webview.setUrl(url)

# --- Prega Screen ---
class PregaScreen(QWidget):
    AVATAR_DIAMETER = 110

    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.back_callback = back_callback
        self.saints = self.load_data()
        self.today_saint = None
        self._last_category = None
        self._pending_category = None
        self._recording = False
        self._record_seconds = 0
        self.audio_recorder = None
        self._last_recording_path = None
        self._record_timer = QTimer(self)
        self._record_timer.timeout.connect(self._update_elapsed)
        self.blessings = [
            "Che il Signore ti benedica e ti protegga.",
            "La pace di Cristo sia con te.",
            "Dio ti doni forza e serenità.",
            "Che la grazia divina ti accompagni sempre.",
            "Il Signore ascolti la tua preghiera."
        ]
        self.categories = ["Aiuto", "Guida", "Ringraziamento", "Protezione"]
        self.init_ui()
        self.load_today_saint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(0)

        # Go back icon (top left)
        top_bar = QHBoxLayout()
        goback = ClickableLabel(self)
        pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        goback.setPixmap(pixmap)
        goback.setAlignment(Qt.AlignCenter)
        goback.setFixedSize(64, 64)
        goback.setStyleSheet("background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22); border-radius: 32px;")
        goback.clicked.connect(self.go_back)
        top_bar.addWidget(goback, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Today's saint - connects this screen to Santo del Giorno instead
        # of making the user pick a saint before they can pray at all.
        self.saint_avatar_label = QLabel()
        self.saint_avatar_label.setFixedSize(self.AVATAR_DIAMETER, self.AVATAR_DIAMETER)
        self.saint_avatar_label.setAlignment(Qt.AlignCenter)
        self.saint_avatar_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.saint_avatar_label, alignment=Qt.AlignHCenter)
        layout.addSpacing(10)

        self.saint_name_label = QLabel()
        self.saint_name_label.setFont(spectral(23))
        self.saint_name_label.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        self.saint_name_label.setAlignment(Qt.AlignHCenter)
        self.saint_name_label.setWordWrap(True)
        layout.addWidget(self.saint_name_label)

        self.change_saint_btn = QPushButton("Cambia santo")
        self.change_saint_btn.setFlat(True)
        self.change_saint_btn.setCursor(Qt.PointingHandCursor)
        self.change_saint_btn.setStyleSheet(f"""
            QPushButton {{ color: {VETRATA_GOLD.name()}; background: transparent; border: none; font-size: 14px; padding: 6px; }}
            QPushButton:pressed {{ color: {VETRATA_GOLD_BRIGHT.name()}; }}
        """)
        self.change_saint_btn.clicked.connect(self.toggle_saint_picker)
        layout.addWidget(self.change_saint_btn, alignment=Qt.AlignHCenter)

        # Saint picker - hidden until "Cambia santo" is tapped, so praying
        # with today's saint never requires touching a dropdown first.
        combo_style = """
QComboBox {
    color: #f2eee2;
    background: rgba(255,255,255,0.1);
    font-size: 18px;
    padding-left: 18px;
    padding-right: 32px;
    border-radius: 22px;
    border: 1px solid rgba(255,255,255,0.22);
    min-width: 180px;
    max-width: 280px;
    height: 44px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border-top-right-radius: 22px;
    border-bottom-right-radius: 22px;
    border-left: none;
    background: transparent;
}
QComboBox::down-arrow {
    image: none;
}
QComboBox QAbstractItemView {
    color: #f2eee2;
    background: #1c1f2c;
    selection-background-color: rgba(200,162,74,0.4);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 14px;
    font-size: 18px;
}
"""
        self.saint_combo = QComboBox()
        seen_names = set()
        for s in self.saints:
            if s['name'] not in seen_names:
                seen_names.add(s['name'])
                self.saint_combo.addItem(s['name'])
        self.saint_combo.setStyleSheet(combo_style)
        self.saint_combo.setFixedHeight(44)
        self.saint_combo.setMaximumWidth(280)
        self.saint_combo.currentTextChanged.connect(self.on_saint_changed)
        self.saint_combo.hide()
        saint_picker_layout = QHBoxLayout()
        saint_picker_layout.addStretch()
        saint_picker_layout.addWidget(self.saint_combo)
        saint_picker_layout.addStretch()
        layout.addLayout(saint_picker_layout)
        layout.addSpacing(18)

        # Intention selection - shown by default; swapped out for
        # record_view once an intention is tapped, and swapped back in
        # by _reset_flow()/discard_recording().
        self.intention_view = QWidget()
        intention_view_layout = QVBoxLayout(self.intention_view)
        intention_view_layout.setContentsMargins(0, 0, 0, 0)
        intention_view_layout.setSpacing(14)

        prompt_label = QLabel("Cosa senti di voler chiedere oggi?")
        prompt_label.setFont(QFont("Arial", 16))
        prompt_label.setStyleSheet(f"color: {VETRATA_TEXT_DIM.name()}; background: transparent;")
        prompt_label.setAlignment(Qt.AlignHCenter)
        intention_view_layout.addWidget(prompt_label)

        # Intention buttons: tapping one opens the voice recorder for that
        # intention, instead of picking a category, generating a request,
        # then separately tapping "Prega". Styled as a QSS approximation
        # of GlassCard's gradient recipe - plain QPushButtons here (rather
        # than GlassCard instances) since a button's own label is painted
        # internally and never risks swallowing its own click.
        intention_style = """
            QPushButton {
                color: #f2eee2;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.20), stop:0.58 rgba(255,255,255,0.05), stop:1 rgba(255,255,255,0.09));
                font-weight: 600;
                font-size: 17px;
                padding: 14px 10px;
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,0.2);
                min-height: 44px;
            }
            QPushButton:pressed { background: rgba(255,255,255,0.22); }
        """
        intention_layout = QGridLayout()
        intention_layout.setHorizontalSpacing(14)
        intention_layout.setVerticalSpacing(14)
        for i, category in enumerate(self.categories):
            btn = QPushButton(category)
            btn.setStyleSheet(intention_style)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=category: self.start_record_flow(c))
            intention_layout.addWidget(btn, i // 2, i % 2)
        intention_view_layout.addLayout(intention_layout)

        layout.addWidget(self.intention_view)
        layout.addSpacing(20)

        # Voice recorder - the actual "praying" moment: tap the record
        # button, say the prayer out loud, tap again to stop. Hidden until
        # an intention is chosen.
        self.record_view = QWidget()
        record_view_layout = QVBoxLayout(self.record_view)
        record_view_layout.setContentsMargins(0, 0, 0, 0)
        record_view_layout.setSpacing(10)
        record_view_layout.setAlignment(Qt.AlignHCenter)

        change_intention_btn = QPushButton("‹ Cambia intenzione")
        change_intention_btn.setFlat(True)
        change_intention_btn.setCursor(Qt.PointingHandCursor)
        change_intention_btn.setStyleSheet(f"""
            QPushButton {{ color: {VETRATA_GOLD.name()}; background: transparent; border: none; font-size: 14px; padding: 4px; }}
            QPushButton:pressed {{ color: {VETRATA_GOLD_BRIGHT.name()}; }}
        """)
        change_intention_btn.clicked.connect(self.discard_recording)
        record_view_layout.addWidget(change_intention_btn, alignment=Qt.AlignHCenter)

        self.record_status_label = QLabel()
        self.record_status_label.setWordWrap(True)
        self.record_status_label.setFont(QFont("Arial", 15))
        self.record_status_label.setStyleSheet(f"color: {VETRATA_TEXT_DIM.name()}; background: transparent;")
        self.record_status_label.setAlignment(Qt.AlignHCenter)
        record_view_layout.addWidget(self.record_status_label)
        record_view_layout.addSpacing(6)

        # Record button with a pulsing halo behind it while recording -
        # positioned by hand (no layout) like the existing combo-box arrow
        # labels elsewhere in this class, so the halo can sit centered
        # behind the button rather than pushing it aside.
        record_btn_container = QWidget()
        record_btn_container.setFixedSize(140, 140)
        self.record_halo = QLabel(record_btn_container)
        self.record_halo.setGeometry(5, 5, 130, 130)
        self.record_halo.setStyleSheet(
            "background: #e74c3c; border-radius: 65px;"
        )
        self._record_halo_effect = QGraphicsOpacityEffect(self.record_halo)
        self._record_halo_effect.setOpacity(0.0)
        self.record_halo.setGraphicsEffect(self._record_halo_effect)
        self._pulse_anim = QPropertyAnimation(self._record_halo_effect, b"opacity", self)
        self._pulse_anim.setDuration(900)
        self._pulse_anim.setStartValue(0.15)
        self._pulse_anim.setKeyValueAt(0.5, 0.55)
        self._pulse_anim.setEndValue(0.15)
        self._pulse_anim.setLoopCount(-1)

        self.record_btn = QPushButton("●", record_btn_container)
        self.record_btn.setGeometry(22, 22, 96, 96)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.setStyleSheet("""
            QPushButton {
                color: #fff;
                background: #e74c3c;
                font-size: 30px;
                border-radius: 48px;
                border: 3px solid #ffffff;
            }
            QPushButton:pressed { background: #c0392b; }
            QPushButton:disabled { background: #bbb; }
        """)
        self.record_btn.raise_()
        self.record_btn.clicked.connect(self.toggle_recording)
        record_view_layout.addWidget(record_btn_container, alignment=Qt.AlignHCenter)

        self.record_time_label = QLabel("00:00")
        self.record_time_label.setFont(plex_mono(18))
        self.record_time_label.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        self.record_time_label.setAlignment(Qt.AlignHCenter)
        record_view_layout.addWidget(self.record_time_label)

        layout.addWidget(self.record_view)
        self.record_view.hide()
        layout.addSpacing(20)

        # Prayer response - a single card (a note that the prayer was
        # recorded, a blessing, and the saint's reply) that appears once a
        # recording is stopped.
        self.response_card = GlassCard(variant="accent", radius=22)
        response_layout = QVBoxLayout(self.response_card)
        response_layout.setContentsMargins(26, 22, 26, 22)
        response_layout.setSpacing(10)
        self.prayer_label = QLabel()
        self.prayer_label.setWordWrap(True)
        self.prayer_label.setFont(spectral(19))
        self.prayer_label.setStyleSheet(f"color: {rgba_css(VETRATA_GOLD_BRIGHT)}; background: transparent;")
        response_layout.addWidget(click_through(self.prayer_label))
        self.blessing_label = QLabel()
        self.blessing_label.setWordWrap(True)
        self.blessing_label.setFont(QFont("Arial", 15))
        self.blessing_label.setStyleSheet(f"color: {rgba_css(QColor(253, 240, 207, 214))}; background: transparent;")
        response_layout.addWidget(click_through(self.blessing_label))
        self.reply_label = QLabel()
        self.reply_label.setWordWrap(True)
        self.reply_label.setFont(QFont("Arial", 14, QFont.Normal, italic=True))
        self.reply_label.setStyleSheet(f"color: {rgba_css(QColor(253, 240, 207, 191))}; background: transparent;")
        response_layout.addWidget(click_through(self.reply_label))
        layout.addWidget(self.response_card)
        self.response_card.hide()

        layout.addSpacing(12)
        self.pray_again_btn = QPushButton("Prega di nuovo")
        self.pray_again_btn.setCursor(Qt.PointingHandCursor)
        self.pray_again_btn.setStyleSheet("""
            QPushButton {
                color: #f2eee2;
                background: rgba(255,255,255,0.1);
                font-weight: 500;
                font-size: 15px;
                padding: 8px 20px;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.22);
            }
            QPushButton:pressed { background: rgba(255,255,255,0.2); }
        """)
        self.pray_again_btn.clicked.connect(self.pray_again)
        layout.addWidget(self.pray_again_btn, alignment=Qt.AlignHCenter)
        self.pray_again_btn.hide()

        self.setLayout(layout)

    def toggle_saint_picker(self):
        self.saint_combo.setVisible(not self.saint_combo.isVisible())

    def on_saint_changed(self, name):
        if not name:
            return
        self.saint_name_label.setText(name)
        self._update_avatar_for_name(name)
        # A previous response was for the old saint - don't leave it,
        # or an in-progress recording, showing next to a name it no
        # longer matches.
        self._reset_flow()

    def load_today_saint(self):
        if not self.saints:
            self.saint_name_label.setText("Dati dei santi non disponibili")
            self.saint_avatar_label.setPixmap(
                SaintOfTheDayScreen._circular_pixmap(QPixmap("assets/santi.jpg"), self.AVATAR_DIAMETER)
            )
            return
        day_key = datetime.datetime.now().strftime("%m-%d")
        saint = next((s for s in self.saints if s.get("day") == day_key), None)
        if not saint and day_key == "02-29":
            saint = next((s for s in self.saints if s.get("day") == "02-28"), None)
        if not saint:
            saint = self.saints[0]
        self.today_saint = saint
        name = saint["name"]

        self.saint_combo.blockSignals(True)
        idx = self.saint_combo.findText(name)
        if idx >= 0:
            self.saint_combo.setCurrentIndex(idx)
        self.saint_combo.blockSignals(False)

        self.saint_name_label.setText(name)
        self._update_avatar_for_name(name, saint)
        self._reset_flow()

    def _update_avatar_for_name(self, name, saint=None):
        if saint is None:
            saint = next((s for s in self.saints if s['name'] == name), None)
        pixmap = QPixmap("assets/santi.jpg")
        image_rel_path = saint.get("image") if saint else None
        if image_rel_path:
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_rel_path)
            if os.path.exists(image_path):
                loaded = QPixmap(image_path)
                if not loaded.isNull():
                    pixmap = loaded
        self.saint_avatar_label.setPixmap(SaintOfTheDayScreen._circular_pixmap(pixmap, self.AVATAR_DIAMETER))

    def _reset_flow(self):
        # Back to "pick an intention" - used whenever the saint changes or
        # the screen is (re)opened, so a stale response or a recording left
        # running from a previous visit never lingers.
        if self._recording:
            self.discard_recording()
        else:
            self.record_view.hide()
            self.intention_view.show()
        self.response_card.hide()
        self.pray_again_btn.hide()
        self._last_category = None
        self._pending_category = None

    def go_back(self):
        if self._recording:
            self.discard_recording()
        if self.back_callback:
            self.back_callback()

    def start_record_flow(self, category):
        saint = self.saint_name_label.text()
        if not saint or not self.saints:
            return
        self._pending_category = category
        self._last_category = category
        self.response_card.hide()
        self.pray_again_btn.hide()
        self.intention_view.hide()
        self.record_view.show()
        if AUDIO_RECORDING_AVAILABLE:
            self.record_status_label.setText(
                f"Tocca per registrare la tua preghiera di {category.lower()} a {saint}."
            )
        else:
            self.record_status_label.setText(
                "Registrazione vocale non disponibile su questo dispositivo."
            )
        self.record_time_label.setText("00:00")
        self.record_btn.setText("●")
        self.record_btn.setEnabled(AUDIO_RECORDING_AVAILABLE)

    def discard_recording(self):
        if self._recording:
            self._stop_recorder()
            self._recording = False
            self._record_timer.stop()
            self._pulse_anim.stop()
            self._record_halo_effect.setOpacity(0.0)
            self.record_btn.setText("●")
        self.record_view.hide()
        self.intention_view.show()

    def toggle_recording(self):
        if self._recording:
            self.stop_recording()
        else:
            self.start_recording()

    def _ensure_recorder(self):
        if not AUDIO_RECORDING_AVAILABLE:
            return None
        if self.audio_recorder is None:
            try:
                self.audio_recorder = QAudioRecorder()
            except Exception:
                self.audio_recorder = None
        return self.audio_recorder

    def start_recording(self):
        recorder = self._ensure_recorder()
        if recorder is None:
            self.record_status_label.setText(
                "Registrazione vocale non disponibile su questo dispositivo."
            )
            return
        recordings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
        try:
            os.makedirs(recordings_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            category = self._pending_category or "preghiera"
            path = os.path.join(recordings_dir, f"prega_{category}_{timestamp}.wav")
            recorder.setOutputLocation(QUrl.fromLocalFile(path))
            settings = QAudioEncoderSettings()
            settings.setCodec("audio/pcm")
            settings.setQuality(QMultimedia.HighQuality)
            recorder.setEncodingSettings(settings)
            recorder.record()
        except Exception:
            self.record_status_label.setText("Impossibile avviare la registrazione.")
            return
        self._last_recording_path = path
        self._recording = True
        self._record_seconds = 0
        self.record_time_label.setText("00:00")
        self._record_timer.start(1000)
        self._pulse_anim.start()
        self.record_btn.setText("■")
        self.record_status_label.setText("Registrazione in corso... tocca per fermare.")

    def stop_recording(self):
        self._stop_recorder()
        self._recording = False
        self._record_timer.stop()
        self._pulse_anim.stop()
        self._record_halo_effect.setOpacity(0.0)
        self.record_btn.setText("●")
        self._show_recorded_response()

    def _stop_recorder(self):
        if self.audio_recorder is not None:
            try:
                self.audio_recorder.stop()
            except Exception:
                pass

    def _update_elapsed(self):
        self._record_seconds += 1
        minutes, seconds = divmod(self._record_seconds, 60)
        self.record_time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _show_recorded_response(self):
        import random
        saint = self.saint_name_label.text()
        self.record_view.hide()
        self.prayer_label.setText(f"Hai affidato a {saint} la tua preghiera di {self._pending_category.lower()}.")
        self.blessing_label.setText(random.choice(self.blessings))
        self.reply_label.setText(self.generate_saint_reply(saint))
        self.response_card.show()
        self.pray_again_btn.show()

    def pray_again(self):
        if self._last_category:
            self.start_record_flow(self._last_category)

    def generate_saint_reply(self, saint):
        import random
        replies = [
            f"Figlio/a caro/a, non temere. Pregherò per te e ti accompagnerò nel tuo cammino.",
            f"La tua fede è preziosa. Affido la tua richiesta al Signore e ti proteggerò come ho fatto con tanti altri.",
            f"Non sei solo/a: la mia intercessione sarà con te. Abbi fiducia e persevera nella preghiera.",
            f"Il Signore ascolta chi si affida con cuore sincero. Ti benedico e ti incoraggio a non perdere la speranza.",
            f"Ti sono vicino/a in questo momento. Ricorda che la grazia di Dio opera anche nelle difficoltà."
        ]
        return random.choice(replies)

    def load_data(self):
        saints_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saints.json')
        try:
            with open(saints_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            # A missing/corrupt saints.json used to crash the whole app at
            # startup, since PregaScreen is constructed eagerly - degrade
            # to an empty list instead; load_today_saint()/start_record_flow()
            # both already handle that gracefully.
            return []

# --- Main App ---
class MainStack(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.intro = CinematicIntro(on_finished=self.show_onboarding)
        self.onboarding = OnboardingScreen()
        self.saint_screen = SaintOfTheDayScreen(back_callback=self.show_menu)
        self.menu = MainMenuScreen(promemoria_callback=self.show_promemoria, vatican_callback=self.show_news_vaticano, saint_callback=self.show_saint, prega_callback=self.show_prega, bible_callback=self.show_bible)
        self.promemoria = PromemoriaScreen(back_callback=self.show_menu)
        self.news_vaticano = NewsVaticanoScreen(back_callback=self.show_menu, open_in_app_browser=self.show_in_app_browser)
        self.in_app_browser = InAppBrowserScreen(back_callback=self.show_news_vaticano)
        self.prega_screen = PregaScreen(back_callback=self.show_menu)
        self.bible_screen = BibleReadingScreen(back_callback=self.show_menu)
        self.addWidget(self.intro)
        self.addWidget(self.onboarding)
        self.addWidget(self.menu)
        self.addWidget(self.saint_screen)
        self.addWidget(self.promemoria)
        self.addWidget(self.news_vaticano)
        self.addWidget(self.in_app_browser)
        self.addWidget(self.prega_screen)
        self.addWidget(self.bible_screen)
        self.setCurrentWidget(self.intro)
        self.onboarding.cont_btn.clicked.connect(self.next_step)
        self.menu.promemoria_callback = self.show_promemoria
        self.menu.vatican_callback = self.show_news_vaticano
        self.menu.saint_callback = self.show_saint
        self.menu.prega_callback = self.show_prega
        self.menu.bible_callback = self.show_bible
        self.menu.set_vatican_headline(self.news_vaticano.latest_headline)

    def show_onboarding(self):
        self.setCurrentWidget(self.onboarding)

    def next_step(self):
        self.setCurrentWidget(self.menu)

    def show_menu(self):
        self.setCurrentWidget(self.menu)
        self.menu.refresh()

    def show_promemoria(self):
        self.setCurrentWidget(self.promemoria)

    def show_news_vaticano(self):
        self.setCurrentWidget(self.news_vaticano)

    def show_saint(self):
        # setCurrentWidget before load_saint: the entrance animation
        # (including the one-time shine sweep) is gated on the screen
        # actually being visible, so it must already be current by the
        # time load_saint() triggers it.
        self.setCurrentWidget(self.saint_screen)
        self.saint_screen.load_saint()

    def show_prega(self):
        self.setCurrentWidget(self.prega_screen)
        self.prega_screen.load_today_saint()

    def show_in_app_browser(self, url):
        from PyQt5.QtCore import QUrl
        self.in_app_browser.load_url(QUrl(url))
        self.setCurrentWidget(self.in_app_browser)

    def show_bible(self):
        self.bible_screen.load_reading()
        self.setCurrentWidget(self.bible_screen)

ITALIAN_MONTHS = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


class BibleReadingScreen(QWidget):
    """An antiphonary-styled reading card - a rubric line (in the
    liturgical sense: the instructional line above a reading) and an
    illuminated first letter - reworked onto the app's dark Vetrata
    glass instead of its original light parchment, so the screen
    stays part of the same visual system as the rest of the app."""

    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)

        outer_margin = QVBoxLayout(self)
        outer_margin.setContentsMargins(28, 20, 28, 20)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(18)
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(64, 64)
            back_icon.setStyleSheet("background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22); border-radius: 32px;")
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Letture bibliche")
        title.setFont(spectral(28))
        title.setStyleSheet(f"color: {VETRATA_TEXT.name()}; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        self.date_label = QLabel()
        self.date_label.setFont(plex_mono(13, letter_spacing=1.5))
        self.date_label.setStyleSheet(f"color: {VETRATA_LABEL.name()}; background: transparent;")
        top_bar.addWidget(self.date_label, alignment=Qt.AlignVCenter)
        outer_margin.addLayout(top_bar)
        outer_margin.addSpacing(16)

        card = GlassCard(variant="default", radius=24)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(44, 30, 44, 30)
        card_layout.setSpacing(0)

        # Rubric line: "Vangelo - Lc 5,1-11"
        self.rubric_label = QLabel()
        self.rubric_label.setFont(plex_mono(13, letter_spacing=2))
        self.rubric_label.setStyleSheet(f"color: {VETRATA_GOLD.name()}; background: transparent;")
        self.rubric_label.setAlignment(Qt.AlignHCenter)
        self.rubric_label.setWordWrap(True)
        card_layout.addWidget(self.rubric_label)
        card_layout.addSpacing(8)

        # Pericope title
        self.title_label = QLabel()
        self.title_label.setFont(spectral(20, italic=True))
        self.title_label.setStyleSheet(f"color: {VETRATA_TEXT_DIM.name()}; background: transparent;")
        self.title_label.setAlignment(Qt.AlignHCenter)
        self.title_label.setWordWrap(True)
        card_layout.addWidget(self.title_label)
        card_layout.addSpacing(20)

        # Reading content in a scroll area, with a large illuminated
        # first letter leading the text.
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        scroll_area.viewport().setStyleSheet("background: transparent;")
        QScroller.grabGesture(scroll_area.viewport(), QScroller.LeftMouseButtonGesture)
        reading_widget = QWidget()
        reading_widget.setStyleSheet("background: transparent;")
        reading_layout = QVBoxLayout(reading_widget)
        reading_layout.setContentsMargins(0, 0, 0, 0)
        reading_layout.setSpacing(0)
        self.reading_label = QLabel()
        self.reading_label.setFont(spectral(16))
        self.reading_label.setStyleSheet(f"color: {rgba_css(QColor(235, 232, 224, 224))}; background: transparent;")
        self.reading_label.setWordWrap(True)
        self.reading_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reading_layout.addWidget(self.reading_label)
        scroll_area.setWidget(reading_widget)
        card_layout.addWidget(scroll_area, stretch=1)

        outer_margin.addWidget(card, stretch=1)

        self.load_reading()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        paint_vetrata_background(painter, self.rect())
        super().paintEvent(event)

    def _show_message(self, text):
        self.date_label.setText("")
        self.rubric_label.setText("")
        self.title_label.setText("")
        self.reading_label.setTextFormat(Qt.PlainText)
        self.reading_label.setText(text)

    def load_reading(self):
        readings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bible_readings.json')
        today = datetime.datetime.now()
        day_key = today.strftime("%m-%d")
        try:
            if not os.path.exists(readings_file):
                self._show_message("Dati delle letture non trovati. Esegui lo scraper per generare bible_readings.json.")
                return
            with open(readings_file, "r", encoding="utf-8") as f:
                readings = json.load(f)
            reading = next((r for r in readings if r["day"] == day_key), None)
            if not reading and day_key == "02-29":
                # bible_readings.json has no leap-day entry; fall back to Feb
                # 28's reading rather than showing nothing once every four years.
                reading = next((r for r in readings if r["day"] == "02-28"), None)
            if not reading:
                self._show_message(f"Nessuna lettura trovata per oggi ({day_key}).")
                return

            category = reading.get("category", "")
            title = reading.get("title", "")
            reference = reading.get("reference", "")
            text = reading.get("text", "")

            self.date_label.setText(f"{today.day} {ITALIAN_MONTHS[today.month - 1]}".upper())
            self.rubric_label.setText(html.escape(f"{category} · {reference}").upper())
            self.title_label.setText(html.escape(title) if title else "")

            # An illuminated first letter, in place of Qt's rich-text
            # renderer not supporting a true magazine-style floated
            # drop cap: a large colored inline span leading the text.
            first_char, rest = (text[0], text[1:]) if text else ("", "")
            body_html = (
                f'<span style="font-size:32px; font-weight:bold; color:{VETRATA_GOLD_BRIGHT.name()};">{html.escape(first_char)}</span>'
                + html.escape(rest).replace("\n", "<br>")
            )
            self.reading_label.setTextFormat(Qt.RichText)
            self.reading_label.setText(body_html)
        except Exception as e:
            self._show_message(f"Errore nel caricamento della lettura: {e}")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    load_vetrata_fonts()
    window = MainStack()
    window.setWindowTitle("SANTETIZZATORE")
    window.show()
    sys.exit(app.exec_())