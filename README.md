# Automated File Analysis & Security Reporting System

## Project Overview

This project builds an **automated desktop security application** that continuously monitors files, analyze, and generates **clear, actionable security reports**.

It is designed for **personal security**, enabling everyday users to proactively assess potential threats without requiring expert knowledge.

## How It Works

1. **File Ingestion**

	* A file system watcher monitors the **Downloads** folder (or directory you provide).
	* New files are automatically passed into the sandbox for analysis.

2. **Static Analysis**

	* Uses **YARA** rules for known malware signatures.
	* Inspects PE headers with **PEfile** to detect anomalies (entropy, imports, packing).

3. **Reporting**

	* Generates structured **Markdown reports**.
	* Stores reports locally for review.

## Key Technologies

* **Automation**: Python `watchdog`
* **Static Analysis**: YARA, PEfile
* **Reporting**: Markdown
