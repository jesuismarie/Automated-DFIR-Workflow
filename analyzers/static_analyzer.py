import os
import re
import json
import time
import yara
import magic
import shutil
import pefile
import rarfile
import tarfile
import hashlib
import tempfile
import ipaddress
from typing import Dict, Any
from filelock import FileLock
from zipfile import ZipFile

from logger import setup_logging

QUEUE_PATH = "/analysis/input/queue.json"
LOCK_PATH = "/analysis/input/queue.json.lock"
RULES_DIR = "/analysis/rules/"
OUTPUT_DIR = "/analysis/static-output/"
PROCESSING_DIR = "/analysis/processed/"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSING_DIR, exist_ok=True)

logger = setup_logging("static_analyzer")

class StaticAnalyzer:
	def __init__(self):
		self.rules = self._compile_yara_rules()
		logger.info("Static analyzer initialized, YARA rules loaded")

	def _compile_yara_rules(self):
		"""
		Compile all .yar files in the rules directory recursively.
		"""
		rules = {}
		for root, _, files in os.walk(RULES_DIR):
			for file in files:
				if file.endswith('.yar'):
					filepath = os.path.join(root, file)
					try:
						rules[filepath] = yara.compile(filepath=filepath)
					except yara.SyntaxError as e:
						logger.warning(f"Syntax error in YARA rule {filepath}: {e}")
					except Exception as e:
						logger.error(f"Failed to compile YARA rule {filepath}: {e}")
		return rules

	def _get_file_type(self, file_path: str) -> str:
		"""
		Determine the MIME type of a file using python-magic.
		"""
		try:
			return magic.from_file(file_path, mime=True)
		except Exception as e:
			logger.error(f"Failed to get file type for {file_path}: {e}")
			return "unknown"

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

	def _is_valid_ip(self, ip_str: str) -> bool:
		"""
		Validate if a string is a valid IPv4 address.
		"""
		try:
			ip = ipaddress.ip_address(ip_str)
			return isinstance(ip, ipaddress.IPv4Address) and not ip.is_private and not ip.is_loopback
		except ValueError:
			return False

	def analyze_file(self, file_path: str, sha256: str, depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
		"""
		Analyze a file, handling archives recursively and applying YARA and PE analysis.
		"""
		if depth > max_depth:
			logger.warning(f"Max recursion depth reached for {file_path}")
			return {"status": "failed", "error": "Max recursion depth exceeded"}

		try:
			results = {
				"analysis_id": f"static_{sha256[:8]}",
				"file_info": {
					"sha256": sha256,
					"original_path": file_path,
					"file_type": self._get_file_type(file_path),
					"size_bytes": os.path.getsize(file_path)
				},
				"results": {
					"yara_matches": [],
					"pe_analysis": {},
					"extracted_iocs": {},
					"sub_files": []
				},
				"risk_assessment": {
					"risk_score": 0,
					"risk_level": "LOW",
					"threat_classification": "UNKNOWN",
					"recommendation": "MONITOR"
				},
				"status": "analyzed",
				"tools_used": ["yara", "pefile"],
				"duration_ms": 0
			}

			start_time = time.time()

			temp_dir = None
			file_type = results["file_info"]["file_type"]
			if file_type in ["application/zip", "application/x-zip-compressed", "application/x-rar-compressed", "application/x-tar", "application/gzip", "application/x-bzip2"]:
				temp_dir = tempfile.mkdtemp(prefix="static_analysis_")
				try:
					if file_type in ["application/zip", "application/x-zip-compressed"]:
						with ZipFile(file_path, 'r') as z:
							z.extractall(temp_dir)
					elif file_type == "application/x-rar-compressed":
						with rarfile.RarFile(file_path, 'r') as r:
							r.extractall(temp_dir)
					elif file_type in ["application/x-tar", "application/gzip", "application/x-bzip2"]:
						with tarfile.open(file_path, 'r:*') as t:
							t.extractall(temp_dir)

					extracted_files = [os.path.join(root, f) for root, _, files in os.walk(temp_dir) for f in files]
					if len(extracted_files) > 100:
						raise ValueError("Too many files in archive (>100)")

					for sub_file_path in extracted_files:
						sub_sha256 = self._calculate_sha256(sub_file_path)
						sub_results = self.analyze_file(sub_file_path, sub_sha256, depth + 1, max_depth)
						results["results"]["sub_files"].append(sub_results)
						results["risk_assessment"]["risk_score"] = max(
							results["risk_assessment"]["risk_score"],
							sub_results["risk_assessment"]["risk_score"]
						)
						results["results"]["yara_matches"].extend(sub_results["results"]["yara_matches"])
						for key in sub_results["results"]["extracted_iocs"]:
							if key not in results["results"]["extracted_iocs"]:
								results["results"]["extracted_iocs"][key] = []
							results["results"]["extracted_iocs"][key].extend(sub_results["results"]["extracted_iocs"][key])
				except Exception as e:
					logger.error(f"Failed to process archive {file_path}: {e}")
					results["status"] = "failed"
					results["error"] = f"Archive processing failed: {str(e)}"
				finally:
					if temp_dir:
						shutil.rmtree(temp_dir, ignore_errors=True)

			else:
				# YARA scan
				yara_matches = []
				for rule_filepath, rule_set in self.rules.items():
					try:
						matches = rule_set.match(file_path)
						yara_matches.extend([
							{
								"rule_name": m.rule,
								"severity": "HIGH" if "malware" in m.rule.lower() else "MEDIUM",
								"matched_strings": [str(s) for s in m.strings],
								"source_rule": rule_filepath
							} for m in matches
						])
					except Exception as e:
						logger.warning(f"YARA scan failed for {file_path} with rule {rule_filepath}: {e}")
				results["results"]["yara_matches"] = yara_matches
				if yara_matches:
					results["risk_assessment"]["risk_score"] += 50

				# PEfile analysis
				try:
					pe = pefile.PE(file_path)
					pe_analysis = {
						"suspicious_imports": [
							imp.name.decode('utf-8', errors='ignore') if imp.name else ""
							for dll in pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']].imports
							for imp in dll.imports
							if imp.name and (b'VirtualAlloc' in imp.name or b'CreateRemoteThread' in imp.name)
						],
						"high_entropy_sections": [
							sec.Name.decode('utf-8', errors='ignore').strip() for sec in pe.sections if sec.get_entropy() > 6.5
						],
						"overlay_detected": len(pe.get_overlay()) > 0,
						"is_packed": any(pe.sections[i].SizeOfRawData == 0 for i in range(len(pe.sections)))
					}
					results["results"]["pe_analysis"] = pe_analysis
					if pe_analysis["suspicious_imports"] or pe_analysis["high_entropy_sections"] or pe_analysis["is_packed"]:
						results["risk_assessment"]["risk_score"] += 35
				except pefile.PEFormatError:
					print(f"Not a PE file: {file_path}")

				# IOC extraction
				try:
					with open(file_path, "rb") as f:
						content = f.read()
					iocs = {
						"urls": [u.decode('utf-8', errors='ignore') for u in re.findall(
							b"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", content
						)],
						"ips": [i.decode('utf-8') for i in re.findall(
							b"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", content
						) if self._is_valid_ip(i.decode('utf-8'))]
					}
					results["results"]["extracted_iocs"] = iocs
					if iocs["urls"] or iocs["ips"]:
						results["risk_assessment"]["risk_score"] += 15
				except Exception as e:
					logger.warning(f"IOC extraction failed for {file_path}: {e}")

				# Calculate risk level
				score = results["risk_assessment"]["risk_score"]
				if score > 70:
					results["risk_assessment"]["risk_level"] = "HIGH"
					results["risk_assessment"]["recommendation"] = "QUARANTINE"
				elif score > 40:
					results["risk_assessment"]["risk_level"] = "MEDIUM"

			results["duration_ms"] = int((time.time() - start_time) * 1000)
			return results
		except Exception as e:
			logger.error(f"Analysis failed for {file_path}: {e}")
			return {
				"analysis_id": f"static_{sha256[:8]}",
				"file_info": {"sha256": sha256, "original_path": file_path},
				"status": "failed",
				"error": str(e)
			}

	def run(self):
		"""
		Poll queue.json and analyze pending files.
		"""
		while True:
			with FileLock(LOCK_PATH):
				try:
					with open(QUEUE_PATH, "r") as f:
						queue = json.load(f)
				except json.JSONDecodeError:
					logger.warning("Invalid queue.json, skipping")
					queue = []

				for entry in queue:
					if entry.get("status", "pending") == "pending":
						entry["status"] = "analyzing"
						with open(QUEUE_PATH, "w") as f:
							json.dump(queue, f, indent=2)

						file_basename = os.path.basename(entry["shared_path"])
						file_path = os.path.join("/analysis/input/files", file_basename)

						processing_path = os.path.join(PROCESSING_DIR, file_basename)
						try:
							shutil.move(file_path, processing_path)
							logger.info(f"Moved file to processing: {processing_path}")
						except Exception as e:
							logger.error(f"Failed to move file to processing: {file_path}: {e}")
							entry["status"] = "failed"
							entry["error"] = str(e)
							with open(QUEUE_PATH, "w") as f:
								json.dump(queue, f, indent=2)
							continue

						results = self.analyze_file(processing_path, entry["sha256"])
						output_path = os.path.join(OUTPUT_DIR, f"{entry['sha256']}.json")
						with open(output_path, "w") as f:
							json.dump(results, f, indent=2)

						entry["status"] = results["status"]
						entry["static_output_path"] = output_path
						with open(QUEUE_PATH, "w") as f:
							json.dump(queue, f, indent=2)

						logger.info(f"Analyzed file: {entry['original_path']} (Output: {output_path})")

			time.sleep(10)

if __name__ == "__main__":
	analyzer = StaticAnalyzer()
	analyzer.run()
