import sys
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget, QPushButton


def play_bounce_in(widget: QWidget, duration=500, delay=10):
    """为控件添加从下方+微缩放弹跳出现的 QEasingCurve.Type.OutBack 动效 (防窗口闪烁版)"""
    def _start_anim():
        if not widget:
            return

        # 如果是 Top-Level 独立窗口 (如 QDialog)，直接对 OS 窗口做 Geometry 变换会导致闪烁/跳动
        # 此时采用极简平滑 Fade-In 渐变，避免 OS 窗口框架闪烁
        if widget.isWindow():
            opacity_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(opacity_effect)
            fade_anim = QPropertyAnimation(opacity_effect, b"opacity")
            fade_anim.setDuration(int(duration * 0.8))
            fade_anim.setStartValue(0.0)
            fade_anim.setEndValue(1.0)
            fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            fade_anim.finished.connect(lambda: widget.setGraphicsEffect(None))
            fade_anim.start()
            widget._window_fade = fade_anim
            return

        # 内部 Child 控件 (如卡片、容器 Widget)：执行流畅弹跳 + 淡入
        orig_geo = widget.geometry()
        if orig_geo.width() <= 1 or orig_geo.height() <= 1:
            return

        offset_y = 18
        shrink_w = int(orig_geo.width() * 0.05)
        shrink_h = int(orig_geo.height() * 0.05)

        start_geo = QRect(
            orig_geo.x() + shrink_w // 2,
            orig_geo.y() + offset_y + shrink_h // 2,
            max(1, orig_geo.width() - shrink_w),
            max(1, orig_geo.height() - shrink_h)
        )

        anim = QPropertyAnimation(widget, b"geometry")
        anim.setDuration(duration)
        anim.setStartValue(start_geo)
        anim.setEndValue(orig_geo)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)

        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        fade_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_anim.setDuration(int(duration * 0.5))
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _cleanup():
            if widget:
                widget.setGraphicsEffect(None)
                widget.setGeometry(orig_geo)

        anim.finished.connect(_cleanup)

        anim.start()
        fade_anim.start()

        widget._bounce_anim = anim
        widget._fade_anim = fade_anim

    QTimer.singleShot(max(1, delay), _start_anim)


def add_click_bounce(btn: QPushButton):
    """给按钮绑定弹性下压反馈，锁定原始尺寸，防止多次连续点击导致按钮不断变小的 Bug"""
    orig_press = btn.mousePressEvent
    orig_release = btn.mouseReleaseEvent

    def custom_press(event):
        if not btn.property("_anim_running"):
            btn._normal_geo = btn.geometry()
            btn.setProperty("_anim_running", True)

        normal = btn._normal_geo

        if hasattr(btn, "_press_anim") and btn._press_anim:
            btn._press_anim.stop()
        if hasattr(btn, "_release_anim") and btn._release_anim:
            btn._release_anim.stop()

        pressed_geo = QRect(
            normal.x() + 2,
            normal.y() + 2,
            max(1, normal.width() - 4),
            max(1, normal.height() - 4)
        )

        anim = QPropertyAnimation(btn, b"geometry", btn)
        anim.setDuration(80)
        anim.setStartValue(btn.geometry())
        anim.setEndValue(pressed_geo)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start()
        btn._press_anim = anim

        if orig_press:
            orig_press(event)

    def custom_release(event):
        if hasattr(btn, "_normal_geo"):
            normal = btn._normal_geo

            if hasattr(btn, "_press_anim") and btn._press_anim:
                btn._press_anim.stop()
            if hasattr(btn, "_release_anim") and btn._release_anim:
                btn._release_anim.stop()

            anim = QPropertyAnimation(btn, b"geometry", btn)
            anim.setDuration(350)
            anim.setStartValue(btn.geometry())
            anim.setEndValue(normal)
            anim.setEasingCurve(QEasingCurve.Type.OutElastic)

            def _on_finish():
                btn.setGeometry(normal)
                btn.setProperty("_anim_running", False)

            anim.finished.connect(_on_finish)
            anim.start()
            btn._release_anim = anim

        if orig_release:
            orig_release(event)

    btn.mousePressEvent = custom_press
    btn.mouseReleaseEvent = custom_release


def play_fade_in_animation(widget, duration=500):
    play_bounce_in(widget, duration=duration)