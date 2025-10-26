################################################################################
# Variables
################################################################################

MAKEFLAGS		+= --no-print-directory

VENV			:= .venv
PYTHON			:= $(VENV)/bin/python3
PIP				:= $(VENV)/bin/pip
DOCKER_COMPOSE	:= docker-compose
MKDIR			:= mkdir -p
TOUCH			:= touch
CHOWN			:= chown

CONFIG_FILE		:= config/config.json
SHARED_DIR		:= $(HOME)/malware-analysis
QUEUE_FILE		:= $(SHARED_DIR)/queue/queue.json
REQUIREMENTS	:= requirements.txt
MONITORED_DIR	:= $(shell $(PYTHON) -c "import json, os; config=json.load(open('$(CONFIG_FILE)', 'r')); path=os.path.expanduser(config.get('monitoring', {}).get('watch_directory', '~/Downloads')); print(path)" 2>/dev/null || echo "$$HOME/Downloads")

# Colors for output
RESET		= \033[0m
BLUE		= \033[34m
MAGENTA		= \033[35m
YELLOW		= \033[38;2;255;239;0m
APPLE_GREEN	= \033[38;2;141;182;0m

################################################################################
# Main Targets
################################################################################

all: venv setup run

help:
	@echo "${MAGENTA}================================================================================${RESET}"
	@echo "${MAGENTA}| Automated Malware Analysis Workflow Commands                                 |${RESET}"
	@echo "${MAGENTA}================================================================================${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make help${RESET}         : Show this help message.                                  ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make venv${RESET}         : Create virtual environment and install dependencies.     ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make config${RESET}       : Create default config file if missing.                   ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make setup${RESET}        : Setup shared directories and configuration.              ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make run${RESET}          : Run full workflow (monitor → analyze → report).          ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make monitor${RESET}      : Run only monitoring phase.                               ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make report${RESET}       : Generate analysis reports and alerts.                    ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make clean${RESET}        : Remove generated files (keep venv).                      ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}| ${YELLOW}make clean-all${RESET}    : Full cleanup (remove venv and all generated data).       ${MAGENTA}|${RESET}"
	@echo "${MAGENTA}================================================================================${RESET}"
	@echo ""
	@echo "${MAGENTA}Configuration: Reads from ${YELLOW}config/config.json${RESET}"
	@echo "${YELLOW}• Monitored directory:${RESET} ${MONITORED_DIR}"
	@echo "${YELLOW}• Shared directory:   ${RESET} ${SHARED_DIR}"
	@echo ""

################################################################################
# Setup and Configuration
################################################################################

setup: check-venv config setup-shared

config: check-venv
	@echo "${BLUE}Setting up configuration...${RESET}"
	@$(MKDIR) config
	@if [ ! -f "$(CONFIG_FILE)" ]; then \
		echo "${YELLOW}⚠️  Config file not found, creating default...${RESET}"; \
		$(PYTHON) -c "import json, os; config = { \
			'monitoring': { \
				'watch_directory': os.path.expanduser('~/Downloads'), \
				'recursive': True, \
				'file_types': ['*'], \
				'shared_directory': os.path.expanduser('~/malware-analysis'), \
			} \
		}; json.dump(config, open('$(CONFIG_FILE)', 'w'), indent=2)"; \
	fi
	@cat $(CONFIG_FILE)
	@echo ""

check-config:
	@if [ ! -f "$(CONFIG_FILE)" ]; then \
		echo "${YELLOW}⚠️  Config file not found. Run 'make setup' first.${RESET}"; \
		exit 1; \
	fi

setup-shared:
	@echo "${BLUE}Setting up shared directories: $(SHARED_DIR)${RESET}"
	@$(MKDIR) "$(SHARED_DIR)/queue/files"
	@$(MKDIR) "$(SHARED_DIR)/static-output"
	@$(MKDIR) "$(SHARED_DIR)/reports"
	@$(MKDIR) "$(SHARED_DIR)/logs"
	@$(TOUCH) "$(QUEUE_FILE)"
	@echo "[]" > "$(QUEUE_FILE)"
	@$(CHOWN) 1000:1000 -R "$(SHARED_DIR)"
	@chmod 755 "$(SHARED_DIR)"
	@chmod -R 755 "$(SHARED_DIR)/queue" "$(SHARED_DIR)/static-output" "$(SHARED_DIR)/reports" "$(SHARED_DIR)/logs"
	@chmod 644 "$(QUEUE_FILE)"
	@echo "${APPLE_GREEN}✅ Shared directories ready at: $(SHARED_DIR)${RESET}"

################################################################################
# Virtual Environment
################################################################################

venv: $(VENV)/bin/activate

$(VENV)/bin/activate: $(REQUIREMENTS)
	@echo "${BLUE}🔧 Creating virtual environment...${RESET}"
	@python3 -m venv $(VENV)
	@echo "${BLUE}⬆️ Upgrading pip...${RESET}"
	@$(PIP) install --upgrade pip
	@echo "${APPLE_GREEN}📦 Installing dependencies...${RESET}"
	@$(PIP) install -r $(REQUIREMENTS)
	@echo "${APPLE_GREEN}✅ Virtual environment ready!${RESET}"

check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "${YELLOW}⚠️  Virtual environment not found. Run 'make venv' first.${RESET}"; \
		exit 1; \
	fi

################################################################################
# Docker Management
################################################################################

sandbox-up:
	@echo "${YELLOW}🚀 Starting malware sandbox container...${RESET}"
	@$(DOCKER_COMPOSE) up -d
	@echo "${APPLE_GREEN}✅ Sandbox container started${RESET}"

sandbox-down:
	@echo "${BLUE}🛑 Stopping sandbox container...${RESET}"
	@$(DOCKER_COMPOSE) down
	@echo "${YELLOW}✨ Sandbox stopped${RESET}"

sandbox-rebuild:
	@echo "${BLUE}🔨 Rebuilding sandbox image...${RESET}"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "${APPLE_GREEN}✅ Sandbox rebuilt${RESET}"

################################################################################
# Running Scripts
################################################################################

run: check-venv check-config sandbox-up
	@echo "${YELLOW}▶️ Starting Automated DFIR Workflow...${RESET}"
	@echo "${YELLOW}📁 Monitoring: $(MONITORED_DIR)${RESET}"
	@echo "${YELLOW}📤 Shared:    $(SHARED_DIR)${RESET}"
	@make monitor

monitor: check-venv check-config
	@echo "${YELLOW}👀 Starting file monitoring only...${RESET}"
	@$(PYTHON) -m monitoring.file_watcher

################################################################################
# Utility Targets
################################################################################

re: clean-all all

clean:
	@echo "${BLUE}🧹 Cleaning project files (keeping venv)...${RESET}"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf "$(SHARED_DIR)/queue/*" "$(SHARED_DIR)/static-output/*" "$(SHARED_DIR)/reports/*" 2>/dev/null || true
	@if [ -f "$(QUEUE_FILE)" ]; then \
		echo "[]" > "$(QUEUE_FILE)"; \
	fi
	@echo "${YELLOW}✨ Project cleaned${RESET}"

clean-all: clean
	@echo "${BLUE}🧹 Complete cleanup...${RESET}"
	@make sandbox-down
	@docker rmi malware-sandbox:latest 2>/dev/null || true
	@docker system prune -af --volumes 2>/dev/null || true
	@rm -rf $(VENV)
	@rm -rf $(SHARED_DIR) 2>/dev/null || true
	@rm -rf config 2>/dev/null || true
	@echo "${YELLOW}✨ Everything cleaned${RESET}"

.PHONY: all help \
	venv check-venv \
	setup config check-config setup-shared \
	sandbox-up sandbox-down sandbox-logs sandbox-rebuild \
	run monitor \
	clean clean-all
