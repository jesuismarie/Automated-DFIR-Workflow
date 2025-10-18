import os
import sys
import time
import fnmatch
from typing import Dict, Any

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from monitoring.config import load_config
from monitoring.utils import setup_logging, wait_for_download_completion
from constants import TEMP_EXTENSIONS, IGN_EXTENSIONS, IGN_DIRS

logger = setup_logging("monitoring")

class NewFileHandler(FileSystemEventHandler):
	"""
	Custom handler to process new file system events from the watcher.
	"""
	def __init__(self):
		super().__init__()
		self._processed_paths = set()

	def _scan_directory_contents(self, directory_path):
		"""
		Recursively scans a directory (new or moved) and queues all found files.
		"""
		logger.info(f"  [SCAN] Starting recursive scan of directory contents: {directory_path}")

		for root, _, files in os.walk(directory_path):
			if files:
				logger.info(f"  -> Found {len(files)} files in {os.path.basename(root)}")
			for file_name in files:
				file_path = os.path.join(root, file_name)
				if self._is_temp_file(file_path):
					continue
				logger.info(f"  [>] Queuing file for Static/Dynamic analysis: {os.path.normpath(os.path.abspath(file_path))}")

	def _process_new_file(self, path):
		"""
		Handles the stability check and processing of a single file.
		"""
		_, ext = os.path.splitext(path)
		ext = ext.lower()

		if self._is_temp_file(path):
			logger.debug(f"Skipping temporary download file (waiting): {os.path.basename(path)}")
			if wait_for_download_completion(path):
				logger.info(f"[*] File ready for analysis after wait: {path}")
				logger.info(f"  [>] Queuing file for Static/Dynamic analysis: {os.path.normpath(os.path.abspath(path))}")
		elif self._is_ign_file(path):
			logger.debug(f"Ignoring file: {os.path.basename(path)}")
		else:
			logger.info(f"  [>] Queuing file for Static/Dynamic analysis: {os.path.normpath(os.path.abspath(path))}")

	def _is_temp_file(self, path: str) -> bool:
		"""Return True if the filename matches any pattern in TEMP_EXTENSIONS.
		Uses fnmatch to allow wildcard patterns like '.com.google.Chrome.*'.
		"""
		fname = os.path.basename(path)
		for pat in TEMP_EXTENSIONS:
			pattern = pat if pat.startswith('*') else f"*{pat}"
			try:
				if fnmatch.fnmatch(fname, pattern):
					return True
			except Exception:
				if fname.lower().endswith(pat.lower()):
					return True
		return False

	def _is_ign_dir(self, path):
		"""
		Checks if the given path contains any directory from the ignore list.
		This allows checking any sub-path of the event source.
		"""
		path = os.path.expanduser(path)
		trash_dir = os.path.expanduser("~/.local/share/Trash/files")

		if path.startswith(trash_dir):
			return False

		for ign in IGN_DIRS:
			if ign in path:
				return True
		return False

	def _is_ign_file(self, path: str) -> bool:
		"""
		Return True if the filename matches any pattern in IGN_EXTENSIONS.
		Uses fnmatch to allow wildcard patterns like '*~'.
		"""
		fname = os.path.basename(path)
		for pat in IGN_EXTENSIONS:
			pattern = pat if pat.startswith('*') else f"*{pat}"
			try:
				if fnmatch.fnmatch(fname, pattern):
					return True
			except Exception:
				if fname.lower().endswith(pat.lower()):
					return True
		return False

	def on_created(self, event):
		"""
		Handles the creation of a new file or directory.
		"""
		path = event.src_path

		if path in self._processed_paths:
			return
		self._processed_paths.add(path)

		if not self._is_ign_dir(path):
			if event.is_directory:
				logger.info(f"\n[*] New directory detected: {path}")
				self._scan_directory_contents(path)
			else:
				self._process_new_file(path)

	def on_moved(self, event):
		"""
		Handles file or directory renames/moves (critical for finalized downloads).
		"""
		path = event.dest_path

		if not self._is_ign_dir(path):
			if event.is_directory:
				logger.info(f"\n[*] Directory moved/renamed detected: {path}")
				self._scan_directory_contents(path)
			else:
				logger.info(f"\n[*] File moved/renamed detected (Finalizing download): {path}")
				self._process_new_file(path)

	def on_deleted(self, event):
		"""
		Handles the removal of a file or directory.
		"""
		path = event.src_path

		if path not in self._processed_paths:
			return

		if not self._is_ign_dir(path):
			if event.is_directory:
				logger.info(f"\n[*] Directory DELETED: {path}")
			else:
				logger.info(f"\n[*] File DELETED: {path}")

def start_watcher(config: Dict[str, Any]):
	"""
	Sets up and starts the file system watcher process.
	"""
	monitored_directory = os.path.abspath(os.path.expanduser(config.get('watch_directory')))

	if not os.path.isdir(monitored_directory):
		logger.warning(f"Error: Directory '{monitored_directory}' does not exist.")
		sys.exit(1)

	event_handler = NewFileHandler()
	observer = Observer()
	observer.schedule(event_handler, monitored_directory, recursive=config.get('recursive'))

	logger.info("[*] Press Ctrl+C to stop the watcher.")

	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()
	logger.debug("\n[*] File watcher stopped.")

def main():
	"""
	Main entry point.
	"""
	try:
		config = load_config()
		start_watcher(config)
	except KeyboardInterrupt:
		logger.info("Monitoring stopped by user")
	except Exception as e:
		logger.error(f"Fatal error: {str(e)}")
		sys.exit(1)

if __name__ == "__main__":
	main()
