################################################################################
# Variables
################################################################################

VENV		:= .venv
PYTHON		:= $(VENV)/bin/python
PIP			:= $(VENV)/bin/pip

# Set a directory to monitor (By default Downloads directory)
DIR			?= ~/Downloads
SCRIPT		?= file_watcher.py

RESET		= \033[0m
BLUE		= \033[34m
MAGENTA		= \033[35m
YELLOW		= \033[38;2;255;239;0m
APPLE_GREEN	= \033[38;2;141;182;0m

################################################################################
# Main Targets
################################################################################

all: run

help:
	@echo "${MAGENTA}------------------------------------------------------------------------------------${RESET}"
	@echo "${MAGENTA}|Available commands:                                                               |${RESET}"
	@echo "${MAGENTA}------------------------------------------------------------------------------------${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make help${RESET}    : Show this help message.                                           ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make venv${RESET}    : Create the virtual environment and install dependencies.          ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make run${RESET}     : Check venv, then start the file watcher on $(DIR).           ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make watch${RESET}   : Same as 'run'.                                                    ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make analyze${RESET} : Check venv, then run the analyzer script on $(DIR).          ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make report${RESET}  : Check venv, then generate a report for $(DIR).               ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}|${RESET} ${YELLOW}make clean${RESET}   : Remove the virtual environment (${VENV}) and other generated files. ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}------------------------------------------------------------------------------------${RESET}"
	@echo ""
	@echo "${MAGENTA}To change the target directory, use: make run DIR=/path/to/folder${RESET}"
	@echo ""

################################################################################
# Virtual Environment
################################################################################

venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	@echo "${BLUE}🔧 Creating virtual environment...${RESET}"
	@python3 -m venv $(VENV)
	@echo "${BLUE}⬆️  Upgrading pip...${RESET}"
	@$(PIP) install --upgrade pip
	@echo "${APPLE_GREEN}📦 Installing dependencies from requirements.txt...${RESET}"
	@$(PIP) install -r requirements.txt
	@echo "${APPLE_GREEN}✅ Virtual environment ready!${RESET}"

################################################################################
# Running Scripts
################################################################################

run: check-venv
	@echo "${YELLOW}▶️  Starting Automated File Watcher on $(DIR)...${RESET}"
	@$(PYTHON) $(SCRIPT) $(DIR)

watch: check-venv
	@$(PYTHON) file_watcher.py $(DIR)

analyze: check-venv
	@$(PYTHON) analyzer.py $(DIR)

report: check-venv
	@$(PYTHON) report_generator.py $(DIR)

################################################################################
# Utility
################################################################################

check-venv:
	@test -d $(VENV) || (echo "${YELLOW}⚠️  Virtual environment not found. Run 'make venv' first.${RESET}"; exit 1)

clean:
	@echo "${BLUE}🧹 Cleaning up project files...${RESET}"
	@rm -rf __pycache__ $(VENV) *.pyc *.json *.md *.log
	@echo "${YELLOW}✨ Everything is clean ✅${RESET}"

.PHONY: all venv run watch analyze report clean check-venv
