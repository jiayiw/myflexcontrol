import asyncio
from typing import Callable, Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlexRadioClient:
    def __init__(self, host: str, port: int = 4992, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.reader = None
        self.writer = None
        self.sequence = 0
        self.pending_commands: Dict[int, asyncio.Future] = {}
        self.status_callback = None
        self.running = False

    async def connect(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.running = True
            asyncio.create_task(self._receive_responses())
            logger.info(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        self.running = False
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except:
                pass
        self.reader = None
        self.writer = None
        logger.info("Disconnected")

    async def send_command(self, command: str) -> str:
        self.sequence = (self.sequence + 1) % 1000
        seq = self.sequence

        cmd_str = f"C{seq}|{command}\n"
        self.writer.write(cmd_str.encode())
        await self.writer.drain()

        future = asyncio.Future()
        self.pending_commands[seq] = future

        try:
            result = await asyncio.wait_for(future, timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            if seq in self.pending_commands:
                del self.pending_commands[seq]
            raise TimeoutError(f"Command timeout: {command}")

    async def _receive_responses(self):
        while self.running and self.reader:
            try:
                line = await self.reader.readline()
                if not line:
                    break

                line_str = line.decode().strip()

                if not line_str:
                    continue

                if line_str[0] == "H":
                    self._handle_heartbeat(line_str)
                elif line_str[0] == "R":
                    seq, errno, message = self._parse_response(line_str)
                    if seq in self.pending_commands:
                        if errno == "0":
                            self.pending_commands[seq].set_result(message)
                        else:
                            self.pending_commands[seq].set_exception(
                                Exception(f"{errno}: {message}")
                            )
                elif line_str[0] == "S":
                    self._handle_status(line_str)
            except Exception as e:
                logger.error(f"Error receiving response: {e}")
                if not self.running:
                    break

    def _parse_response(self, line: str) -> tuple:
        parts = line[1:].split("|", 2)
        seq = int(parts[0]) if parts else 0
        errno = parts[1] if len(parts) > 1 else "0"
        message = parts[2] if len(parts) > 2 else ""
        return seq, errno, message

    def _handle_heartbeat(self, line: str):
        pass

    def _handle_status(self, line: str):
        if self.status_callback:
            self.status_callback(line)

    def set_status_callback(self, callback: Callable[[str], None]):
        self.status_callback = callback
