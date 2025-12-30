"""
CI MODE DETECTION - Makes scripts work in GitHub Actions without prompts

Detects if running in CI environment and provides utilities for:
- Suppressing input prompts in CI mode
- Logging CI-specific messages
- Handling stdin gracefully
"""

import os
import sys
from typing import Optional


def is_ci_mode() -> bool:
    """Detect if running in CI environment (GitHub Actions, etc)."""
    return (
        os.getenv('CI') == 'true' 
        or os.getenv('GITHUB_ACTIONS') == 'true'
        or os.getenv('CONTINUOUS_INTEGRATION') == 'true'
        or os.getenv('TF_BUILD') == 'true'  # Azure Pipelines
        or os.getenv('TRAVIS') == 'true'    # Travis CI
        or os.getenv('CIRCLECI') == 'true'  # CircleCI
        or os.getenv('GITLAB_CI') == 'true' # GitLab CI
    )


def safe_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Safe input that handles CI mode and closed stdin.
    
    Returns default value in CI mode or when stdin is closed.
    """
    ci = is_ci_mode()
    
    # In CI mode, use default or return empty
    if ci:
        if default is not None:
            return default
        return ""
    
    # Try to get input, fall back to default if stdin is closed
    try:
        return input(prompt)
    except (EOFError, OSError):
        # stdin is closed or not available
        if default is not None:
            return default
        return ""


def confirm(prompt: str = "Continue?", default: bool = True) -> bool:
    """
    Safe confirmation prompt that handles CI mode.
    
    Returns default value in CI mode.
    """
    ci = is_ci_mode()
    
    # In CI mode, return default (usually True)
    if ci:
        return default
    
    # Try to get user confirmation
    try:
        response = input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").lower().strip()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            return default
    except (EOFError, OSError):
        return default


def print_ci_notice() -> None:
    """Print notice if running in CI mode."""
    if is_ci_mode():
        ci_name = os.getenv('GITHUB_ACTIONS', 'Unknown CI')
        print(f"🤖 Running in CI mode ({ci_name})")
