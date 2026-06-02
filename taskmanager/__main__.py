from taskmanager.config import settings
from taskmanager.platform import install_windows_asyncio_compat
from taskmanager.server import mcp


def main() -> None:
    install_windows_asyncio_compat()
    settings.ensure_data_dirs()
    mcp.run(transport="http", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
