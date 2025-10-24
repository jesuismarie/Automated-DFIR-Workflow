import os
import json
import magic
import shutil
import hashlib
from typing import Dict, List
from datetime import datetime
from filelock import FileLock

from logger import setup_logging

logger = setup_logging("queue_manager")

class QueueManager:
	"""
	Manages the queue.json file and file copying for analysis.
	"""
	def __init__(self, shared_dir: str):
		"""
		Initialize the QueueManager with the shared directory path.
		"""
		self.shared_dir = os.path.abspath(os.path.expanduser(shared_dir))
		self.queue_dir = os.path.join(self.shared_dir, "queue")
		self.queue_file = os.path.join(self.queue_dir, "queue.json")
		self.lock_file = os.path.join(self.queue_dir, "queue.json.lock")
		self.files_dir = os.path.join(self.queue_dir, "files")
		os.makedirs(self.files_dir, exist_ok=True)

	def _calculate_sha256(self, file_path: str) -> str:
		"""
		Calculate the SHA256 hash of a file.
		"""
		try:
			sha256_hash = hashlib.sha256()
			with open(file_path, "rb") as f:
				for chunk in iter(lambda: f.read(4096), b""):
					sha256_hash.update(chunk)
			return sha256_hash.hexdigest()
		except Exception as e:
			logger.error(f"Failed to calculate SHA256 for {file_path}: {e}")
			raise

	def _load_queue(self) -> List[Dict[str, str]]:
		"""
		Load the queue.json file with file locking.
		"""
		with FileLock(self.lock_file):
			if not os.path.exists(self.queue_file):
				return []
			try:
				with open(self.queue_file, "r") as f:
					return json.load(f)
			except json.JSONDecodeError as e:
				logger.warning(f"Invalid queue.json, resetting: {e}")
				return []

	def _save_queue(self, queue_data: List[Dict[str, str]]):
		"""
		Save the queue data to queue.json with file locking.
		"""
		with FileLock(self.lock_file):
			try:
				with open(self.queue_file, "w") as f:
					json.dump(queue_data, f, indent=2)
			except Exception as e:
				logger.error(f"Failed to save queue.json: {e}")
				raise

	def _get_file_type(self, file_path: str) -> str:
		"""
		Determine the MIME type of a file using python-magic.
		"""
		try:
			return magic.from_file(file_path, mime=True)
		except Exception as e:
			logger.error(f"Failed to get file type for {file_path}: {e}")
			return "unknown"

	def add_file(self, file_path: str) -> bool:
		"""
		Add a file to the queue and copy it to shared_dir/queue/files/.
		"""
		try:
			file_path = os.path.abspath(file_path)
			if not os.path.isfile(file_path):
				logger.debug(f"File does not exist: {file_path}")
				return False

			sha256 = self._calculate_sha256(file_path)
			queue_data = self._load_queue()

			if any(entry["sha256"] == sha256 for entry in queue_data):
				logger.debug(f"Skipping duplicate file by SHA256: {file_path}")
				return False

			dest_path = os.path.join(self.files_dir, os.path.basename(file_path))
			shutil.copy2(file_path, dest_path)

			queue_entry = {
				"queue_id": sha256[:8],
				"original_path": file_path,
				"shared_path": dest_path,
				"sha256": sha256,
				"timestamp": datetime.utcnow().isoformat() + "Z",
				"event_type": "created",
				"file_type": self._get_file_type(file_path),
				"status": "pending"
			}

			queue_data.append(queue_entry)
			self._save_queue(queue_data)
			logger.info(f"[>] Queued file: {file_path} (SHA256: {sha256})")
			return True
		except Exception as e:
			logger.error(f"Failed to add file {file_path} to queue: {e}")
			return False

	def update_file(self, old_path: str, new_path: str) -> bool:
		"""
		Update a file's entry in queue.json after a rename/move and copy the new file.
		"""
		try:
			old_path = os.path.abspath(old_path)
			new_path = os.path.abspath(new_path)
			if not os.path.isfile(new_path):
				logger.debug(f"New file does not exist: {new_path}")
				return False

			sha256 = self._calculate_sha256(new_path)
			queue_data = self._load_queue()

			updated = False
			for entry in queue_data:
				if entry["original_path"] == old_path or entry["sha256"] == sha256:
					entry["original_path"] = new_path
					entry["shared_path"] = os.path.join(self.files_dir, os.path.basename(new_path))
					entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
					entry["event_type"] = "moved"
					entry["status"] = "pending"
					updated = True
					break

			if not updated:
				return self.add_file(new_path)

			shutil.copy2(new_path, entry["shared_path"])
			self._save_queue(queue_data)
			logger.info(f"[>] Updated file in queue: {old_path} -> {new_path} (SHA256: {sha256})")
			return True
		except Exception as e:
			logger.error(f"Failed to update file {old_path} -> {new_path}: {e}")
			return False

	def remove_file(self, file_path: str) -> bool:
		"""
		Remove a file's entry from queue.json.
		"""
		try:
			file_path = os.path.abspath(file_path)
			queue_data = self._load_queue()
			initial_len = len(queue_data)

			queue_data = [
				entry for entry in queue_data
				if not (entry["original_path"] == file_path or entry["shared_path"] == os.path.join(self.files_dir, os.path.basename(file_path)))
			]

			if len(queue_data) < initial_len:
				self._save_queue(queue_data)
				logger.info(f"[>] Removed file from queue: {file_path}")
				return True
			logger.debug(f"File not found in queue: {file_path}")
			return False
		except Exception as e:
			logger.error(f"Failed to remove file {file_path} from queue: {e}")
			return False
