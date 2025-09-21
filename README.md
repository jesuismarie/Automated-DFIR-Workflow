# Automated File Analysis & Security Reporting System

## Project Overview

This project builds an **automated desktop security application** that continuously monitors downloaded files, performs **digital forensics and malware analysis**, and generates **clear, actionable security reports**.

It is designed for **personal security**, enabling everyday users to proactively assess potential threats without requiring expert knowledge.

## How It Works

1. **File Ingestion**

	* A file system watcher monitors the **Downloads** folder (or directory you provide).
	* New files are automatically passed into the sandbox for analysis.

2. **Static Analysis**

	* Uses **YARA** rules for known malware signatures.
	* Inspects PE headers with **PEfile** to detect anomalies (entropy, imports, packing).

3. **Dynamic Analysis**

	* Runs the file in an **isolated sandbox VM** (VirtualBox/REMnux).
	* Logs API calls, file system changes, registry edits, and network connections.

4. **Manual Analysis Integration**

	* Suspicious files trigger a **manual review flag**.
	* User can investigate further using a CLI or lightweight GUI.

5. **Reporting**

	* Combines static & dynamic results.
	* Generates structured **Markdown/HTML reports**.
	* Stores reports locally for review.

## Key Technologies

* **Automation**: Python `watchdog`
* **Static Analysis**: YARA, PEfile
* **Dynamic Analysis**: VirtualBox, REMnux, Wireshark/tcpdump
* **Digital Forensics**: Procmon, sandbox logging
* **Reporting**: Markdown, HTML, Jinja2
* **UI**: CLI (`click`) or basic GUI (`Tkinter`)
