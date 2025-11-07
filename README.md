# Automated Malware Analysis & Security Reporting Workflow

## Project Overview

The **Automated Malware Analysis Workflow** is a modular, fully automated system for **detecting, analyzing, and reporting** on suspicious files in real time.
It continuously monitors specified directories, safely analyzes files inside a **hardened Docker sandbox**, and generates **comprehensive reports** — all without manual intervention.

Designed for cybersecurity research and malware forensics, this workflow ensures **secure, reproducible, and isolated analysis** with full traceability.

## Capabilities

* **Continuous Monitoring** — Real-time directory watch powered by `watchdog`.
* **Isolated Sandbox** — Containerized static analysis using a non-root, network-less Docker environment.
* **Static Analysis Engine** — YARA scanning, string and IOC extraction.
* **Centralized Queue System** — Files tracked and processed through `queue.json` with file locking.
* **Automated Reporting** — Generates structured JSON and human-readable Markdown reports with risk scoring.
* **Zero Manual Setup** — Fully configured via `Makefile` and `config.json` on first run.
* **Auditable Logging** — Detailed logs for all workflow stages, from detection to reporting.

## Getting Started

### Prerequisites

Ensure the following are installed on your system:

* **Python 3.10+**
* **Docker** & **Docker Compose**
* **Make**

### Installation

Clone the repository and build the environment:

```bash
git clone https://github.com/jesuismarie/Automated-Malware-Analysis-Workflow
cd Automated-Malware-Analysis-Workflow
make venv
make setup        # Configure monitored directory, file types, and shared directory
make run
```

If you want to use the default configuration, you can simply run:

```bash
git clone https://github.com/jesuismarie/Automated-Malware-Analysis-Workflow
cd Automated-Malware-Analysis-Workflow
make
```

This will:

* Create a virtual environment.
* Install all Python dependencies.
* Generate a default `config.json`.
* Create directories for logs, reports, queue, and output.

## Usage

You can launch individual phases or the full workflow via `make`:

| Command           | Description                                          |
| ----------------- | ---------------------------------------------------- |
| `make help`       | Show help message.                                   |
| `make venv`       | Create virtual environment and install dependencies. |
| `make config`     | Generate default `config.json` if missing.           |
| `make setup`      | Set up directories and configurations.               |
| `make run`        | Execute full workflow (monitor → analyze → report).  |
| `make sandbox-up` | Build and run the Docker sandbox.                    |
| `make clean`      | Remove temporary files (keep venv).                  |
| `make clean-all`  | Full cleanup including venv.                         |

## Configuration

The system is configured using `config.json`, automatically generated on first launch.

**Example:**

```json
{
	"monitoring": {
		"watch_directory": "/home/user/Downloads",
		"recursive": true,
		"file_types": ["*"],
		"shared_directory": "/home/user/malware-analysis"
	}
}
```

### Editable Parameters

| Key                | Description                                   |
| ------------------ | --------------------------------------------- |
| `watch_directory`  | Directory to monitor for new files.           |
| `file_types`       | Filter file types (e.g., `[".exe", ".pdf"]`). |
| `recursive`        | Monitor subdirectories if `true`.             |
| `shared_directory` | Location of shared folder for sandbox I/O.    |

## Workflow Phases

### **Phase 1 – File Monitoring**

* Detects file system changes in the watched directory.
* Filters temporary/incomplete downloads.
* Computes SHA-256 and stores file metadata in `queue.json`.
* Copies files safely into `shared/queue/`.

### **Phase 2 – Static Analysis**

* Performed inside Docker with `network_mode: none` and `cap_drop: ALL`.
* Analyzes files using:

  * **YARA rules** for pattern matching.
  * **File type detection** with `magic`.
  * **IOC extraction** (URLs, IPs, registry keys).
* Outputs JSON results with risk assessment.

### **Phase 3 – Reporting**

* Collects analyzed results.
* Merges data into human-readable Markdown and structured JSON reports.
* Assigns risk levels (Low/Medium/High) with recommendations.
* Updates `queue.json` status to `reported`.

## Logs

Logs are stored both on the host and in the container for debugging and auditing.

| Level   | Purpose                   |
| ------- | ------------------------- |
| INFO    | Normal operations         |
| DEBUG   | Detailed debugging output |
| WARNING | Non-critical issues       |
| ERROR   | Component failures        |

**Locations:**

* Host: `~/malware-analysis/logs/`
* Container: `/analysis/logs/`

## Project Structure

```
Automated-Malware-Analysis-Workflow/
├── analyzers
│	└── static_analyzer.py
├── constants.py
├── docker-compose.yml
├── LICENSE
├── logger.py
├── Makefile
├── monitoring
│	├── config.py
│	├── file_watcher.py
│	├── queue_manager.py
│	└── utils.py
├── reporting
│	└── report_generator.py
├── requirements.txt
└── sandbox
	├── Dockerfile
	├── entrypoint.sh
	└── requirements.txt
```

## Future Improvements

Planned features include:

* **Dynamic Analysis Sandbox** — Safe runtime behavior observation.
* **Web Dashboard** — Real-time visualization of analysis metrics.
* **Machine Learning Integration** — Behavioral anomaly detection.
* **Automatic Quarantine & Alerts** — Block C2 domains and send alerts via email/Slack.

## Dependencies

Main Python libraries:

* `watchdog` – Filesystem monitoring
* `filelock` – Safe file access
* `yara-python` – Malware pattern matching
* `python-magic` – File type detection
* `markdown` – Report rendering

## Contributing

Contributions, issues, and feature requests are welcome!
Fork the repo, create a branch, and submit a pull request.

```bash
git checkout -b feature/new-analyzer
git commit -m "Add new static analyzer module"
git push origin feature/new-analyzer
```

## License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.
