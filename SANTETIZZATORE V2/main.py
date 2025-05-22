import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QStackedWidget, QToolButton, QGridLayout, QSpacerItem, QCheckBox, QScrollArea, QComboBox, QLineEdit, QGraphicsDropShadowEffect, QMessageBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimer, QEasingCurve, pyqtProperty, QSize, QRectF, QPointF
from PyQt5.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QFontDatabase, QIcon, QPen, QPixmap, QRadialGradient, QPainterPath, QRegion, QMovie
from PyQt5.QtWebEngineWidgets import QWebEngineView
import math
import feedparser
import webbrowser
import requests
import re
import json
import openai
import datetime
import os
import sqlite3

# Load the font
# font_id = QFontDatabase.addApplicationFont("assets/fonts/10Pixel-Thin.ttf")
# font_families = QFontDatabase.applicationFontFamilies(font_id)
# print("Loaded font families:", font_families)  # For debugging
# if font_families:
#     title_font = QFont(font_families[0], 40)
# else:
#     title_font = QFont("Arial", 40)  # fallback
title_font = QFont("Arial", 40)

LARA_API_KEY = "F07RSFBVMI90LNSOHGFAIHBGIU"

OPENAI_API_KEY = "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"

def translate_to_italian(text):
    # MyMemory has a 100-word limit per request, so split into chunks
    def chunk_words(s, n):
        words = s.split()
        for start in range(0, len(words), n):
            yield ' '.join(words[start:start+n])
    try:
        url = "https://api.mymemory.translated.net/get"
        translated_chunks = []
        for chunk in chunk_words(text, 100):
            params = {"q": chunk, "langpair": "en|it"}
            response = requests.get(url, params=params, timeout=10)
            if response.ok:
                translated = response.json().get("responseData", {}).get("translatedText", None)
                if not translated or translated.strip() == chunk.strip():
                    print(f"[DEBUG] MyMemory returned original or empty for chunk: {chunk[:60]}...")
                    translated_chunks.append(chunk)
                else:
                    translated_chunks.append(translated)
            else:
                print(f"[DEBUG] MyMemory HTTP error: {response.status_code} {response.text}")
                translated_chunks.append(chunk)  # fallback to original chunk
        result = " ".join(translated_chunks)
        if result.strip() == text.strip():
            print("[DEBUG] MyMemory failed or returned original text for the whole input.")
        return result
    except Exception as e:
        print("Errore nella traduzione MyMemory:", e)
    return text

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
        if self._shine_pos <= 1.5:
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0, QColor(255, 255, 255, 0))
            grad.setColorAt(max(0, self._shine_pos - 0.1), QColor(255, 255, 255, 0))
            grad.setColorAt(self._shine_pos, QColor(255, 255, 255, 180))
            grad.setColorAt(min(1, self._shine_pos + 0.1), QColor(255, 255, 255, 0))
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
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #232a3a, stop:1 #3a4a5a);")
        self.on_finished = on_finished

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        # Main Title
        self.title_label = ShineLabel("SANTETIZZATORE", title_font, "white")
        self.title_label.setFixedHeight(80)

        # Subtitle
        credit_font = QFont("Arial", 13)
        self.credit_label = ShineLabel("Developed by Ora Pro Nobis", credit_font, "white")
        self.credit_label.setFixedHeight(30)

        # Grey thin loading bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(
            """
            QProgressBar { background: #888; border: none; border-radius: 2px; }
            QProgressBar::chunk { background: #e0e0e0; border-radius: 2px; }
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
        self.setStyleSheet("background: #f7f7f7;")
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignVCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignVCenter)
        layout.setContentsMargins(32, 32, 32, 32)

        # Welcome title with white color and glow
        title = QLabel("Benvenuto in SANTETIZZATORE!")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignHCenter)
        # Add glow effect
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(32)
        glow.setColor(QColor(255, 255, 180, 180))
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        layout.addWidget(title)
        layout.addSpacing(32)

        # Continue button: smaller, grey, black text
        self.cont_btn = QPushButton("Continua")
        self.cont_btn.setFont(QFont("Arial", 15, QFont.Bold))
        self.cont_btn.setMinimumHeight(36)
        self.cont_btn.setMaximumWidth(180)
        self.cont_btn.setIcon(QIcon.fromTheme("go-next"))
        self.cont_btn.setStyleSheet("""
            QPushButton {
                background: #bbb;
                color: #222;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
                min-height: 36px;
                max-width: 180px;
                padding: 6px 24px;
            }
            QPushButton:pressed {
                background: #888;
            }
        """)
        self.cont_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.cont_btn, alignment=Qt.AlignHCenter)
        layout.addSpacing(4)

        main_layout.addLayout(layout)
        self.setLayout(main_layout)

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
class MainMenuScreen(QWidget):
    def __init__(self, promemoria_callback=None, vatican_callback=None, saint_callback=None, prega_callback=None, bible_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setStyleSheet("background: transparent;")
        self._gradient_angle = 0.0
        self._ray_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.animate_gradient)
        self._timer.start(50)  # 20 FPS for smoothness
        self.promemoria_callback = promemoria_callback
        self.vatican_callback = vatican_callback
        self.saint_callback = saint_callback
        self.prega_callback = prega_callback
        self.bible_callback = bible_callback
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignVCenter)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)
        grid.setContentsMargins(0, 0, 0, 0)

        def make_btn(text, icon, callback, enabled=True):
            btn = QToolButton()
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumSize(110, 110)
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(48, 48))
            btn.setFont(QFont("Arial", 15, QFont.Bold))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setText(text)
            if not enabled:
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QToolButton {
                        background: #f0f0f0;
                        border: 1px solid #cccccc;
                        border-radius: 18px;
                        color: #aaa;
                        font-size: 15px;
                        font-weight: bold;
                        padding: 10px 4px 4px 4px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QToolButton {
                        background: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 18px;
                        color: #222;
                        font-size: 15px;
                        font-weight: bold;
                        padding: 10px 4px 4px 4px;
                    }
                    QToolButton:pressed {
                        background: #e0e0e0;
                    }
                """)
                btn.clicked.connect(callback)
            return btn

        # Reordered buttons with disabled Rosario and Trova chiese
        buttons = [
            ("Santo del giorno", "assets/saint.jpg", self.saint_clicked if not self.saint_callback else self.saint_callback, True),
            ("Letture Bibliche", "assets/bible.jpg", self.bible_clicked, True),
            ("Prega", "assets/hands.jpg", self.prega_clicked if not self.prega_callback else self.prega_callback, True),
            ("Dal Vaticano", "assets/vatican.jpg", self.vatican_callback if self.vatican_callback else self.vatican_clicked, True),
            ("Promemoria", "assets/bell.jpg", self.promemoria_callback if self.promemoria_callback else self.reminder_clicked, True),
            ("Rosario", "assets/rosary.jpg", self.rosary_clicked, False),
            ("Trova chiese", "assets/maps.jpg", self.maps_clicked, False),
        ]

        cols = 3
        rows = (len(buttons) + cols - 1) // cols
        for idx, (text, icon, cb, enabled) in enumerate(buttons):
            row = idx // cols
            col = idx % cols
            grid.addWidget(make_btn(text, icon, cb, enabled), row, col)

        for i in range(cols):
            grid.setColumnStretch(i, 1)
        for i in range(rows):
            grid.setRowStretch(i, 1)

        layout.addStretch()
        layout.addLayout(grid)
        layout.addStretch()
        self.setLayout(layout)

    def animate_gradient(self):
        self._gradient_angle += 2.0
        if self._gradient_angle >= 360.0:
            self._gradient_angle = 0.0
        self._ray_phase += 0.008
        if self._ray_phase > 1.0:
            self._ray_phase = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        # Animated linear gradient: light purple <-> white <-> light blue <-> white
        angle_rad = math.radians(self._gradient_angle)
        x1 = rect.width() / 2 + math.cos(angle_rad) * rect.width() / 2
        y1 = rect.height() / 2 + math.sin(angle_rad) * rect.height() / 2
        x2 = rect.width() / 2 - math.cos(angle_rad) * rect.width() / 2
        y2 = rect.height() / 2 - math.sin(angle_rad) * rect.height() / 2

        # Animate color phase: 0-0.25 purple->white, 0.25-0.5 white->blue, 0.5-0.75 blue->white, 0.75-1 white->purple
        phase = (self._gradient_angle % 360) / 360.0
        purple = QColor(200, 160, 255)
        blue = QColor(173, 216, 230)
        white = QColor(255, 255, 255)
        if phase < 0.25:
            t = phase / 0.25
            start = QColor(
                int(purple.red() * (1-t) + white.red() * t),
                int(purple.green() * (1-t) + white.green() * t),
                int(purple.blue() * (1-t) + white.blue() * t)
            )
        elif phase < 0.5:
            t = (phase-0.25)/0.25
            start = QColor(
                int(white.red() * (1-t) + blue.red() * t),
                int(white.green() * (1-t) + blue.green() * t),
                int(white.blue() * (1-t) + blue.blue() * t)
            )
        elif phase < 0.75:
            t = (phase-0.5)/0.25
            start = QColor(
                int(blue.red() * (1-t) + white.red() * t),
                int(blue.green() * (1-t) + white.green() * t),
                int(blue.blue() * (1-t) + white.blue() * t)
            )
        else:
            t = (phase-0.75)/0.25
            start = QColor(
                int(white.red() * (1-t) + purple.red() * t),
                int(white.green() * (1-t) + purple.green() * t),
                int(white.blue() * (1-t) + purple.blue() * t)
            )
        grad = QLinearGradient(x1, y1, x2, y2)
        grad.setColorAt(0, start)
        grad.setColorAt(1, white)
        painter.fillRect(rect, grad)

        # Moving light/ray effect
        ray_width = int(rect.width() * 0.5)
        ray_height = int(rect.height() * 0.25)
        ray_x = int((rect.width() + ray_width) * self._ray_phase) - ray_width // 2
        ray_y = int(rect.height() * 0.2)
        ray_color = QColor(255, 255, 255, 80)  # semi-transparent white
        painter.setBrush(ray_color)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.save()
        painter.setOpacity(0.35)
        painter.drawEllipse(ray_x, ray_y, ray_width, ray_height)
        painter.restore()

        super().paintEvent(event)

    # Placeholder callbacks
    def saint_clicked(self):
        if self.saint_callback:
            self.saint_callback()
        else:
            print("Santo del giorno clicked")
    def bible_clicked(self):
        if self.bible_callback:
            self.bible_callback()
        else:
            print("Bible callback not set")
    def _promemoria_clicked(self):
        if self.promemoria_callback:
            self.promemoria_callback()
        else:
            print("Promemoria clicked")
    def vatican_clicked(self):
        print("Dal Vaticano clicked")
    def pray_clicked(self):
        print("Prega clicked")
    def rosary_clicked(self):
        print("Rosario clicked")
    def maps_clicked(self):
        print("Trova chiese clicked")
    def prega_clicked(self):
        if self.prega_callback:
            self.prega_callback()
        else:
            print("Prega clicked")

# --- Promemoria Screen ---
class PromemoriaScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: #eaf3fc;")
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        # Centered card
        card = QWidget()
        card.setStyleSheet("background: white; border-radius: 32px; box-shadow: 0 8px 32px 0 rgba(120,180,255,0.10);")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(32)
        # Top bar: back icon
        top_bar = QHBoxLayout()
        top_bar.setSpacing(24)
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setFixedSize(40, 40)
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        card_layout.addLayout(top_bar)
        # Analog clock
        clock = AnalogClock()
        card_layout.addWidget(clock, alignment=Qt.AlignHCenter)
        # Reminders
        reminders = [
            ("Preghiera del mattino", "07:00"),
            ("Preghiera di mezzogiorno", "12:00"),
            ("Preghiera della sera", "16:00"),
            ("Rosario", "18:00"),
            ("Preghiera della notte", "20:00"),
        ]
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(24)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        available_fonts = QFontDatabase().families()
        for i, (label, time) in enumerate(reminders):
            font = QFont("Arial", 22, QFont.Normal)
            for fam in ["Arial Rounded MT Bold", "Helvetica Neue Light", "Arial"]:
                if fam in available_fonts:
                    font = QFont(fam, 22, QFont.Normal)
                    break
            lbl = QLabel(label)
            lbl.setFont(font)
            lbl.setStyleSheet("color: #3a6fd8; background: transparent;")
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(180, 200, 255, 120))
            lbl.setGraphicsEffect(shadow)
            time_lbl = QLabel(time)
            time_lbl.setFont(font)
            time_lbl.setStyleSheet("color: #7faaff; background: transparent;")
            time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            shadow_time = QGraphicsDropShadowEffect()
            shadow_time.setBlurRadius(10)
            shadow_time.setOffset(0, 2)
            shadow_time.setColor(QColor(180, 200, 255, 120))
            time_lbl.setGraphicsEffect(shadow_time)
            switch = IOSSwitch(checked=True)
            switch.setFixedSize(60, 38)
            grid.addWidget(lbl, i, 0, alignment=Qt.AlignVCenter)
            grid.addWidget(time_lbl, i, 1, alignment=Qt.AlignVCenter)
            grid.addWidget(switch, i, 2, alignment=Qt.AlignVCenter)
        card_layout.addLayout(grid)
        card_layout.addStretch()
        outer_layout.addStretch()
        outer_layout.addWidget(card, alignment=Qt.AlignHCenter | Qt.AlignVCenter)
        outer_layout.addStretch()

    def load_saint(self):
        import datetime
        import os
        saints_file = "saints.json"
        today = datetime.datetime.now()
        day_key = today.strftime("%m-%d")
        fallback_pixmap = QPixmap("assets/santi.jpg")
        self.saint_image = fallback_pixmap
        self.saint_name = ""
        self.saint_description = ""
        self.clear_layout(self.circle_desc_layout)
        try:
            if not os.path.exists(saints_file):
                self.circle_desc_label.setText("Dati dei santi non trovati. Esegui lo scraper per generare saints.json.")
                self.saint_image = fallback_pixmap
                self.update()
                return
            with open(saints_file, "r", encoding="utf-8") as f:
                saints = json.load(f)
            saint = next((s for s in saints if s["day"] == day_key), None)
            if not saint:
                self.circle_desc_label.setText(f"Nessun santo trovato per oggi ({day_key}).")
                self.saint_image = fallback_pixmap
                self.update()
                return
            self.saint_name = saint["name"]
            self.saint_description = saint["bio"]
            festa = saint.get("festivity", "")
            # Compose the display: name (big, bold, centered), festivity (bold, centered), description (justified)
            name_label = QLabel(self.saint_name)
            name_label.setFont(QFont("Arial", 28, QFont.Bold))
            name_label.setStyleSheet("color: #fff; background: transparent; margin-top: 12px; margin-bottom: 8px;")
            name_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            name_label.setWordWrap(True)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            name_label.setMaximumWidth(self.circle_widget.width() - 32)
            # Elide text if still too long
            fm = name_label.fontMetrics()
            elided = fm.elidedText(self.saint_name, Qt.ElideRight, self.circle_widget.width() - 32)
            name_label.setText(elided)
            self.circle_desc_layout.addWidget(name_label)
            if festa:
                festa_label = QLabel(f"{festa}")
                festa_label.setFont(QFont("Arial", 16, QFont.Bold))
                festa_label.setStyleSheet("color: #111; background: #bcd6fc; padding: 2px 8px; border-radius: 4px;")
                festa_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
                self.circle_desc_layout.addWidget(festa_label)
                self.circle_desc_layout.addSpacing(12)
            desc_body_html = '<div style="line-height:1.6; text-align:justify; text-align-last:center;">' + '<br>'.join(self.saint_description.splitlines()) + '</div>'
            self.circle_desc_label.setTextFormat(Qt.RichText)
            self.circle_desc_label.setText(desc_body_html)
            self.circle_desc_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.circle_desc_layout.addWidget(self.circle_desc_label)
            # No image URL in JSON, always use fallback
            self.saint_image = fallback_pixmap
            self.update()
        except Exception as e:
            self.circle_desc_label.setText(f"Errore nel caricamento del santo: {e}")
            self.saint_image = fallback_pixmap
            self.update()

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
        # Draw clock face
        painter.setBrush(QColor(255,255,255,230))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, side//2-4, side//2-4)
        # Draw ticks
        painter.setPen(QPen(QColor(180,200,255,120), 2))
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
        painter.setPen(QPen(QColor(80,120,255), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(center.x() + 0.45*side*math.cos(math.radians(hour*30-90)), center.y() + 0.45*side*math.sin(math.radians(hour*30-90))))
        # Minute hand
        painter.setPen(QPen(QColor(120,180,255), 4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(center.x() + 0.65*side*math.cos(math.radians(minute*6-90)), center.y() + 0.65*side*math.sin(math.radians(minute*6-90))))
        # Second hand
        painter.setPen(QPen(QColor(255,80,80), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center, QPointF(center.x() + 0.7*side*math.cos(math.radians(second*6-90)), center.y() + 0.7*side*math.sin(math.radians(second*6-90))))
        # Center dot
        painter.setBrush(QColor(80,120,255))
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
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self._gradient_angle = 0.0
        self._ray_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.animate_gradient)
        self._timer.start(50)
        self.open_in_app_browser = open_in_app_browser
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(32, 32, 32, 32)
        outer_layout.setSpacing(0)

        # Top bar: back icon + title
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setFixedSize(28, 28)
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Dal Vaticano")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #333; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        outer_layout.addLayout(top_bar)

        # Scroll area for news
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        news_layout = QVBoxLayout(content)
        news_layout.setSpacing(18)
        news_layout.setContentsMargins(0, 0, 0, 0)
        self.news_layout = news_layout
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # Loading spinner
        self.spinner = QLabel()
        self.spinner.setAlignment(Qt.AlignCenter)
        self.spinner_movie = QMovie("assets/loading_spinner.gif")
        self.spinner.setMovie(self.spinner_movie)
        self.spinner_movie.start()
        self.news_layout.addWidget(self.spinner)

        self.load_news()

    def animate_gradient(self):
        self._gradient_angle += 2.0
        if self._gradient_angle >= 360.0:
            self._gradient_angle = 0.0
        self._ray_phase += 0.008
        if self._ray_phase > 1.0:
            self._ray_phase = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        # Animated background: light grey <-> white
        angle_rad = math.radians(self._gradient_angle)
        x1 = rect.width() / 2 + math.cos(angle_rad) * rect.width() / 2
        y1 = rect.height() / 2 + math.sin(angle_rad) * rect.height() / 2
        x2 = rect.width() / 2 - math.cos(angle_rad) * rect.width() / 2
        y2 = rect.height() / 2 - math.sin(angle_rad) * rect.height() / 2
        phase = (self._gradient_angle % 360) / 360.0
        light_grey = QColor(245, 245, 245)
        white = QColor(255, 255, 255)
        # Animate between light grey and white
        t = 0.5 * (1 + math.sin(2 * math.pi * phase))
        start = QColor(
            int(light_grey.red() * (1-t) + white.red() * t),
            int(light_grey.green() * (1-t) + white.green() * t),
            int(light_grey.blue() * (1-t) + white.blue() * t)
        )
        grad = QLinearGradient(x1, y1, x2, y2)
        grad.setColorAt(0, start)
        grad.setColorAt(1, white)
        painter.fillRect(rect, grad)
        # Moving ray
        ray_width = int(rect.width() * 0.5)
        ray_height = int(rect.height() * 0.25)
        ray_x = int((rect.width() + ray_width) * self._ray_phase) - ray_width // 2
        ray_y = int(rect.height() * 0.2)
        ray_color = QColor(255, 255, 255, 80)
        painter.setBrush(ray_color)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.save()
        painter.setOpacity(0.35)
        painter.drawEllipse(ray_x, ray_y, ray_width, ray_height)
        painter.restore()
        super().paintEvent(event)

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
        print("Feed bozo:", getattr(feed, 'bozo', None))
        print("Feed bozo_exception:", getattr(feed, 'bozo_exception', None))
        print("Feed entries:", getattr(feed, 'entries', None))
        # Remove spinner
        self.spinner_movie.stop()
        self.spinner.deleteLater()
        if not feed.entries:
            msg = QLabel("Nessuna notizia disponibile.")
            msg.setFont(QFont("Arial", 14, QFont.Bold))
            msg.setStyleSheet("color: #888; background: transparent;")
            self.news_layout.addWidget(msg)
            return
        for entry in feed.entries[:10]:
            card = QWidget()
            card.setStyleSheet('''
                background: #232a3a;
                border: none;
                border-radius: 16px;
                padding: 18px 16px 18px 16px;
                margin-bottom: 14px;
                box-shadow: 0 4px 24px 0 rgba(0,0,0,0.18);
            ''')
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)
            card_layout.setSpacing(16)
            # Image if available
            img_url = None
            if 'media_content' in entry and entry.media_content:
                img_url = entry.media_content[0].get('url')
            elif 'media_thumbnail' in entry and entry.media_thumbnail:
                img_url = entry.media_thumbnail[0].get('url')
            if img_url:
                try:
                    img_data = requests.get(img_url, timeout=5).content
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    # Resize to 150x150 and add rounded corners
                    size = 150
                    rounded = QPixmap(size, size)
                    rounded.fill(Qt.transparent)
                    painter = QPainter(rounded)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, size, size, 24, 24)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    painter.end()
                    img_label = QLabel()
                    img_label.setPixmap(rounded)
                    img_label.setFixedSize(size, size)
                    img_label.setStyleSheet("margin-right: 16px;")
                    card_layout.addWidget(img_label, alignment=Qt.AlignVCenter)
                except Exception as e:
                    print("Image load error:", e)
            # News content
            content_layout = QVBoxLayout()
            content_layout.setSpacing(4)
            # Date if available
            if hasattr(entry, 'published'):
                date_lbl = QLabel(entry.published)
                date_lbl.setFont(QFont("Arial", 10))
                date_lbl.setStyleSheet("color: #b0b0b0; background: transparent;")
                content_layout.addWidget(date_lbl)
            title = QLabel(entry.title)
            title.setFont(QFont("Arial", 17, QFont.Bold))
            title.setStyleSheet("color: #fff; background: transparent;")
            title.setWordWrap(True)
            title.setCursor(Qt.PointingHandCursor)
            link = entry.link
            title.mousePressEvent = lambda e, url=link: self.open_in_app_browser(url) if self.open_in_app_browser else webbrowser.open(url)
            # Clean summary: remove any 'Leggi tutto' link or text (plain or HTML)
            summary_text = entry.summary
            # Remove HTML links with 'Leggi tutto'
            summary_text = re.sub(r'<a [^>]*>\s*Leggi tutto\s*</a>', '', summary_text, flags=re.IGNORECASE)
            # Remove plain 'Leggi tutto' text
            summary_text = re.sub(r'Leggi tutto', '', summary_text, flags=re.IGNORECASE)
            summary = QLabel(summary_text)
            summary.setFont(QFont("Arial", 13))
            summary.setStyleSheet("color: #e0e0e0; background: transparent;")
            summary.setWordWrap(True)
            content_layout.addWidget(title)
            content_layout.addWidget(summary)
            # Only add the button below
            btn = QPushButton("Leggi tutto")
            btn.setFont(QFont("Arial", 12, QFont.Bold))
            btn.setStyleSheet("background: #e0e0e0; color: #222; border-radius: 6px; padding: 6px 18px; min-width: 100px;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, url=entry.link: self.open_in_app_browser(url) if self.open_in_app_browser else webbrowser.open(url))
            content_layout.addWidget(btn, alignment=Qt.AlignLeft)
            card_layout.addLayout(content_layout)
            self.news_layout.addWidget(card)

# --- Saint of the Day Screen ---
class SaintOfTheDayScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: #181c24;")
        self.saint_name = ""
        self.saint_image = None
        self.saint_description = ""
        self.circle_diameter = 600
        self.circle_center = (self.width() // 2, self.height() // 2)

        # Back button
        self.back_btn = ClickableLabel(self)
        pixmap = QPixmap("assets/goback.jpg").scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.back_btn.setPixmap(pixmap)
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.move(32, 32)
        if back_callback:
            self.back_btn.clicked.connect(back_callback)
        self.back_btn.raise_()

        # Name and description widgets inside the circle
        self.circle_widget = QWidget(self)
        self.circle_widget.setGeometry(self.circle_center[0] - self.circle_diameter // 2 + 24,
                                       self.circle_center[1] - self.circle_diameter // 2 + 24,
                                       self.circle_diameter - 48, self.circle_diameter - 48)
        self.circle_widget.setFixedSize(self.circle_diameter - 48, self.circle_diameter - 48)
        self.circle_widget.setStyleSheet("background: transparent;")
        circle_layout = QVBoxLayout(self.circle_widget)
        circle_layout.setContentsMargins(32, 32, 32, 32)
        circle_layout.setSpacing(18)
        circle_layout.setAlignment(Qt.AlignTop)
        # Scrollable description
        self.circle_scroll = QScrollArea()
        self.circle_scroll.setStyleSheet("background: transparent; border: none;")
        self.circle_scroll.setWidgetResizable(True)
        self.circle_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.circle_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.circle_desc_widget = QWidget()
        self.circle_desc_layout = QVBoxLayout(self.circle_desc_widget)
        self.circle_desc_layout.setContentsMargins(0, 0, 0, 0)
        self.circle_desc_layout.setAlignment(Qt.AlignTop)
        self.circle_desc_label = QLabel()
        self.circle_desc_label.setFont(QFont("Arial", 18))
        self.circle_desc_label.setStyleSheet("color: #fff; background: transparent;")
        self.circle_desc_label.setWordWrap(True)
        self.circle_desc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.circle_desc_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.circle_desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.circle_desc_label.setFixedWidth(self.circle_diameter - 120)
        self.circle_desc_layout.addWidget(self.circle_desc_label)
        self.circle_desc_widget.setMinimumHeight(200)
        self.circle_scroll.setWidget(self.circle_desc_widget)
        circle_layout.addWidget(self.circle_scroll, stretch=1)

        self.circle_desc_widget.setFixedSize(self.circle_diameter - 96, self.circle_diameter - 96)
        self.circle_desc_label.setFixedWidth(self.circle_diameter - 120)
        self.circle_scroll.setFixedSize(self.circle_diameter - 64, self.circle_diameter - 64)

        self.load_saint()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            elif item.layout() is not None:
                self.clear_layout(item.layout())
        # spacers are removed by takeAt

    def resizeEvent(self, event):
        self.circle_center = (self.width() // 2, self.height() // 2)
        self.circle_widget.setGeometry(self.circle_center[0] - self.circle_diameter // 2 + 24,
                                       self.circle_center[1] - self.circle_diameter // 2 + 24,
                                       self.circle_diameter - 48, self.circle_diameter - 48)
        self.circle_widget.setFixedSize(self.circle_diameter - 48, self.circle_diameter - 48)
        self.circle_desc_widget.setFixedSize(self.circle_diameter - 96, self.circle_diameter - 96)
        self.circle_desc_label.setFixedWidth(self.circle_diameter - 120)
        self.circle_scroll.setFixedSize(self.circle_diameter - 64, self.circle_diameter - 64)
        self.back_btn.raise_()
        self.circle_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.circle_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Draw background
        painter.fillRect(self.rect(), QColor("#181c24"))
        # Draw glowing accent ring
        d = self.circle_diameter
        center = self.circle_center
        ring_rect = QRectF(center[0] - d//2 - 12, center[1] - d//2 - 12, d + 24, d + 24)
        grad = QRadialGradient(center[0], center[1], d//2 + 12)
        grad.setColorAt(0.7, QColor(120, 120, 255, 120))
        grad.setColorAt(1.0, QColor(120, 180, 255, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(ring_rect)
        # Draw main circle
        painter.setBrush(QColor("#232a3a"))
        painter.setPen(QPen(QColor(120, 180, 255), 4))
        painter.drawEllipse(center[0] - d//2, center[1] - d//2, d, d)
        # Saint image (circular)
        if self.saint_image:
            img_d = d - 8
            img_rect = QRectF(center[0] - img_d//2, center[1] - img_d//2, img_d, img_d)
            mask = QPixmap(int(img_d), int(img_d))
            mask.fill(Qt.transparent)
            mask_painter = QPainter(mask)
            mask_painter.setRenderHint(QPainter.Antialiasing)
            mask_painter.setBrush(Qt.white)
            mask_painter.setPen(Qt.NoPen)
            mask_painter.drawEllipse(0, 0, int(img_d), int(img_d))
            mask_painter.end()
            img = self.saint_image.scaled(int(img_d), int(img_d), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            img.setMask(mask.createMaskFromColor(Qt.transparent))
            painter.drawPixmap(img_rect.toRect(), img)
            painter.save()
            painter.setBrush(QColor(30, 30, 30, 140))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(img_rect)
        painter.restore()
        painter.end()
        super().paintEvent(event)

    def load_saint(self):
        import datetime
        import os
        saints_file = "saints.json"
        today = datetime.datetime.now()
        day_key = today.strftime("%m-%d")
        fallback_pixmap = QPixmap("assets/santi.jpg")
        self.saint_image = fallback_pixmap
        self.saint_name = ""
        self.saint_description = ""
        self.clear_layout(self.circle_desc_layout)
        try:
            if not os.path.exists(saints_file):
                self.circle_desc_label.setText("Dati dei santi non trovati. Esegui lo scraper per generare saints.json.")
                self.saint_image = fallback_pixmap
                self.update()
                return
            with open(saints_file, "r", encoding="utf-8") as f:
                saints = json.load(f)
            saint = next((s for s in saints if s["day"] == day_key), None)
            if not saint:
                self.circle_desc_label.setText(f"Nessun santo trovato per oggi ({day_key}).")
                self.saint_image = fallback_pixmap
                self.update()
                return
            self.saint_name = saint["name"]
            self.saint_description = saint["bio"]
            festa = saint.get("festivity", "")
            # Compose the display: name (big, bold, centered), festivity (bold, centered), description (justified)
            name_label = QLabel(self.saint_name)
            name_label.setFont(QFont("Arial", 28, QFont.Bold))
            name_label.setStyleSheet("color: #fff; background: transparent; margin-top: 12px; margin-bottom: 8px;")
            name_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            name_label.setWordWrap(True)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            name_label.setMaximumWidth(self.circle_widget.width() - 32)
            # Elide text if still too long
            fm = name_label.fontMetrics()
            elided = fm.elidedText(self.saint_name, Qt.ElideRight, self.circle_widget.width() - 32)
            name_label.setText(elided)
            self.circle_desc_layout.addWidget(name_label)
            if festa:
                festa_label = QLabel(f"{festa}")
                festa_label.setFont(QFont("Arial", 16, QFont.Bold))
                festa_label.setStyleSheet("color: #111; background: #bcd6fc; padding: 2px 8px; border-radius: 4px;")
                festa_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
                self.circle_desc_layout.addWidget(festa_label)
                self.circle_desc_layout.addSpacing(12)
            desc_body_html = '<div style="line-height:1.6; text-align:justify; text-align-last:center;">' + '<br>'.join(self.saint_description.splitlines()) + '</div>'
            self.circle_desc_label.setTextFormat(Qt.RichText)
            self.circle_desc_label.setText(desc_body_html)
            self.circle_desc_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.circle_desc_layout.addWidget(self.circle_desc_label)
            # No image URL in JSON, always use fallback
            self.saint_image = fallback_pixmap
            self.update()
        except Exception as e:
            self.circle_desc_label.setText(f"Errore nel caricamento del santo: {e}")
            self.saint_image = fallback_pixmap
            self.update()

# --- In-App Browser Screen ---
class InAppBrowserScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setStyleSheet("background: #232a3a;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Top bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setFixedSize(28, 28)
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Leggi la notizia")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #fff; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        # Web view
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

    def load_url(self, url):
        self.webview.setUrl(url)

# --- Prega Screen ---
class PregaScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.back_callback = back_callback
        self.data = self.load_data()
        self.saints = self.data
        self.templates = [
            "O {saint}, ascolta la mia preghiera: {request}",
            "{saint}, ti affido la mia richiesta: {request}",
            "Caro {saint}, intercedi per me: {request}",
            "{saint}, patrono e protettore, prega per me: {request}",
            "O glorioso {saint}, porta la mia supplica a Dio: {request}"
        ]
        self.blessings = [
            "Che il Signore ti benedica e ti protegga.",
            "La pace di Cristo sia con te.",
            "Dio ti doni forza e serenità.",
            "Che la grazia divina ti accompagni sempre.",
            "Il Signore ascolti la tua preghiera."
        ]
        self.request_categories = {
            'Aiuto': [
                "Aiutami nelle mie difficoltà.",
                "Concedimi forza in questo momento di bisogno.",
                "Assisti la mia famiglia nei momenti difficili."
            ],
            'Guida': [
                "Guidami sulla strada giusta.",
                "Mostrami la via nelle mie decisioni.",
                "Donami saggezza e chiarezza."
            ],
            'Ringraziamento': [
                "Grazie per le tue benedizioni.",
                "Sono grato per la tua intercessione.",
                "Grazie per le preghiere esaudite."
            ],
            'Protezione': [
                "Proteggi i miei cari.",
                "Tienimi al sicuro da ogni male.",
                "Veglia sulla mia famiglia e sui miei amici."
            ]
        }
        # Animated gradient state
        self._gradient_angle = 0.0
        self._ray_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.animate_gradient)
        self._timer.start(50)
        self.saint_of_day = self.get_saint_of_the_day()
        self.init_ui()

    def animate_gradient(self):
        self._gradient_angle += 2.0
        if self._gradient_angle >= 360.0:
            self._gradient_angle = 0.0
        self._ray_phase += 0.008
        if self._ray_phase > 1.0:
            self._ray_phase = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        angle_rad = math.radians(self._gradient_angle)
        x1 = rect.width() / 2 + math.cos(angle_rad) * rect.width() / 2
        y1 = rect.height() / 2 + math.sin(angle_rad) * rect.height() / 2
        x2 = rect.width() / 2 - math.cos(angle_rad) * rect.width() / 2
        y2 = rect.height() / 2 - math.sin(angle_rad) * rect.height() / 2
        phase = (self._gradient_angle % 360) / 360.0
        purple = QColor(200, 160, 255)
        blue = QColor(173, 216, 230)
        white = QColor(255, 255, 255)
        if phase < 0.25:
            t = phase / 0.25
            start = QColor(
                int(purple.red() * (1-t) + white.red() * t),
                int(purple.green() * (1-t) + white.green() * t),
                int(purple.blue() * (1-t) + white.blue() * t)
            )
        elif phase < 0.5:
            t = (phase-0.25)/0.25
            start = QColor(
                int(white.red() * (1-t) + blue.red() * t),
                int(white.green() * (1-t) + blue.green() * t),
                int(white.blue() * (1-t) + blue.blue() * t)
            )
        elif phase < 0.75:
            t = (phase-0.5)/0.25
            start = QColor(
                int(blue.red() * (1-t) + white.red() * t),
                int(blue.green() * (1-t) + white.green() * t),
                int(blue.blue() * (1-t) + white.blue() * t)
            )
        else:
            t = (phase-0.75)/0.25
            start = QColor(
                int(white.red() * (1-t) + purple.red() * t),
                int(white.green() * (1-t) + purple.green() * t),
                int(white.blue() * (1-t) + purple.blue() * t)
            )
        grad = QLinearGradient(x1, y1, x2, y2)
        grad.setColorAt(0, start)
        grad.setColorAt(1, white)
        painter.fillRect(rect, grad)
        # Moving ray
        ray_width = int(rect.width() * 0.5)
        ray_height = int(rect.height() * 0.25)
        ray_x = int((rect.width() + ray_width) * self._ray_phase) - ray_width // 2
        ray_y = int(rect.height() * 0.2)
        ray_color = QColor(255, 255, 255, 80)
        painter.setBrush(ray_color)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.save()
        painter.setOpacity(0.35)
        painter.drawEllipse(ray_x, ray_y, ray_width, ray_height)
        painter.restore()
        super().paintEvent(event)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 40, 40, 40)
        # Remove background and color from widget stylesheet (handled by paintEvent)
        self.setStyleSheet("font-size: 22px; color: #111;")

        # Go back icon (top left)
        goback = ClickableLabel(self)
        pixmap = QPixmap("assets/goback.jpg").scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        goback.setPixmap(pixmap)
        goback.setFixedSize(48, 48)
        goback.clicked.connect(self.back_callback)
        layout.addWidget(goback, alignment=Qt.AlignLeft)

        combo_style = """
QComboBox {
    color: #111;
    background: #fff;
    font-size: 22px;
    padding-left: 18px;
    padding-right: 32px;
    border-radius: 22px;
    border: 1.5px solid #ccc;
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
    color: #111;
    background: #fff;
    selection-background-color: #ffe082;
    border-radius: 14px;
    font-size: 20px;
}
"""
        # Saint selection (iOS style, no label)
        self.saint_combo = QComboBox()
        self.saint_combo.addItem("Seleziona un santo")
        for s in self.saints:
            self.saint_combo.addItem(s['name'])
        self.saint_combo.setCurrentIndex(0)
        self.saint_combo.setStyleSheet(combo_style)
        self.saint_combo.setFixedHeight(44)
        self.saint_combo.setMaximumWidth(280)
        self.saint_combo.style().unpolish(self.saint_combo)
        self.saint_combo.style().polish(self.saint_combo)
        # Add custom arrow label
        self.saint_arrow = QLabel("▼", self.saint_combo)
        self.saint_arrow.setStyleSheet("color: #888; font-size: 18px; background: transparent;")
        self.saint_arrow.setFixedSize(24, 44)
        self.saint_arrow.move(self.saint_combo.width() - 32, 0)
        def saint_combo_resize(event, combo=self.saint_combo, arrow=self.saint_arrow):
            arrow.move(combo.width() - 32, 0)
            QComboBox.resizeEvent(combo, event)
        self.saint_combo.resizeEvent = saint_combo_resize
        saint_layout = QHBoxLayout()
        saint_layout.addStretch()
        saint_layout.addWidget(self.saint_combo)
        saint_layout.addStretch()
        layout.addLayout(saint_layout)

        # Category selection (iOS style, no label)
        self.category_combo = QComboBox()
        self.category_combo.addItem("Seleziona una categoria")
        for cat in self.request_categories.keys():
            self.category_combo.addItem(cat)
        self.category_combo.setCurrentIndex(0)
        self.category_combo.setStyleSheet(combo_style)
        self.category_combo.setFixedHeight(44)
        self.category_combo.setMaximumWidth(280)
        self.category_combo.style().unpolish(self.category_combo)
        self.category_combo.style().polish(self.category_combo)
        # Add custom arrow label
        self.category_arrow = QLabel("▼", self.category_combo)
        self.category_arrow.setStyleSheet("color: #888; font-size: 18px; background: transparent;")
        self.category_arrow.setFixedSize(24, 44)
        self.category_arrow.move(self.category_combo.width() - 32, 0)
        def category_combo_resize(event, combo=self.category_combo, arrow=self.category_arrow):
            arrow.move(combo.width() - 32, 0)
            QComboBox.resizeEvent(combo, event)
        self.category_combo.resizeEvent = category_combo_resize
        category_layout = QHBoxLayout()
        category_layout.addStretch()
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        layout.addLayout(category_layout)

        # Request input (read-only)
        self.request_input = QLineEdit()
        self.request_input.setPlaceholderText("La richiesta verrà generata...")
        self.request_input.setStyleSheet("color: #111; background: #fff; font-size: 22px; padding: 8px 24px; border-radius: 28px; border: 2px solid #bbb;")
        self.request_input.setReadOnly(True)
        self.request_input.setFixedHeight(48)
        layout.addWidget(self.request_input)

        # Generate random request button
        self.random_request_btn = QPushButton("Genera richiesta casuale")
        self.random_request_btn.setStyleSheet("""
            QPushButton {
                color: #222;
                background: #fff;
                font-weight: 500;
                font-size: 18px;
                padding: 8px 18px;
                border-radius: 14px;
                border: 1.5px solid #e0e0e0;
                min-width: 100px;
                min-height: 36px;
                max-width: 220px;
                max-height: 40px;
            }
            QPushButton:pressed {
                background: #f0f0f0;
            }
        """)
        self.random_request_btn.setFixedHeight(40)
        self.random_request_btn.clicked.connect(self.generate_random_request)
        layout.addWidget(self.random_request_btn, alignment=Qt.AlignHCenter)

        # Restore Prega button
        self.prega_btn = QPushButton("Prega")
        self.prega_btn.setStyleSheet("""
            QPushButton {
                color: #222;
                background: #fff;
                font-weight: 500;
                font-size: 18px;
                padding: 8px 18px;
                border-radius: 14px;
                border: 1.5px solid #e0e0e0;
                min-width: 100px;
                min-height: 36px;
                max-width: 180px;
                max-height: 40px;
            }
            QPushButton:pressed {
                background: #f0f0f0;
            }
        """)
        self.prega_btn.setFixedHeight(40)
        self.prega_btn.clicked.connect(self.generate_prayer)
        layout.addWidget(self.prega_btn, alignment=Qt.AlignHCenter)

        # Output
        self.prayer_label = QLabel()
        self.prayer_label.setWordWrap(True)
        self.prayer_label.setStyleSheet("font-size: 26px; color: #111; margin-top: 30px; font-weight: bold; background: transparent;")
        layout.addWidget(self.prayer_label)
        self.blessing_label = QLabel()
        self.blessing_label.setStyleSheet("font-size: 22px; color: #111; margin-top: 10px; background: transparent;")
        layout.addWidget(self.blessing_label)
        # Saint reply label
        self.reply_label = QLabel()
        self.reply_label.setWordWrap(True)
        self.reply_label.setStyleSheet("font-size: 20px; color: #555; margin-top: 18px; font-style: italic; background: transparent;")
        layout.addWidget(self.reply_label)
        self.setLayout(layout)

    def generate_random_request(self):
        import random
        saint = self.saint_combo.currentText()
        category = self.category_combo.currentText()
        # Find saint specialty
        specialty = ""
        for s in self.saints:
            if s['name'] == saint:
                specialty = s.get('specialty', "")
                break
        # More human, emotional templates
        templates = [
            "Caro {saint}, so che sei vicino a chi si affida a te. In questo momento sento il bisogno del tuo aiuto: {detail}",
            "{saint}, patrono di {specialty}, ascolta la mia preghiera. {detail}",
            "Mi rivolgo a te, {saint}, con il cuore pieno di speranza. {detail}",
            "O {saint}, tu che conosci le difficoltà di {specialty.lower()}, ti chiedo: {detail}",
            "{saint}, sento il peso di questa situazione. Ti prego, aiutami: {detail}",
            "{saint}, confido nella tua intercessione. {detail}",
            "In questo momento difficile, mi affido a te, {saint}. {detail}",
            "{saint}, so che ascolti chi si rivolge a te. Ti chiedo con fede: {detail}",
            "{saint}, modello di {specialty.lower()}, ti affido la mia intenzione: {detail}",
            "{saint}, ti prego con tutto il cuore: {detail}"
        ]
        if category in self.request_categories:
            detail = random.choice(self.request_categories[category])
        else:
            detail = "le mie necessità."
        # Sometimes add a context sentence
        contexts = [
            "Mi sento smarrito/a e ho bisogno di una guida.",
            "La mia famiglia sta attraversando un momento difficile.",
            "Porto nel cuore tante preoccupazioni.",
            "Cerco conforto e speranza.",
            "Ho bisogno di forza per andare avanti.",
            "Il mio cuore è inquieto e cerca pace.",
            "Mi affido alla tua bontà e protezione.",
            "So che la tua intercessione è potente presso Dio.",
            "Ho bisogno di luce per le mie scelte.",
            "Ti chiedo di vegliare su di me e sui miei cari."
        ]
        use_context = random.choice([True, False])
        context = random.choice(contexts) if use_context else ""
        template = random.choice(templates)
        request = template.format(saint=saint, specialty=specialty, detail=detail)
        if context:
            request = context + " " + request
        self.request_input.setText(request)

    def generate_prayer(self):
        saint = self.saint_combo.currentText()
        request = self.request_input.text().strip()
        if not request:
            self.prayer_label.setText("Genera una richiesta prima di pregare.")
            self.blessing_label.clear()
            self.reply_label.clear()
            return
        import random
        template = random.choice(self.templates)
        prayer = template.format(saint=saint, request=request)
        self.prayer_label.setText(prayer)
        self.blessing_label.setText(random.choice(self.blessings))
        # Generate saint reply
        self.reply_label.setText(self.generate_saint_reply(saint))

    def generate_saint_reply(self, saint):
        import random
        specialty = ""
        quotes = []
        for s in self.saints:
            if s['name'] == saint:
                specialty = s.get('specialty', "")
                quotes = s.get('quotes', [])
                break
        replies = [
            f"Figlio/a caro/a, non temere. Come patrono di {specialty.lower() if specialty else 'tante cause'}, pregherò per te e ti accompagnerò nel tuo cammino.",
            f"La tua fede è preziosa. Affido la tua richiesta al Signore e ti proteggerò come ho fatto con tanti altri.",
            f"Non sei solo/a: la mia intercessione sarà con te. Abbi fiducia e persevera nella preghiera.",
            f"Il Signore ascolta chi si affida con cuore sincero. Ti benedico e ti incoraggio a non perdere la speranza.",
            f"Ti sono vicino/a in questo momento. Ricorda che la grazia di Dio opera anche nelle difficoltà."
        ]
        reply = random.choice(replies)
        if quotes:
            n_quotes = random.choice([1, 2, 3]) if len(quotes) >= 3 else min(len(quotes), random.choice([1, 2]))
            selected_quotes = random.sample(quotes, n_quotes)
            quotes_text = '\n'.join([f'"{q}"' for q in selected_quotes])
            reply += f"\n\n{quotes_text}\n- {saint}"
        return reply

    def load_data(self):
        with open('saints.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_saint_of_the_day(self):
        feed_url = "https://feeds.feedburner.com/catholicnewsagency/saintoftheday"
        try:
            resp = requests.get(feed_url, timeout=10)
            feed = feedparser.parse(resp.content)
        except Exception:
            return None
        if not feed.entries:
            return None
        entry = feed.entries[0]
        saint_name = entry.title
        for s in self.saints:
            if s['name'].lower() in saint_name.lower():
                return s
        return None

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

    def show_onboarding(self):
        self.setCurrentWidget(self.onboarding)

    def next_step(self):
        self.setCurrentWidget(self.menu)

    def show_menu(self):
        self.setCurrentWidget(self.menu)

    def show_promemoria(self):
        self.setCurrentWidget(self.promemoria)

    def show_news_vaticano(self):
        self.setCurrentWidget(self.news_vaticano)

    def show_saint(self):
        self.saint_screen.load_saint()
        self.setCurrentWidget(self.saint_screen)

    def show_prega(self):
        self.setCurrentWidget(self.prega_screen)

    def show_in_app_browser(self, url):
        from PyQt5.QtCore import QUrl
        self.in_app_browser.load_url(QUrl(url))
        self.setCurrentWidget(self.in_app_browser)

    def show_bible(self):
        self.bible_screen.load_reading()
        self.setCurrentWidget(self.bible_screen)

class BibleReadingScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setStyleSheet("background: #f5ecd6;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Card overlay
        card = QWidget()
        card.setStyleSheet("""
            background: rgba(255, 248, 220, 0.96);
            border-radius: 32px;
            border: 2px solid #d2b48c;
            box-shadow: 0 8px 32px 0 rgba(120,80,40,0.18);
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 48, 48, 48)
        card_layout.setSpacing(24)
        # Top bar: back icon + title
        top_bar = QHBoxLayout()
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setFixedSize(36, 36)
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        title = QLabel("Lettura Biblica del Giorno")
        title.setFont(QFont("Georgia", 32, QFont.Bold))
        title.setStyleSheet("color: #7c5a1a; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        card_layout.addLayout(top_bar)
        # Reading content in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        reading_widget = QWidget()
        reading_layout = QVBoxLayout(reading_widget)
        reading_layout.setContentsMargins(0, 0, 0, 0)
        reading_layout.setSpacing(0)
        self.reading_label = QLabel()
        self.reading_label.setFont(QFont("Georgia", 20))
        self.reading_label.setStyleSheet("color: #4B2E05; background: transparent;")
        self.reading_label.setWordWrap(True)
        self.reading_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reading_layout.addWidget(self.reading_label)
        scroll_area.setWidget(reading_widget)
        card_layout.addWidget(scroll_area, stretch=1)
        # Center the card in the main layout
        layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.setLayout(layout)
        self.load_reading()
    def load_reading(self):
        import os
        db_path = os.path.join(os.path.dirname(__file__), 'bible_readings.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM readings')
        count = c.fetchone()[0]
        import datetime
        day_of_year = datetime.datetime.now().timetuple().tm_yday
        idx = (day_of_year - 1) % count
        c.execute('SELECT category, title, reference, text FROM readings LIMIT 1 OFFSET ?', (idx,))
        row = c.fetchone()
        conn.close()
        if row:
            category, title, reference, text = row
            html = f"<b>[{category}] {title}</b><br><i>{reference}</i><br><br>{text}"
            self.reading_label.setText(html)
        else:
            self.reading_label.setText("Nessuna lettura trovata.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainStack()
    window.setWindowTitle("SANTETIZZATORE")
    window.show()
    sys.exit(app.exec_())