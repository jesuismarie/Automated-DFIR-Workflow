import os
import time
import zipfile
import tarfile
import subprocess
import shutil
try:
	import patoolib
except ImportError:
	patoolib = None

from constants import UNPACK_ROOT_DIR, MAX_FILES_TO_EXTRACT

def get_next_analysis_path(original_path):
	"""
	Creates a unique, isolated subdirectory inside UNPACK_ROOT_DIR
	for processing the contents of a single file/archive.
	"""
	if not os.path.isdir(UNPACK_ROOT_DIR):
		os.makedirs(UNPACK_ROOT_DIR)

	filename_base = os.path.splitext(os.path.basename(original_path))[0]
	timestamp_ms = int(time.time() * 1000)
	target_dir = os.path.join(UNPACK_ROOT_DIR, f"{filename_base}_{timestamp_ms}")
	os.makedirs(target_dir, exist_ok=False)
	return target_dir

def unpack_archive(archive_path):
	"""
	Safely extracts files from an archive into an isolated directory.
	"""
	_, ext = os.path.splitext(archive_path)
	ext = ext.lower()

	# Target directory setup
	target_dir = None
	try:
		target_dir = get_next_analysis_path(archive_path)
	except FileExistsError:
		print(f"  [!] Extraction directory collision. Skipping extraction.")
		return None
	except Exception as e:
		print(f"  [!] Failed to create unique directory: {e}")
		return None

	print(f"  -> Extracting contents to isolated directory: {target_dir}")

	try:
		_, ext = os.path.splitext(archive_path)
		ext = ext.lower()

		def _is_within_directory(directory, target):
			abs_directory = os.path.abspath(directory)
			abs_target = os.path.abspath(target)
			return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

		def _safe_extract_zip(zf: zipfile.ZipFile, path: str):
			for member in zf.namelist():
				member_path = os.path.join(path, member)
				if not _is_within_directory(path, member_path):
					raise ValueError("Zip-Slip attempt detected")
			zf.extractall(path)

		if ext == '.zip':
			with zipfile.ZipFile(archive_path, 'r') as zf:
				names = zf.namelist()
				num_files = len(names)
				if num_files > MAX_FILES_TO_EXTRACT:
					raise ValueError(f"Too many files in archive ({num_files})")
				_safe_extract_zip(zf, target_dir)
				print(f"  [+] Successfully extracted {num_files} files.")

		elif ext in ('.tar', '.gz', '.bz2', '.tgz'):
			with tarfile.open(archive_path, 'r:*') as tf:
				members = tf.getmembers()
				num_files = len(members)
				if num_files > MAX_FILES_TO_EXTRACT:
					raise ValueError(f"Too many files in archive ({num_files})")
				# Check for path traversal
				for m in members:
					member_path = os.path.join(target_dir, m.name)
					if not _is_within_directory(target_dir, member_path):
						raise ValueError("Tar-Slip attempt detected")
				tf.extractall(target_dir)
				print(f"  [+] Successfully extracted {num_files} members.")

		elif ext in ('.rar', '.7z'):
			# Try patool if available, otherwise try system '7z' or 'unrar' commands
			if patoolib is not None:
				patoolib.extract_archive(archive_path, outdir=target_dir, verbosity=-1)
				file_count = sum(len(files) for _, _, files in os.walk(target_dir))
				if file_count > MAX_FILES_TO_EXTRACT:
					raise ValueError(f"File count limit exceeded post-extraction ({file_count}).")
				print(f"  [+] Successfully extracted contents (Approx. {file_count} files).")
			else:
				# Attempt to use system 7z if present
				for cmd in (['7z', 'x', '-y', f'-o{target_dir}', archive_path], ['unrar', 'x', '-o+', archive_path, target_dir]):
					try:
						subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
						file_count = sum(len(files) for _, _, files in os.walk(target_dir))
						if file_count > MAX_FILES_TO_EXTRACT:
							raise ValueError(f"File count limit exceeded post-extraction ({file_count}).")
						print(f"  [+] Successfully extracted contents (Approx. {file_count} files).")
						break
					except Exception:
						# try next command
						shutil.rmtree(target_dir, ignore_errors=True)
						os.makedirs(target_dir, exist_ok=True)
				else:
					raise RuntimeError("No extractor available for rar/7z archives")

		else:
			print(f"  [!] Unsupported or unknown archive extension '{ext}'. Skipping.")
			return None

		file_count = sum(len(files) for _, _, files in os.walk(target_dir))
		if file_count > MAX_FILES_TO_EXTRACT:
			raise ValueError(f"File count limit exceeded post-extraction ({file_count}).")

		should_cleanup = False
		return target_dir

	except (zipfile.BadZipFile, tarfile.ReadError, ValueError) as e:
		print(f"  [!] Failed to unpack archive or security check failed: {e}")
	except Exception as e:
		print(f"  [!] An unexpected error occurred during unpacking: {e}")
	finally:
		# Cleanup runs if any failure occurred (should_cleanup is True) or if the directory is empty.
		if should_cleanup and target_dir and os.path.isdir(target_dir):
			shutil.rmtree(target_dir, ignore_errors=True)
			print(f"  [CLEANUP] Removed extraction directory: {target_dir}")
		elif target_dir and os.path.isdir(target_dir) and not os.listdir(target_dir):
			shutil.rmtree(target_dir, ignore_errors=True)
			print(f"  [CLEANUP] Removed empty directory: {target_dir}")
	return None
