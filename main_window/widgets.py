from PyQt6.QtWidgets import QSlider, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QTimer
from animations import add_click_bounce


class NonScrollSlider(QSlider):
    """自定义滑块：屏蔽鼠标滚轮改变值的行为，允许外层 ScrollArea 继续滚动"""
    def wheelEvent(self, event):
        event.ignore()


class DeploySuccessPopup(QLabel):
    """带有高强超调 Bounce 动效的成功弹出浮动横幅"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("GlassCard")
        self.setStyleSheet(
            "background-color: rgba(37, 99, 235, 0.95); color: white; "
            "font-weight: bold; border-radius: 12px; padding: 14px 24px;"
            "border: 1px solid rgba(255, 255, 255, 0.2);"
        )
        self.adjustSize()
        if parent:
            start_x = (parent.width() - self.width()) // 2
            start_y = parent.height() + 30
            target_y = parent.height() - self.height() - 35
            self.setGeometry(start_x, start_y, self.width(), self.height())

            self.anim = QPropertyAnimation(self, b"geometry")
            self.anim.setDuration(550)
            self.anim.setStartValue(QRect(start_x, start_y, self.width(), self.height()))
            self.anim.setEndValue(QRect(start_x, target_y, self.width(), self.height()))
            # 使用更强的 OutBack 回弹效果
            self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
            self.show()
            self.anim.start()

            QTimer.singleShot(3800, self.fadeOut)

    def fadeOut(self):
        self.eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.eff)
        self.fade = QPropertyAnimation(self.eff, b"opacity")
        self.fade.setDuration(450)
        self.fade.setStartValue(1.0)
        self.fade.setEndValue(0.0)
        self.fade.finished.connect(self.deleteLater)
        self.fade.start()