import os
import sys
import json
from typing import Dict, Any

from logger import setup_logging

logger = setup_logging("config_loader")

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
		logger.error(f"❌ Invalid or missing config: {e}")
		sys.exit(1)

	watch_dir = monitoring_config.get('watch_directory')
	shared_dir = monitoring_config.get('shared_directory')
	file_types = monitoring_config.get('file_types')

	if not watch_dir:
		logger.error("watch_directory not set in config")
		sys.exit(1)
	if not shared_dir:
		logger.error("shared_directory not set in config")
		sys.exit(1)
	if not file_types:
		logger.error("file_types not set in config, defaulting to all files")
		file_types = ['*']

	watch_dir = os.path.expanduser(watch_dir)
	shared_dir = os.path.expanduser(shared_dir)

	monitoring_config['watch_directory'] = watch_dir
	monitoring_config['shared_directory'] = shared_dir
	monitoring_config['file_types'] = file_types

	logger.info(f"Config loaded - Watch: {watch_dir}")
	logger.info(f"Shared: {shared_dir}")
	logger.info(f"File Types: {file_types}")
	return monitoring_config
