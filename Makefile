
SRC_DIR = src

# Colors
COLOR_RESET = \033[0m
COLOR_CYAN = \033[36m
COLOR_GREEN = \033[32m
COLOR_RED = \033[31m
COLOR_YELLOW = \033[33m
COLOR_MAGENTA = \033[35m

install:
	@printf "$(COLOR_CYAN)Installing dependencies...$(COLOR_RESET)\n"
	@uv sync
	@printf "$(COLOR_GREEN)Installation completed$(COLOR_RESET)\n"

run:
	@printf "$(COLOR_CYAN)Starting game$(COLOR_RESET)\n"
	@uv run python pac-man.py config.json

debug:
	@printf "$(COLOR_YELLOW)========================================================$(COLOR_RESET)\n"
	@printf "$(COLOR_YELLOW)Debug mode enabled (pdb)$(COLOR_RESET)\n"
	@printf "  → $(COLOR_YELLOW)s$(COLOR_RESET) : Step (enter functions)\n"
	@printf "  → $(COLOR_YELLOW)n$(COLOR_RESET) : Next (without entering)\n"
	@printf "  → $(COLOR_YELLOW)c$(COLOR_RESET) : Continue execution\n"
	@printf "  → $(COLOR_YELLOW)l$(COLOR_RESET) : Display current code\n"
	@printf "  → $(COLOR_YELLOW)q$(COLOR_RESET) : Quit debugger\n"
	@printf "$(COLOR_YELLOW)========================================================$(COLOR_RESET)\n"
	@uv run python -m pdb $(SRC_DIR)/main.py

clean:
	@printf "$(COLOR_RED)Cleaning project...$(COLOR_RESET)\n"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.log" -delete
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@rm -f output.txt
	@rm -rf .venv
	@rm -fr package
	@printf "$(COLOR_GREEN)✓ Cleanup completed$(COLOR_RESET)\n"

lint:
	@printf "$(COLOR_CYAN)Running Flake8...$(COLOR_RESET)\n"
	@uv run python -m flake8 $(SRC_DIR)/ && \
		printf "$(COLOR_GREEN)✓ $(COLOR_CYAN)Flake8$(COLOR_GREEN) [OK]$(COLOR_RESET)\n"

	@printf "$(COLOR_CYAN)Running Mypy...$(COLOR_RESET)\n"
	@uv run python -m mypy $(SRC_DIR)/ --warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs && \
		printf "$(COLOR_GREEN)✓ $(COLOR_CYAN)Mypy$(COLOR_GREEN) [OK]$(COLOR_RESET)\n"

	@printf "$(COLOR_GREEN)✓ Lint completed$(COLOR_RESET)\n"

lint-strict:
	@printf "$(COLOR_MAGENTA)⚠ Strict linting$(COLOR_RESET)\n"

	@printf "$(COLOR_CYAN)Running Flake8...$(COLOR_RESET)\n"
	@uv run python -m flake8 $(SRC_DIR)/ && \
		printf "$(COLOR_GREEN)✓ $(COLOR_CYAN)Flake8$(COLOR_GREEN) [OK]$(COLOR_RESET)\n"

	@printf "$(COLOR_CYAN)Running Mypy...$(COLOR_RESET)\n"
	@uv run python -m mypy $(SRC_DIR) --strict && \
		printf "$(COLOR_GREEN)✓ $(COLOR_CYAN)Mypy strict$(COLOR_GREEN) [OK]$(COLOR_RESET)\n"

	@printf "$(COLOR_GREEN)✓ Strict verification completed$(COLOR_RESET)\n"

package:
	uv run pyinstaller --noconsole pac-man.py
	cp -r assets/ dist/pac-man/
	cp config.json dist/pac-man/
	touch dist/pac-man/launch.sh
	@printf "#!/bin/bash\n./pac-man config.json" > dist/pac-man/launch.sh
	chmod +x dist/pac-man/launch.sh

init_test:
	@printf "$(COLOR_CYAN)Initializing test json...$(COLOR_RESET)\n"
	@python3 tester.py
	@printf "$(COLOR_GREEN)✓ Test environment initialized$(COLOR_RESET)\n"
test:
	@printf "$(COLOR_CYAN)Running parsing tests...$(COLOR_RESET)\n\n"
	@for file in $$(ls test/*.json 2>/dev/null | sort -V 2>/dev/null || ls test/*.json); do \
		test_name=$$(basename "$$file" .json); \
		if uv run python pac-man.py "$$file" > /dev/null 2>&1; then \
			printf "$(COLOR_RED)✗ $$test_name : c'est une erreur (le jeu s'est lancé)$(COLOR_RESET)\n"; \
		else \
			printf "$(COLOR_GREEN)✓ $$test_name : on est bon$(COLOR_RESET)\n"; \
		fi; \
	done
	@printf "\n$(COLOR_CYAN)Tests finished.$(COLOR_RESET)

test:
	@printf "$(COLOR_CYAN)Running parsing tests...$(COLOR_RESET)\n\n"
	@for file in $$(ls test/*.json 2>/dev/null | sort -V 2>/dev/null || ls test/*.json); do \
		test_name=$$(basename "$$file" .json); \
		printf "$(COLOR_YELLOW)[TEST] $$test_name$(COLOR_RESET)\n"; \
		timeout 1.5 uv run python pac-man.py "$$file" > /dev/null 2>&1; \
		STATUS=$$?; \
		if [ $$STATUS -eq 124 ]; then \
			printf "  $(COLOR_GREEN)✓ Le jeu s'est lancé et a continué (Timeout 1.5s)$(COLOR_RESET)\n"; \
		elif [ $$STATUS -eq 0 ]; then \
			printf "  $(COLOR_RED)✗ Le programme a quitté proprement sans lancer le jeu (Exit 0)$(COLOR_RESET)\n"; \
		else \
			printf "  $(COLOR_RED)✗ Le programme a crashé (Exit $$STATUS - Traceback interdit)$(COLOR_RESET)\n"; \
		fi; \
	done
	@printf "\n$(COLOR_CYAN)Tests finished.$(COLOR_RESET)\n"

.PHONY: all install run debug clean re lint lint-strict test
