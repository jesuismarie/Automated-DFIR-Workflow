import time
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from constants import TEMP_EXTENSIONS

def wait_for_download_completion(filepath):
	"""
	Waits until a file's size stops changing for a set number of checks,
	indicating the download or copy operation is complete and the file is stable.

	:param filepath: The path to the file.
	:return: True if the file download completes/stabilizes, False if the file is removed during the wait.
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

class NewFileHandler(FileSystemEventHandler):
	"""
	Custom handler to process new file system events from the watcher.
	"""
	def on_created(self, event):
		"""Handles the creation of a new file or directory."""
		path = event.src_path
		
		if event.is_directory:
			print(f"\n[*] New directory detected: {path}")
			print(f"Starting scanning directory: {path}")
		else:
			_, file_extension = os.path.splitext(event.src_path)
			if file_extension.lower() in TEMP_EXTENSIONS:
				print(f"Ignoring temporary download file: {event.src_path}")
				if wait_for_download_completion(event.src_path):
					print(f"[*] File ready for analysis: {event.src_path}")
				return
			print(f"[*] New file detected: {event.src_path}")
			# analyze

def start_watcher(path_to_watch):
	"""
	Sets up and starts the file system watcher process.
	:param path_to_watch: The path of the directory to monitor.
	"""
	monitored_directory = os.path.abspath(os.path.expanduser(path_to_watch))

	if not os.path.isdir(monitored_directory):
		print(f"Error: Directory '{monitored_directory}' does not exist.")
		sys.exit(1)

	event_handler = NewFileHandler()
	observer = Observer()
	observer.schedule(event_handler, monitored_directory, recursive=True)

	print(f"[*] Monitoring directory: {monitored_directory}")
	print("[*] Press Ctrl+C to stop the watcher..")

	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()
