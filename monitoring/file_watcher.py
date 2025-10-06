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

# --- Core Processing Logic ---

def is_downloading(file_path):
	"""
	Checks if a file appears to be incomplete or temporary based on its extension.
	"""
	_, ext = os.path.splitext(file_path)
	return ext.lower() in TEMP_EXTENSIONS

def process_file(file_path):
	"""
	Performs stability check and prints the file path if stable.
	"""
	try:
		if is_downloading(file_path):
			# This case is usually handled by the handler, but serves as a backup
			print(f"Ignoring file in progress: {os.path.basename(file_path)}")
			return

		if wait_for_download_completion(file_path):
			print(f"[FOUND & STABLE] {file_path}")
		else:
			print(f"[FAILED] Could not analyze file: {file_path} (removed or unstable)")

	except Exception as e:
		print(f"Error checking file stability: {e}")

# def scan_directory(path):
# 	"""
# 	Recursively scans a directory for files and processes them.
# 	This handles files already present when the watcher starts, or new directories created.
# 	"""
# 	try:
# 		if not os.path.exists(path):
# 			print(f"Error: Path not found: {path}")
# 			return
			
# 		print(f"Starting initial recursive scan of: {path}")
		
# 		for root, dirs, files in os.walk(path):
# 			# Ignore hidden directories (starting with '.')
# 			dirs[:] = [d for d in dirs if not d.startswith('.')]
			
# 			for file_name in files:
# 				file_path = os.path.join(root, file_name)
# 				# We trust files found during initial scan are stable enough, 
# 				# but we still run the robust check inside process_file.
# 				process_file(file_path)
# 	except Exception as e:
# 		print(f"An error occurred during initial directory scan: {e}")

class NewFileHandler(FileSystemEventHandler):
	"""
	Custom handler to process new file system events from the watcher.
	"""
	def on_created(self, event):
		"""Handles the creation of a new file or directory."""
		path = event.src_path
		
		if event.is_directory:
			print(f"\n[*] New directory detected: {path}")
			# scan_directory(path)
		else:
			print(f"\n[*] New file detected: {os.path.basename(path)}")
			# For new files, process_file handles the stability wait and final print
			process_file(path)

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
	# CRITICAL: Set up the observer to recursively monitor the path
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




# import os
# import time
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# from constants import TEMP_EXTENSIONS

# def is_downloading(file_path):
# 	"""
# 	Checks if a file appears to be incomplete or temporary based on its extension.
# 	"""
# 	return file_path.lower().endswith(TEMP_EXTENSIONS)

# def process_file(file_path):
# 	"""
# 	Performs stability check and prints the file path if stable.
# 	In the full version, this is where the job would be added to the persistent queue.
# 	"""
# 	try:
# 		if is_downloading(file_path):
# 			print(f"Ignoring file in progress: {os.path.basename(file_path)}")
# 			return
		
# 		# Stability check: Wait a moment and check file size stability. 
# 		# This prevents picking up a file that is still actively being written.
# 		initial_size = os.path.getsize(file_path)
# 		time.sleep(1) # Wait 1 second to confirm download/copy is done
# 		current_size = os.path.getsize(file_path)
		
# 		if initial_size == current_size:
# 			# MVP requirement: just print the path
# 			print(f"[FOUND & STABLE] {file_path}")
# 		else:
# 			print(f"Ignoring file: {os.path.basename(file_path)} (Size still changing, likely unstable)")

# 	except FileNotFoundError:
# 		print(f"File disappeared before analysis: {file_path}")
# 	except Exception as e:
# 		print(f"Error checking file stability: {e}")

# def scan_directory(path):
# 	"""
# 	Recursively scans a directory for files and processes them.
# 	This handles files already present when the watcher starts, or new directories created.
# 	"""
# 	try:
# 		if not os.path.exists(path):
# 			print(f"Error: Path not found: {path}")
# 			return
			
# 		print(f"Starting initial scan of: {path}")
		
# 		for root, dirs, files in os.walk(path):
# 			# Ignore hidden directories (starting with '.')
# 			dirs[:] = [d for d in dirs if not d.startswith('.')]
			
# 			for file_name in files:
# 				file_path = os.path.join(root, file_name)
# 				process_file(file_path)
				
# 	except Exception as e:
# 		print(f"An error occurred during initial directory scan: {e}")

# class NewFileHandler(FileSystemEventHandler):
# 	"""
# 	Custom handler to process new file system events from the watcher.
# 	"""
# 	def on_created(self, event):
# 		"""Handles the creation of a new file or directory."""
# 		path = event.src_path
		
# 		if event.is_directory:
# 			print(f"New directory detected: {path}")
# 			# Recursively scan the new directory immediately
# 			scan_directory(path)
# 		elif not is_downloading(path):
# 			print(f"New file creation event detected: {os.path.basename(path)}")
# 			# Process the new file, which includes a stability check
# 			process_file(path)
# 		else:
# 			# We ignore temporary files on creation
# 			print(f"Ignoring temporary/downloading file creation: {os.path.basename(path)}")


# def start_watcher(path_to_watch):
# 	"""
# 	Sets up and starts the file system watcher process.
# 	"""
# 	# 1. Initial Scan: Process files already in the directory
# 	scan_directory(path_to_watch)
		
# 	# 2. Continuous Monitoring: Start the watchdog observer
# 	event_handler = NewFileHandler()
# 	observer = Observer()
		
# 	# Set up the observer to recursively monitor the path
# 	observer.schedule(event_handler, path_to_watch, recursive=True)
# 	observer.start()
		
# 	print(f"\n--- Continuous Monitoring started for path: {path_to_watch} ---\n")
# 	print("Press Ctrl+C to stop the watcher.\n")
		
# 	try:
# 		while True:
# 			time.sleep(5)
# 	except KeyboardInterrupt:
# 		observer.stop()
		
# 	observer.join()
