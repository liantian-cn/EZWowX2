import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, cast
from PySide6.QtCore import QThread
logger: logging.Logger = logging.getLogger(__name__)

class PixelDumpHTTPServer(HTTPServer):
    allow_reuse_address: bool = True

    def __init__(self, server_address: tuple[str, int], request_handler_class: type[BaseHTTPRequestHandler], get_pixel_dump: Callable[[], dict[str, Any]]) -> None:
        self.get_pixel_dump: Callable[[], dict[str, Any]] = get_pixel_dump
        super().__init__(server_address, request_handler_class)

class PixelDumpRequestHandler(BaseHTTPRequestHandler):

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        data: bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def _handle_pixel_dump(self) -> None:
        try:
            server: PixelDumpHTTPServer = cast(PixelDumpHTTPServer, self.server)
            pixel_dump: dict[str, Any] = server.get_pixel_dump()
        except Exception as exc:
            logger.exception('获取 pixel_dump 失败')
            # details here is an exception string; business validation may return a list.
            self._send_json(500, {'error': 'failed to get pixel dump', 'details': str(exc)})
            return
        self._send_json(200, pixel_dump)

    def do_GET(self) -> None:
        # Intentionally keep a single payload endpoint for any path.
        self._handle_pixel_dump()

    def do_HEAD(self) -> None:
        self._handle_pixel_dump()

    def do_POST(self) -> None:
        # Intentionally use default HTTPServer 405 behavior for non-GET API access.
        self.send_error(405, 'Method Not Allowed')

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - overrides BaseHTTPRequestHandler signature
        return

class WebServerWorker(QThread):

    def __init__(self, get_pixel_dump_callback: Callable[[], dict[str, Any]], host: str='0.0.0.0', port: int=65131) -> None:
        super().__init__()
        self._get_pixel_dump: Callable[[], dict[str, Any]] = get_pixel_dump_callback
        self._host: str = host
        self._port: int = port
        self._server: PixelDumpHTTPServer | None = None

    def run(self) -> None:
        try:
            self._server = PixelDumpHTTPServer((self._host, self._port), PixelDumpRequestHandler, self._get_pixel_dump)
            self._server.serve_forever(poll_interval=0.2)
        except Exception:
            logger.exception('HTTP服务器启动失败')
        finally:
            if self._server is not None:
                self._server.server_close()
                self._server = None

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
        self.wait(1000)
