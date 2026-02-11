import sys
import asyncio
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from flexradio_gui import FlexRadioGUI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)

    try:
        window = FlexRadioGUI()
        window.show()

        loop = asyncio.get_event_loop()

        timer = QTimer()
        timer.timeout.connect(lambda: loop.call_soon(loop.stop))
        timer.start(10)

        while window.isVisible():
            try:
                loop.run_until_complete(asyncio.sleep(0.01))
                app.processEvents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event loop: {e}")

        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        sys.exit(0)

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
