import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QStackedWidget, QToolButton, QGridLayout, QScrollArea, QScroller, QComboBox, QLineEdit, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QTimer, QEasingCurve, pyqtProperty, QSize, QRectF, QPointF,
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

title_font = QFont("Arial", 40)

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

        def make_btn(text, icon, callback):
            btn = QToolButton()
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumSize(110, 110)
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(48, 48))
            btn.setFont(QFont("Arial", 15, QFont.Bold))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setText(text)
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

        # Reordered buttons
        buttons = [
            ("Santo del giorno", "assets/saint.jpg", self.saint_clicked if not self.saint_callback else self.saint_callback),
            ("Letture Bibliche", "assets/bible.jpg", self.bible_clicked),
            ("Prega", "assets/hands.jpg", self.prega_clicked if not self.prega_callback else self.prega_callback),
            ("Dal Vaticano", "assets/vatican.jpg", self.vatican_callback if self.vatican_callback else self.vatican_clicked),
            ("Promemoria", "assets/bell.jpg", self.promemoria_callback if self.promemoria_callback else self.reminder_clicked),
            ("Trova chiese", "assets/maps.jpg", self.maps_clicked),
        ]

        cols = 3
        rows = (len(buttons) + cols - 1) // cols
        for idx, (text, icon, cb) in enumerate(buttons):
            row = idx // cols
            col = idx % cols
            btn = make_btn(text, icon, cb)
            if text == "Trova chiese":
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QToolButton {
                        background: #f5f5f5;
                        border: 1px solid #e0e0e0;
                        border-radius: 18px;
                        color: #aaa;
                        font-size: 15px;
                        font-weight: bold;
                        padding: 10px 4px 4px 4px;
                    }
                    QToolButton:disabled {
                        background: #f5f5f5;
                        color: #bbb;
                        border: 1px solid #e0e0e0;
                    }
                """)
            grid.addWidget(btn, row, col)

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
    def reminder_clicked(self):
        if self.promemoria_callback:
            self.promemoria_callback()
        else:
            print("Promemoria clicked")
    def vatican_clicked(self):
        print("Dal Vaticano clicked")
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
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(48, 48)
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
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(48, 48)
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
        QScroller.grabGesture(scroll.viewport(), QScroller.LeftMouseButtonGesture)
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
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: #181c24;")
        self.saint_name = ""
        self.saint_image = None
        self.saint_description = ""
        self.circle_diameter = self.CIRCLE_DIAMETER
        self.circle_center = (self.width() // 2, self.height() // 2)

        # Back button - 48x48 touch target (icon stays visually smaller,
        # centered inside it) for comfortable tapping on a touchscreen.
        self.back_btn = ClickableLabel(self)
        pixmap = QPixmap("assets/goback.jpg").scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.back_btn.setPixmap(pixmap)
        self.back_btn.setAlignment(Qt.AlignCenter)
        self.back_btn.setFixedSize(48, 48)
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
        self.name_label.setStyleSheet("color: #fff; background: transparent;")
        self.name_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFixedWidth(self.CONTENT_WIDTH)
        circle_layout.addWidget(self.name_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setFont(QFont("Arial", 13, QFont.StyleItalic))
        self.subtitle_label.setStyleSheet("color: #cdd6f0; background: transparent;")
        self.subtitle_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setFixedWidth(self.CONTENT_WIDTH)
        circle_layout.addWidget(self.subtitle_label)

        circle_layout.addSpacing(8)
        self.festa_label = QLabel()
        self.festa_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.festa_label.setStyleSheet("color: #111; background: #bcd6fc; padding: 2px 10px; border-radius: 4px;")
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
        self.circle_desc_label.setStyleSheet("color: #fff; background: transparent; line-height: 1.5;")
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

        self._position_content()
        self.load_saint()

    def get_ring_opacity(self):
        return self._ring_opacity

    def set_ring_opacity(self, value):
        self._ring_opacity = value
        self.update()

    ring_opacity = pyqtProperty(float, get_ring_opacity, set_ring_opacity)

    def _play_entrance_animation(self):
        if self._entrance_group is not None:
            self._entrance_group.stop()

        self._ring_opacity = 0.0
        for effect in (self._avatar_opacity, self._name_opacity, self._subtitle_opacity,
                       self._festa_opacity, self._bio_opacity):
            effect.setOpacity(0.0)

        group = QParallelAnimationGroup(self)

        ring_anim = QPropertyAnimation(self, b"ring_opacity", self)
        ring_anim.setDuration(500)
        ring_anim.setStartValue(0.0)
        ring_anim.setEndValue(1.0)
        ring_anim.setEasingCurve(QEasingCurve.OutCubic)
        group.addAnimation(ring_anim)

        # (effect, delay before starting, fade duration) - each element
        # rises in a little after the previous one.
        stagger = [
            (self._avatar_opacity, 120, 450),
            (self._name_opacity, 260, 420),
            (self._subtitle_opacity, 340, 400),
            (self._festa_opacity, 400, 400),
            (self._bio_opacity, 480, 500),
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

        self._entrance_group = group
        group.start()

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
        # Draw background
        painter.fillRect(self.rect(), QColor("#181c24"))
        # Draw glowing accent ring - fades and grows in on entrance
        # (ring_opacity animates 0 -> 1 via _play_entrance_animation),
        # otherwise sits at rest fully visible.
        d = self.circle_diameter
        center = self.circle_center
        ring_scale = 0.9 + 0.1 * self._ring_opacity
        ring_half = (d / 2 + 12) * ring_scale
        ring_rect = QRectF(center[0] - ring_half, center[1] - ring_half, ring_half * 2, ring_half * 2)
        grad = QRadialGradient(center[0], center[1], d//2 + 12)
        grad.setColorAt(0.7, QColor(120, 120, 255, 120))
        grad.setColorAt(1.0, QColor(120, 180, 255, 0))
        painter.setOpacity(self._ring_opacity)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(ring_rect)
        painter.setOpacity(1.0)
        # Draw main circle
        painter.setBrush(QColor("#232a3a"))
        painter.setPen(QPen(QColor(120, 180, 255), 4))
        painter.drawEllipse(center[0] - d//2, center[1] - d//2, d, d)
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
        painter.setPen(QPen(QColor(120, 180, 255), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, diameter - 2, diameter - 2)
        painter.end()
        return rounded

    @staticmethod
    def _fit_label_font(label, text, max_width, start_pt=24, min_pt=15, max_lines=2):
        """Shrink the label's font until `text` wraps to at most
        `max_lines` lines within max_width, instead of letting a long
        name overflow or get truncated."""
        pt = start_pt
        while pt > min_pt:
            font = QFont("Arial", pt, QFont.Bold)
            metrics = QFontMetrics(font)
            bounds = metrics.boundingRect(0, 0, max_width, 4000, Qt.TextWordWrap, text)
            if bounds.height() <= metrics.lineSpacing() * max_lines + 4:
                label.setFont(font)
                return
            pt -= 1
        label.setFont(QFont("Arial", min_pt, QFont.Bold))

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
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(48, 48)
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
        saints_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saints.json')
        with open(saints_file, 'r', encoding='utf-8') as f:
            return json.load(f)

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

ITALIAN_MONTHS = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


class BibleReadingScreen(QWidget):
    """A parchment/missal-styled reading card: a rubric line (in the
    liturgical sense - the red instructional line above a reading) and
    an illuminated first letter, evoking an antiphonary page."""

    INK = "#2e2013"
    INK_MUTED = "#4a3a24"
    RUBRIC_RED = "#8a2432"
    PARCHMENT = "#f1e6cd"

    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)

        outer_margin = QVBoxLayout(self)
        outer_margin.setContentsMargins(24, 24, 24, 24)
        outer_frame = QWidget()
        outer_frame.setStyleSheet("background: transparent; border: 1px solid rgba(91,67,38,0.35);")
        outer_margin.addWidget(outer_frame)

        outer_frame_layout = QVBoxLayout(outer_frame)
        outer_frame_layout.setContentsMargins(6, 6, 6, 6)
        inner_frame = QWidget()
        inner_frame.setStyleSheet("background: transparent; border: 1px solid rgba(91,67,38,0.18);")
        outer_frame_layout.addWidget(inner_frame)

        card_layout = QVBoxLayout(inner_frame)
        card_layout.setContentsMargins(48, 22, 48, 26)
        card_layout.setSpacing(0)

        # Top bar: back icon + today's date
        top_bar = QHBoxLayout()
        if back_callback:
            back_icon = ClickableLabel()
            pixmap = QPixmap("assets/goback.jpg").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            back_icon.setPixmap(pixmap)
            back_icon.setAlignment(Qt.AlignCenter)
            back_icon.setFixedSize(48, 48)
            back_icon.setStyleSheet("background: rgba(91,67,38,0.08); border-radius: 24px;")
            back_icon.clicked.connect(back_callback)
            top_bar.addWidget(back_icon, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        self.date_label = QLabel()
        date_font = QFont("Georgia", 12, QFont.Bold)
        date_font.setCapitalization(QFont.SmallCaps)
        date_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        self.date_label.setFont(date_font)
        self.date_label.setStyleSheet(f"color: {self.RUBRIC_RED}; background: transparent;")
        top_bar.addWidget(self.date_label, alignment=Qt.AlignVCenter)
        card_layout.addLayout(top_bar)
        card_layout.addSpacing(6)

        # Rubric line: "Dal Vangelo secondo Luca - 5,1-11"
        self.rubric_label = QLabel()
        rubric_font = QFont("Georgia", 13, QFont.Bold)
        rubric_font.setCapitalization(QFont.SmallCaps)
        rubric_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        self.rubric_label.setFont(rubric_font)
        self.rubric_label.setStyleSheet(f"color: {self.RUBRIC_RED}; background: transparent;")
        self.rubric_label.setAlignment(Qt.AlignHCenter)
        self.rubric_label.setWordWrap(True)
        card_layout.addWidget(self.rubric_label)
        card_layout.addSpacing(6)

        # Pericope title
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Georgia", 19, QFont.Normal, italic=True))
        self.title_label.setStyleSheet(f"color: {self.INK_MUTED}; background: transparent;")
        self.title_label.setAlignment(Qt.AlignHCenter)
        self.title_label.setWordWrap(True)
        card_layout.addWidget(self.title_label)
        card_layout.addSpacing(18)

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
        self.reading_label.setFont(QFont("Georgia", 16))
        self.reading_label.setStyleSheet(f"color: {self.INK}; background: transparent;")
        self.reading_label.setWordWrap(True)
        self.reading_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        reading_layout.addWidget(self.reading_label)
        scroll_area.setWidget(reading_widget)
        card_layout.addWidget(scroll_area, stretch=1)

        self.load_reading()

    def paintEvent(self, event):
        # Paint the parchment fill explicitly rather than relying on a
        # QSS "background:" alone - a plain QWidget's stylesheet
        # background isn't reliably painted on every Qt platform theme,
        # the same class of issue fixed on the Santo del Giorno screen.
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.PARCHMENT))
        painter.end()
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

            self.date_label.setText(f"{today.day} {ITALIAN_MONTHS[today.month - 1]}")
            self.rubric_label.setText(html.escape(f"{category} · {reference}"))
            self.title_label.setText(html.escape(title) if title else "")

            # An illuminated first letter, in place of Qt's rich-text
            # renderer not supporting a true magazine-style floated
            # drop cap: a large colored inline span leading the text.
            first_char, rest = (text[0], text[1:]) if text else ("", "")
            body_html = (
                f'<span style="font-size:32px; font-weight:bold; color:{self.RUBRIC_RED};">{html.escape(first_char)}</span>'
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
    window = MainStack()
    window.setWindowTitle("SANTETIZZATORE")
    window.show()
    sys.exit(app.exec_())