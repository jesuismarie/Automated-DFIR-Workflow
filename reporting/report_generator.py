import os
import json
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from filelock import FileLock

from logger import setup_logging

HOME_DIR = os.path.expanduser("~/malware-analysis")
QUEUE_DIR = os.path.join(HOME_DIR, "queue")
QUEUE_PATH = os.path.join(QUEUE_DIR, "queue.json")
QUEUE_LOCK = os.path.join(QUEUE_DIR, "queue.json.lock")
REPORTS_DIR = os.path.join(HOME_DIR, "reports")
STATIC_OUT_DIR = os.path.join(HOME_DIR, "static-output")
DYNAMIC_OUT_DIR = os.path.join(HOME_DIR, "dynamic-output")

os.makedirs(REPORTS_DIR, exist_ok=True)

logger = setup_logging("report_generator")

def host_path(container_path: str) -> str:
	"""
	Convert a path that starts with '/analysis' (as seen inside the container)
	into the corresponding host path under ~/malware-analysis.
	"""
	if not container_path:
		return ""
	container_path = os.path.normpath(container_path)
	if container_path.startswith("/analysis"):
		rel_path = container_path[len("/analysis"):]
		return os.path.join(HOME_DIR, rel_path.lstrip("/"))
	return container_path

def load_json(path: str) -> Optional[Dict[Any, Any]]:
	"""Safely load a JSON file; return None on error."""
	if not os.path.isfile(path):
		return None
	try:
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception as e:
		logger.error(f"[!] Failed to load {path}: {e}")
		return None

def save_json(data: Dict, path: str) -> None:
	"""Write JSON with pretty formatting."""
	try:
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2, sort_keys=True)
	except Exception as e:
		logger.error(f"[!] Failed to write {path}: {e}")

def save_markdown(content: str, path: str) -> None:
	try:
		with open(path, "w", encoding="utf-8") as f:
			f.write(content)
	except Exception as e:
		logger.error(f"[!] Failed to write Markdown {path}: {e}")

def generate_markdown(report: Dict) -> str:
	md = f"# Malware Analysis Report\n\n"
	md += f"**Report ID**: `{report['report_id']}`  \n"
	md += f"**Generated**: {report['generated_at']}\n\n"
	md += f"---\n\n"

	info = report["file_info"]
	md += f"## File Information\n\n"
	md += f"- **Original Path**: `{info['original_path']}`\n"
	md += f"- **SHA256**: `{info['sha256']}`\n"
	md += f"- **Event**: `{info.get('event_type', 'unknown')}`\n"
	md += f"- **Timestamp**: `{info.get('timestamp', 'N/A')}`\n\n"

	file_type = info.get("file_type")
	size_bytes = info.get("size_bytes")
	if file_type:
		md += f"- **File Type**: `{file_type}`\n"
	if size_bytes is not None:
		md += f"- **Size**: `{size_bytes}` bytes\n"
	md += "\n"

	risk = report["overall_risk"]
	level = risk["level"]
	score = risk["score"]
	badge_color = {
		"CRITICAL": "red",
		"HIGH": "orange",
		"MEDIUM": "yellow",
		"LOW": "green",
		"INFO": "blue"
	}.get(level, "gray")
	md += f"## Overall Risk\n\n"
	md += f"![Risk](https://img.shields.io/badge/Risk-{level}-{badge_color}?style=for-the-badge) **Score: {score}**\n\n"

	static = report.get("static_analysis")
	if static:
		md += f"## Static Analysis\n\n"
		md += f"- **Risk Score**: `{static.get('risk_score', 0)}`\n\n"

		yara = static.get("yara_matches", [])
		if yara:
			md += f"### YARA Rule Matches\n\n"
			md += f"| Rule | Description |\n"
			md += f"|------|-------------|\n"
			for match in yara:
				md += f"| `{match.get('rule', 'unknown')}` | {match.get('description', 'N/A')} |\n"
			md += f"\n"

		strings = static.get("interesting_strings", [])
		if strings:
			md += f"### Suspicious Strings\n\n"
			md += "```\n"
			for s in strings[:10]:  # limit
				md += f"{s}\n"
			if len(strings) > 10:
				md += f"... ({len(strings) - 10} more)\n"
			md += "```\n\n"

	else:
		md += f"## Static Analysis\n\n*No static analysis available.*\n\n"

	return md

def build_report(entry: Dict) -> Dict[str, Any]:
	"""Merge static results into a final report."""
	sha256 = entry["sha256"]
	report: Dict[str, Any] = {
		"report_id": f"report-{sha256}",
		"generated_at": datetime.now(UTC).isoformat(),
		"file_info": {
			"original_path": entry.get("original_path"),
			"sha256": sha256,
			"timestamp": entry.get("timestamp"),
			"event_type": entry.get("event_type"),
			"file_type": None,
			"size_bytes": None
		},
		"static_analysis": None,
		"overall_risk": {
			"score": 0,
			"level": "UNKNOWN"
		}
	}

	static_path = entry.get("static_output_path")
	if static_path:
		host_static = host_path(static_path)
		static_data = load_json(host_static)
		if static_data:
			report["static_analysis"] = static_data
			static_file_info = static_data.get("file_info", {})
			report["file_info"]["file_type"] = static_file_info.get("file_type")
			report["file_info"]["size_bytes"] = static_file_info.get("size_bytes")
			report["overall_risk"]["score"] += static_data.get("risk_score", 0)

	total = report["overall_risk"]["score"]
	if total >= 140:
		level = "CRITICAL"
	elif total >= 100:
		level = "HIGH"
	elif total >= 60:
		level = "MEDIUM"
	elif total >= 30:
		level = "LOW"
	else:
		level = "INFO"
	report["overall_risk"]["level"] = level

	return report

def run_reporter() -> None:
	logger.info("[*] Report generator started - watching queue.json")
	while True:
		try:
			with FileLock(QUEUE_LOCK, timeout=5):
				if not os.path.exists(QUEUE_PATH):
					time.sleep(10)
					continue
				with open(QUEUE_PATH, "r", encoding="utf-8") as f:
					queue = json.load(f)
		except Exception as e:
			logger.error(f"[!] Queue lock/error: {e}")
			time.sleep(10)
			continue

		changed = False
		for entry in queue:
			if entry.get("status") != "analyzed":
				continue

			if entry.get("report_path"):
				continue

			report_data = build_report(entry)
			sha256 = entry["sha256"]
			json_file = os.path.join(REPORTS_DIR, f"report-{sha256}.json")
			md_file = os.path.join(REPORTS_DIR, f"report-{sha256}.md")

			save_json(report_data, json_file)
			save_markdown(generate_markdown(report_data), md_file)

			entry["report_path"] = json_file
			entry["report_md_path"] = md_file
			entry["status"] = "reported"
			changed = True
			logger.info(f"[+] Reports generated: {os.path.basename(json_file)}, {os.path.basename(md_file)}")

		if changed:
			try:
				with FileLock(QUEUE_LOCK, timeout=5):
					with open(QUEUE_PATH, "w", encoding="utf-8") as f:
						json.dump(queue, f, indent=2)
			except Exception as e:
				logger.warning(f"[!] Failed to update queue: {e}")

		time.sleep(10)
