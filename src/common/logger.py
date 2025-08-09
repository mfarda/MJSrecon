import logging
from pathlib import Path
from datetime import datetime

# Using a class for colors is a good practice for organization.
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'  # Added magenta for commands
    NC = '\033[0m' # No Color

class Logger:
    """
    A centralized logger for the application, handling both console and file logging.
    """
    def __init__(self, log_dir: Path, verbose: bool = False, quiet: bool = False, timestamp_format: str = '%H:%M:%S'):
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "mjsrecon.log"
        
        # Determine the logging level for both console and file.
        if quiet:
            self.console_level = logging.WARNING
            self.file_level = logging.INFO # Still log info to file
        elif verbose:
            self.console_level = logging.DEBUG
            self.file_level = logging.DEBUG
        else:
            self.console_level = logging.INFO
            self.file_level = logging.INFO

        # Configure the root logger for file output
        logging.basicConfig(
            level=self.file_level,
            format='%(asctime)s [%(levelname)-8s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=log_file,
            filemode='w'
        )
        
        # Get a logger instance
        self.logger = logging.getLogger("MJSRecon")
        self.quiet = quiet
        self.timestamp_format = timestamp_format

        # Color mapping for console output
        self.color_map = {
            'DEBUG': Colors.NC,
            'INFO': Colors.CYAN,
            'COMMAND': Colors.MAGENTA,  # Added command color
            'SUCCESS': Colors.GREEN,
            'WARNING': Colors.YELLOW,
            'ERROR': Colors.RED,
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in a consistent format."""
        return datetime.now().strftime(self.timestamp_format)

    def _log_to_console(self, level: str, message: str):
        """Prints formatted and colored messages to the console with timestamp."""
        log_level_numeric = logging.getLevelName(level)
        # Fix: Map custom levels to INFO
        if isinstance(log_level_numeric, str):
            log_level_numeric = logging.INFO
        if log_level_numeric >= self.console_level:
            color = self.color_map.get(level, Colors.NC)
            timestamp = self._get_timestamp()
            print(f"[{timestamp}] [{color}{level: <8}{Colors.NC}] {message}")

    def debug(self, message: str):
        self.logger.debug(message)
        self._log_to_console('DEBUG', message)

    def info(self, message: str):
        self.logger.info(message)
        self._log_to_console('INFO', message)
        
    def command(self, message: str):
        # 'COMMAND' is a custom level. We log it as INFO to the file.
        self.logger.info(f"COMMAND: {message}")
        self._log_to_console('COMMAND', message)
        
    def success(self, message: str):
        # 'SUCCESS' is a custom level. We log it as INFO to the file.
        self.logger.info(f"SUCCESS: {message}")
        self._log_to_console('SUCCESS', message)

    def warning(self, message: str):
        self.logger.warning(message)
        self._log_to_console('WARNING', message)

    def error(self, message: str):
        self.logger.error(message)
        self._log_to_console('ERROR', message)
