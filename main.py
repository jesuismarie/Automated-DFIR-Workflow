import sys
from monitoring.file_watcher import start_watcher

def main():
	"""
	Main entry point for the file watcher application.
	Handles command-line arguments and starts the watcher.
	"""
	if len(sys.argv) < 2:
		print("Usage: python main.py <path_to_watch>")
		sys.exit(1)

	path_to_watch = sys.argv[1]
	start_watcher(path_to_watch)

if __name__ == "__main__":
	main()
