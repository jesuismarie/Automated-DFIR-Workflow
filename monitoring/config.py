import os
import sys
import json
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
	"""
	Load configuration from config/config.json and normalize keys.
	"""
	config_path = os.path.join("config", "config.json")

	try:
		with open(config_path, 'r') as f:
			config = json.load(f)
		monitoring_config = config.get('monitoring', {})
	except (json.JSONDecodeError, FileNotFoundError) as e:
		print(f"❌ Invalid or missing config: {e}")
		sys.exit(1)

	watch_dir = monitoring_config.get('watch_directory')
	shared_dir = monitoring_config.get('shared_directory')

	if not watch_dir:
		print("watch_directory not set in config")
		sys.exit(1)
	if not shared_dir:
		print("shared_directory not set in config")
		sys.exit(1)

	watch_dir = os.path.expanduser(watch_dir)
	shared_dir = os.path.expanduser(shared_dir)

	monitoring_config['watch_directory'] = watch_dir
	monitoring_config['shared_directory'] = shared_dir

	print(f"Config loaded - Watch: {watch_dir}")
	print(f"Shared: {shared_dir}")
	return monitoring_config
