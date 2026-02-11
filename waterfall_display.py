import numpy as np
import pyqtgraph as pg


class WaterfallWidget(pg.GraphicsLayoutWidget):
    def __init__(self, history_lines: int = 100):
        super().__init__()
        self.history_lines = history_lines
        self.buffer = np.zeros((history_lines, 1024))

        self.img = pg.ImageItem()
        self.addItem(self.img)

        colormap = pg.colormap.get("inferno")
        self.img.setLookupTable(colormap)

    def update(self, new_line: np.ndarray):
        self.buffer = np.roll(self.buffer, -1, axis=0)
        self.buffer[-1] = new_line
        self.img.setImage(self.buffer, autoLevels=False, levels=(0, 255))

    def clear(self):
        self.buffer = np.zeros((self.history_lines, 1024))
        self.img.setImage(self.buffer)
