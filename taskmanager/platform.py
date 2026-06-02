"""Platform-specific runtime adjustments."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

# Cursor and other MCP clients often close streamable-HTTP connections abruptly on
# Windows. asyncio's ProactorEventLoop then logs ConnectionResetError from
# _call_connection_lost — harmless but noisy.
_BENIGN_CONNECTION_ERRORS = (ConnectionResetError, ConnectionAbortedError)


def install_windows_asyncio_compat() -> None:
    """Suppress benign connection-reset noise on Windows before the event loop starts."""
    if sys.platform != "win32":
        return

    from asyncio.proactor_events import _ProactorBasePipeTransport

    if getattr(_ProactorBasePipeTransport, "_taskmanager_patched", False):
        return

    original = _ProactorBasePipeTransport._call_connection_lost

    def _call_connection_lost(
        self: _ProactorBasePipeTransport, exc: BaseException | None
    ) -> None:
        try:
            original(self, exc)
        except _BENIGN_CONNECTION_ERRORS:
            pass

    _ProactorBasePipeTransport._call_connection_lost = _call_connection_lost  # type: ignore[method-assign]
    _ProactorBasePipeTransport._taskmanager_patched = True  # type: ignore[attr-defined]


def _asyncio_exception_handler(
    loop: asyncio.AbstractEventLoop, context: dict[str, Any]
) -> None:
    exc = context.get("exception")
    if isinstance(exc, _BENIGN_CONNECTION_ERRORS):
        return
    loop.default_exception_handler(context)


@asynccontextmanager
async def server_lifespan(_server: Any) -> AsyncIterator[None]:
    """FastMCP lifespan hook: tame Windows connection-reset logging."""
    if sys.platform != "win32":
        yield
        return

    install_windows_asyncio_compat()
    loop = asyncio.get_running_loop()
    previous = loop.get_exception_handler()
    loop.set_exception_handler(_asyncio_exception_handler)
    try:
        yield
    finally:
        loop.set_exception_handler(previous)
