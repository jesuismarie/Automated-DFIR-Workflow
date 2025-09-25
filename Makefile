VENV		:= .venv
PYTHON		:= $(VENV)/bin/python
PIP			:= $(VENV)/bin/pip
DIR			?= ~/Downloads
SCRIPT		?= file_watcher.py

RESET		= \033[0m
BLUE		= \033[34m
YELLOW		= \033[38;2;255;239;0m
APPLE_GREEN	= \033[38;2;141;182;0m

all: run

venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	@echo "${BLUE}🔧 Creating virtual environment...${RESET}"
	@python3 -m venv $(VENV)
	@echo "${BLUE}⬆️  Upgrading pip...${RESET}"
	@$(PIP) install --upgrade pip
	@echo "${APPLE_GREEN}📦 Installing dependencies from requirements.txt...${RESET}"
	@$(PIP) install -r requirements.txt
	@echo "${APPLE_GREEN}✅ Virtual environment ready!${RESET}"
	@touch $(VENV)/bin/activate

run: check-venv
	@echo "${YELLOW}▶️  Running $(SCRIPT) on $(DIR)...${RESET}"
	@$(PYTHON) $(SCRIPT) $(DIR)

watch: check-venv
	@$(PYTHON) file_watcher.py $(DIR)

analyze: check-venv
	@$(PYTHON) analyzer.py $(DIR)

report: check-venv
	@$(PYTHON) report_generator.py $(DIR)

check-venv:
	@test -d $(VENV) || (echo "${YELLOW}⚠️  Virtual environment not found. Run 'make venv' first.${RESET}"; exit 1)

clean:
	@echo "${BLUE}🧹 Cleaning up...${RESET}"
	@rm -rf __pycache__ $(VENV)
	@echo "${YELLOW}✨ Everything is clean ✅${RESET}"

.PHONY: all venv run watch analyze report clean check-venv
