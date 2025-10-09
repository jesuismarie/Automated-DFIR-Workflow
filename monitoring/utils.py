import os
import time

def wait_for_download_completion(filepath):
	"""
	Waits until a file's size stops changing for a set number of checks.
	"""
	last_size = -1
	check_interval = 1
	stable_checks_needed = 3
	stable_checks = 0

	while stable_checks < stable_checks_needed:
		time.sleep(check_interval)
		try:
			current_size = os.path.getsize(filepath)
			if current_size == last_size:
				stable_checks += 1
			else:
				last_size = current_size
				stable_checks = 0
		except FileNotFoundError:
			print(f"[*] File disappeared during stability check: {os.path.basename(filepath)}")
			return False
	return True
