import os
import time
import logging
from pathlib import Path

def setup_logging(component: str = "monitoring") -> logging.Logger:
	"""
	Setup logging with file and console output.
	"""
	log_dir = Path.home() / "malware-analysis" / "logs"
	log_dir.mkdir(parents=True, exist_ok=True)

	log_file = log_dir / f"{component}.log"

	logging.basicConfig(
		level=logging.INFO,
		format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
		handlers=[
			logging.FileHandler(log_file),
			logging.StreamHandler()
		]
	)
	return logging.getLogger(component)

def wait_for_download_completion(filepath: str, timeout: int = 60, check_interval: int = 1, stable_checks_needed: int = 3) -> bool:
	"""
	Waits until a file's size stops changing for a set number of checks, with a total timeout.
	"""
	if not os.path.exists(filepath):
		return False

	start_time = time.time()
	last_size = -1
	stable_checks = 0

	while time.time() - start_time < timeout:
		time.sleep(check_interval)
		
		try:
			current_size = os.path.getsize(filepath)
			
			if current_size == last_size and current_size != -1:
				stable_checks += 1
				if stable_checks >= stable_checks_needed:
					return True
			else:
				last_size = current_size
				stable_checks = 0
				
		except FileNotFoundError:
			return False
		except OSError:
			pass 

	return False
