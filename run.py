import asyncio
import logging
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from flexradio_gui import FlexRadioGUI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)

    try:
        window = FlexRadioGUI()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
