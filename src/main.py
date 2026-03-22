import sys

from PySide6.QtWidgets import QApplication

from src.common.config import Config
from src.common.logger import setup_logger
from src.model.store.token_store import TokenStore
from src.view.main_window import MainWindow


def main():
    """Application entrypoint"""
    # Load configuration
    config = Config()

    # Setup logger
    logger = setup_logger(config.log_file)
    logger.info(f"TrackSwop v{config.version} starting...")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    app.setOrganizationName("TrackSwop")

    # Create stores
    token_store = TokenStore(
        path=config.token_store_path,
        master_key=config.master_key,
    )

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("MainWindow shown")

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
