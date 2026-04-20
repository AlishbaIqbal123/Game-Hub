from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


class FadeStackedWidget(QStackedWidget):
    """Stacked widget with a soft slide and fade transition for screen changes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._animation_group = None
        self._animating = False

    def set_current_index_animated(self, index: int) -> None:
        if index == self.currentIndex():
            return

        # Stop any in-progress animation before starting a new one
        if self._animation_group is not None and self._animating:
            self._animation_group.stop()
            self._animation_group = None
            self._animating = False

        next_widget = self.widget(index)
        final_pos = next_widget.pos()

        # Clear any leftover graphics effect before applying a new one
        next_widget.setGraphicsEffect(None)

        effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        super().setCurrentIndex(index)
        next_widget.move(final_pos + QPoint(26, 0))

        fade = QPropertyAnimation(effect, b"opacity", self)
        fade.setDuration(280)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.InOutCubic)

        slide = QPropertyAnimation(next_widget, b"pos", self)
        slide.setDuration(280)
        slide.setStartValue(final_pos + QPoint(26, 0))
        slide.setEndValue(final_pos)
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(fade)
        group.addAnimation(slide)

        def cleanup() -> None:
            next_widget.move(final_pos)
            next_widget.setGraphicsEffect(None)
            self._animating = False

        group.finished.connect(cleanup)
        self._animation_group = group
        self._animating = True
        group.start()


def animate_reveal(widget: QWidget, *, delay_ms: int = 0, duration: int = 320) -> None:
    """Safely fade a widget in when it first appears on screen."""

    # Clear any existing effect so re-shows always animate cleanly
    widget.setGraphicsEffect(None)

    def start() -> None:
        # Guard: widget may have been hidden or destroyed before the timer fires
        if not widget.isVisible():
            return

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        fade = QPropertyAnimation(effect, b"opacity", widget)
        fade.setDuration(duration)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.InOutCubic)

        group = QParallelAnimationGroup(widget)
        group.addAnimation(fade)

        def cleanup() -> None:
            widget.setGraphicsEffect(None)

        group.finished.connect(cleanup)
        widget._reveal_animation = group  # type: ignore[attr-defined]
        group.start()

    QTimer.singleShot(delay_ms, start)
