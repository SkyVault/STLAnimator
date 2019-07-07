from PyQt5.QtWidgets import (
    QWidget,
    )




class TimelineWidget():
    def __init__(self):
        super().__init__(self)

        self.scene = QGraphicsScene(self)
        self.circle = QGraphicsEllipseItem(10, 10, 100, 100)
        self.scene.addItem(self.circle)
