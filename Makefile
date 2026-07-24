# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: opernod <opernod@student.42lyon.fr>        +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/06/02 12:07:37 by opernod           #+#    #+#              #
#    Updated: 2026/06/09 15:17:03 by opernod          ###   ########lyon.fr    #
#                                                                              #
# **************************************************************************** #

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
	@uv run python pac-man.py

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

test:
	@printf "$(COLOR_CYAN)Running tests...$(COLOR_RESET)\n"


.PHONY: all install run debug clean re lint lint-strict test
