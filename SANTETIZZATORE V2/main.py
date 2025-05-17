import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QProgressBar, QPushButton, QLabel, QHBoxLayout, QSizePolicy, QStackedWidget, QToolButton, QGridLayout, QSpacerItem, QCheckBox, QScrollArea
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimer, QEasingCurve, pyqtProperty, QSize, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QFontDatabase, QIcon, QPen, QPixmap
import math
import feedparser
import webbrowser

# Load the font
# font_id = QFontDatabase.addApplicationFont("assets/fonts/10Pixel-Thin.ttf")
# font_families = QFontDatabase.applicationFontFamilies(font_id)
# print("Loaded font families:", font_families)  # For debugging
# if font_families:
#     title_font = QFont(font_families[0], 40)
# else:
#     title_font = QFont("Arial", 40)  # fallback
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

        # Italiano button
        lang_btn = QPushButton("Italiano")
        lang_btn.setFont(QFont("Arial", 15))
        lang_btn.setEnabled(False)
        lang_btn.setMinimumHeight(44)
        lang_btn.setMinimumWidth(120)
        lang_btn.setIcon(QIcon.fromTheme("flag"))
        lang_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                color: #222;
                font-weight: 500;
                font-size: 15px;
                min-height: 44px;
                min-width: 120px;
                padding: 0 0 0 12px;
                text-align: left;
            }
        """)
        lang_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(lang_btn)
        layout.addSpacing(12)

        # Cattolica button
        rel_btn = QPushButton("Cattolica")
        rel_btn.setFont(QFont("Arial", 15))
        rel_btn.setEnabled(False)
        rel_btn.setMinimumHeight(44)
        rel_btn.setMinimumWidth(120)
        rel_btn.setIcon(QIcon.fromTheme("emblem-favorite"))  # heart/cross icon
        rel_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                color: #222;
                font-weight: 500;
                font-size: 15px;
                min-height: 44px;
                min-width: 120px;
                padding: 0 0 0 12px;
                text-align: left;
            }
        """)
        rel_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(rel_btn)
        layout.addSpacing(24)

        # Continue button
        self.cont_btn = QPushButton("Continua")
        self.cont_btn.setFont(QFont("Arial", 17, QFont.Bold))
        self.cont_btn.setMinimumHeight(44)
        self.cont_btn.setIcon(QIcon.fromTheme("go-next"))
        self.cont_btn.setStyleSheet("""
            QPushButton {
                background: #007aff;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 17px;
                min-height: 44px;
            }
            QPushButton:pressed {
                background: #005ecb;
            }
        """)
        self.cont_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.cont_btn)
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
    def __init__(self, promemoria_callback=None, vatican_callback=None):
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

        buttons = [
            ("Santo del giorno", "assets/saint.jpg", self.saint_clicked),
            ("Promemoria", "assets/bell.jpg", self.promemoria_callback if self.promemoria_callback else self.reminder_clicked),
            ("Letture Bibliche", "assets/bible.jpg", self.bible_clicked),
            ("Prega", "assets/hands.jpg", self.pray_clicked),
            ("Rosario", "assets/rosary.jpg", self.rosary_clicked),
            ("News dal Vaticano", "assets/vatican.jpg", self.vatican_callback if self.vatican_callback else self.vatican_clicked),
            ("Trova chiese", "assets/maps.jpg", self.maps_clicked),
        ]

        cols = 3
        rows = (len(buttons) + cols - 1) // cols
        for idx, (text, icon, cb) in enumerate(buttons):
            row = idx // cols
            col = idx % cols
            grid.addWidget(make_btn(text, icon, cb), row, col)

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
        print("Santo del giorno clicked")
    def bible_clicked(self):
        print("Letture bibliche clicked")
    def _promemoria_clicked(self):
        if self.promemoria_callback:
            self.promemoria_callback()
    def vatican_clicked(self):
        print("News dal Vaticano clicked")
    def pray_clicked(self):
        print("Prega clicked")
    def rosary_clicked(self):
        print("Rosario clicked")
    def maps_clicked(self):
        print("Trova chiese clicked")

# --- Promemoria Screen ---
class PromemoriaScreen(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self._gradient_angle = 0.0
        self._ray_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.animate_gradient)
        self._timer.start(50)

        # Use a scroll area for the main content
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

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
        title = QLabel("Promemoria")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #333; background: transparent;")
        top_bar.addWidget(title, alignment=Qt.AlignVCenter)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        reminders = [
            ("Morning prayers", "07:00"),
            ("Midday prayers", "12:00"),
            ("Evening prayer", "16:00"),
            ("Rosary", "18:00"),
            ("Night prayer", "20:00"),
        ]

        # Use a grid layout for reminders
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 2)  # alarm name, less expansion
        grid.setColumnStretch(1, 1)  # time, a bit more space
        grid.setColumnStretch(2, 1)  # toggle, more space than before
        for i, (label, time) in enumerate(reminders):
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 12))
            lbl.setStyleSheet("color: #222; background: transparent;")
            time_lbl = QLabel(time)
            time_lbl.setFont(QFont("Arial", 12, QFont.Bold))
            time_lbl.setStyleSheet("color: #555; background: transparent;")
            time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            switch = IOSSwitch(checked=True)
            grid.addWidget(lbl, i, 0, alignment=Qt.AlignVCenter)
            grid.addWidget(time_lbl, i, 1, alignment=Qt.AlignVCenter)
            grid.addWidget(switch, i, 2, alignment=Qt.AlignVCenter)
        layout.addLayout(grid)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

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
    def __init__(self, back_callback=None):
        super().__init__()
        self.setFixedSize(1080, 720)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self._gradient_angle = 0.0
        self._ray_phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.animate_gradient)
        self._timer.start(50)
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
        title = QLabel("News dal Vaticano")
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

    def load_news(self):
        feed_url = "https://www.vaticannews.va/it.rss.xml"
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            msg = QLabel("Nessuna notizia disponibile.")
            msg.setFont(QFont("Arial", 14, QFont.Bold))
            msg.setStyleSheet("color: #888; background: transparent;")
            self.news_layout.addWidget(msg)
            return
        for entry in feed.entries[:10]:
            news_widget = QWidget()
            news_widget.setStyleSheet("background: transparent;")
            news_layout = QVBoxLayout(news_widget)
            news_layout.setContentsMargins(0, 0, 0, 0)
            news_layout.setSpacing(2)
            title = QLabel(entry.title)
            title.setFont(QFont("Arial", 15, QFont.Bold))
            title.setStyleSheet("color: #222; background: transparent;")
            title.setWordWrap(True)
            summary = QLabel(entry.summary)
            summary.setFont(QFont("Arial", 12))
            summary.setStyleSheet("color: #444; background: transparent;")
            summary.setWordWrap(True)
            link = entry.link
            title.mousePressEvent = lambda e, url=link: webbrowser.open(url)
            title.setCursor(Qt.PointingHandCursor)
            news_layout.addWidget(title)
            news_layout.addWidget(summary)
            self.news_layout.addWidget(news_widget)

# --- Main App ---
class MainStack(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.intro = CinematicIntro(on_finished=self.show_onboarding)
        self.onboarding = OnboardingScreen()
        self.menu = MainMenuScreen(promemoria_callback=self.show_promemoria, vatican_callback=self.show_news_vaticano)
        self.promemoria = PromemoriaScreen(back_callback=self.show_menu)
        self.news_vaticano = NewsVaticanoScreen(back_callback=self.show_menu)
        self.addWidget(self.intro)
        self.addWidget(self.onboarding)
        self.addWidget(self.menu)
        self.addWidget(self.promemoria)
        self.addWidget(self.news_vaticano)
        self.setCurrentWidget(self.intro)
        self.onboarding.cont_btn.clicked.connect(self.next_step)
        # Connect promemoria button
        self.menu.promemoria_callback = self.show_promemoria
        self.menu.vatican_callback = self.show_news_vaticano

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainStack()
    window.setWindowTitle("SANTETIZZATORE")
    window.show()
    sys.exit(app.exec_())