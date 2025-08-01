import shutil
from pathlib import Path
from .config import CONFIG
from .logger import Logger

def check_tools(logger: Logger) -> bool:
    """
    Verifies that all required external and internal tools/scripts are available.
    
    Args:
        logger: The logger instance.

    Returns:
        True if all tools are found, False otherwise.
    """
    logger.info("Checking for required tools...")
    required_tools = set(CONFIG['tools']['required'])
    required_tools.update(CONFIG['tools'].get('full_mode', []))
    
    # Also ensure python3 is available for our own scripts
    required_tools.add('python3')

    all_ok = True

    for tool in sorted(list(required_tools)):
        if shutil.which(tool) is None:
            logger.error(f"Required tool '{tool}' is not installed or not in PATH.")
            all_ok = False
        else:
            logger.debug(f"Found tool: {tool}")

    python_tools = CONFIG['tools'].get('python_tools', {})
    for script_name, script_path in python_tools.items():
        script_path = Path(script_path)
        if not script_path.exists():
            logger.error(f"Required script '{script_name}' not found at {script_path}")
            all_ok = False
        else:
            logger.debug(f"Found script: {script_name} at {script_path}")

    if all_ok:
        logger.success("All required tools and scripts are available.")
    else:
        logger.error("One or more required tools/scripts are missing. Please install them and try again.")
        
    return all_ok
