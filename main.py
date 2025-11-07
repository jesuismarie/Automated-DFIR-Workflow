import sys

from monitoring.config import load_config
from monitoring.file_watcher import start_watcher
from logger import setup_logging

logger = setup_logging("main")

def main():
	"""
	Main entry point.
	"""
	try:
		config = load_config()
		start_watcher(config)
	except Exception as e:
		logger.error(f"Fatal error: {str(e)}")
		sys.exit(1)

if __name__ == "__main__":
	main()
