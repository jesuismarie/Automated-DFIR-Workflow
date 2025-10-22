import logging
import os
from pathlib import Path

def setup_logging(component: str = "monitoring") -> logging.Logger:
	"""
	Setup logging with file and console output, compatible with both host and Docker container.
	"""
	logger = logging.getLogger(component)
		
	if logger.handlers:
		return logger

	logger.setLevel(logging.INFO)
		
	logger.propagate = False

	if os.path.exists('/analysis/logs'):
		log_dir = Path('/analysis/logs')
	else:
		log_dir = Path.home() / "malware-analysis" / "logs"

	log_dir.mkdir(parents=True, exist_ok=True)

	log_file = log_dir / f"{component}.log"

	formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

	file_handler = logging.FileHandler(log_file)
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(formatter)

	stream_handler = logging.StreamHandler()
	stream_handler.setLevel(logging.INFO)
	stream_handler.setFormatter(formatter)

	logger.addHandler(file_handler)
	logger.addHandler(stream_handler)

	return logger
