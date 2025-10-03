import time
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from constants import TEMP_EXTENSIONS

def wait_for_download_completion(filepath):
	"""
	Waits until a file's size stops changing, indicating the download is complete.
	:param filepath: The path to the file being downloaded.
	:return: True if the file download completes, False if the file is not found.
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
			return False
	return True

class NewFileHandler(FileSystemEventHandler):
	"""
	Handles file system events, specifically the creation of new files, 
	and waits for them to complete downloading before logging.
	"""
	def on_created(self, event):
		"""
		Called when a new file or directory is created.
		"""
		if not event.is_directory:
			_, file_extension = os.path.splitext(event.src_path)

			if file_extension.lower() in TEMP_EXTENSIONS:
				print(f"Ignoring temporary download file: {event.src_path}")
				return

			print(f"New file detected: {event.src_path}")

			if wait_for_download_completion(event.src_path):
				print(f"[*] File ready for analysis: {event.src_path}")
				print("Proceeding with analysis...")
				# analyze
			else:
				print("Could not analyze file, as it was not found or was removed.")

def start_watcher(path_to_watch):
	"""
	Sets up and starts the file system watcher for a given directory.
	:param path_to_watch: The path of the directory to monitor.
	"""
	monitored_directory = os.path.abspath(os.path.expanduser(path_to_watch))

	if not os.path.exists(monitored_directory):
		print(f"Error: Directory '{monitored_directory}' does not exist.")
		sys.exit(1)

	event_handler = NewFileHandler()
	observer = Observer()
	observer.schedule(event_handler, monitored_directory, recursive=False)

	print(f"[*] Monitoring directory: {monitored_directory}")
	print("[*] Press Ctrl+C to stop.")

	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()
	print("\n[*] File watcher stopped.")
