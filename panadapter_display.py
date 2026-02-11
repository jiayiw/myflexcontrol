import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, MouseEvent
import pyqtgraph as pg


class PanadapterWidget(pg.PlotWidget):
    frequency_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setBackground("k")
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel("left", "Signal (dB)", units="")
        self.setLabel("bottom", "Frequency", units="Hz")

        self.curve = self.plot(pen=pg.mkPen("g", width=2))
        self.center_freq_line = self.addLine(
            color="y", width=1, style=Qt.PenStyle.DashLine
        )
        self.cursor_line = self.addLine(color="r", width=2, movable=True)

        self.freq_bins = None
        self.magnitudes = None

        self.plotItem.scene().sigMouseClicked.connect(self._on_scene_clicked)

    def update(self, frequency_bins: np.ndarray, magnitude_db: np.ndarray):
        self.freq_bins = frequency_bins
        self.magnitudes = magnitude_db
        self.curve.setData(frequency_bins, magnitude_db)

    def set_center_frequency(self, hz: int):
        self.center_freq_line.setValue(x=hz)

    def _on_scene_clicked(self, event):
        pos = event.scenePos()
        mouse_point = self.plotItem.vb.mapSceneToView(pos)
        freq = int(mouse_point.x())
        if event.button() == Qt.MouseButton.LeftButton:
            self.frequency_clicked.emit(freq)
