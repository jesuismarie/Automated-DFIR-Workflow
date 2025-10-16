import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from monitoring.utils import wait_for_download_completion
from constants import TEMP_EXTENSIONS, ARCHIVE_EXTENSIONS

class NewFileHandler(FileSystemEventHandler):
	"""
	Custom handler to process new file system events from the watcher.
	"""
	def __init__(self):
		super().__init__()
		self._processed_paths = set()

	def _queue_file_for_analysis(self, filepath):
		"""
		Placeholder for adding a file to the secure analysis queue.
		"""
		print(f"  [>] Queuing file for Static/Dynamic analysis: {os.path.normpath(os.path.abspath(filepath))}")

	def _scan_directory_contents(self, directory_path):
		"""
		Recursively scans a directory (new or moved) and queues all found files.
		"""
		print(f"  [SCAN] Starting recursive scan of directory contents: {directory_path}")

		for root, dir, files in os.walk(directory_path):
			if files:
				print(f"  -> Found {len(files)} files in {os.path.basename(root)}")
			for file_name in files:
				file_path = os.path.join(root, file_name)
				if os.path.splitext(file_path)[1].lower() not in TEMP_EXTENSIONS:
					if os.path.isdir(file_path):
						self._scan_directory_contents(file_path)
					else:
						self._queue_file_for_analysis(file_path)

	def _process_new_file(self, path):
		"""
		Handles the stability check and processing of a single file.
		"""
		_, ext = os.path.splitext(path)
		ext = ext.lower()

		if ext in TEMP_EXTENSIONS:
			print(f"Ignoring temporary download file: {os.path.basename(path)}")
			if wait_for_download_completion(path):
				print(f"[*] File ready for analysis: {path}")
		self._queue_file_for_analysis(path)

	def on_created(self, event):
		"""
		Handles the creation of a new file or directory.
		"""
		path = event.src_path

		if path in self._processed_paths:
			return
		self._processed_paths.add(path)

		if event.is_directory:
			print(f"\n[*] New directory detected: {path}")
			self._scan_directory_contents(path)
		else:
			self._process_new_file(path)

	def on_moved(self, event):
		"""
		Handles file or directory renames/moves (critical for finalized downloads).
		"""
		dest_path = event.dest_path

		if dest_path in self._processed_paths:
			return
		self._processed_paths.add(dest_path)

		if event.is_directory:
			print(f"\n[*] Directory moved/renamed detected: {dest_path}")
			self._scan_directory_contents(dest_path)
		else:
			print(f"\n[*] File moved/renamed detected (Finalizing download): {dest_path}")
			self._process_new_file(dest_path)

	def on_deleted(self, event):
		"""
		Handles the removal of a file or directory.
		"""
		path = event.src_path

		if event.is_directory:
			print(f"\n[*] Directory DELETED: {path}")
		else:
			print(f"\n[*] File DELETED: {path}")

def start_watcher(path_to_watch):
	"""
	Sets up and starts the file system watcher process.
	"""
	monitored_directory = os.path.abspath(os.path.expanduser(path_to_watch))

	if not os.path.isdir(monitored_directory):
		print(f"Error: Directory '{monitored_directory}' does not exist.")
		sys.exit(1)

	event_handler = NewFileHandler()
	observer = Observer()
	observer.schedule(event_handler, monitored_directory, recursive=True)

	print("[*] Press Ctrl+C to stop the watcher.")

	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()
	print("\n[*] File watcher stopped.")
