#!/usr/bin/env python3
"""Prepare environment for a process run."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from platform_problem_monitoring_core.utils import ensure_dir_exists, logger


def prepare_environment() -> str:
    """
    Prepare environment for a process run.

    Returns:
        Path to the temporary work folder
    """
    logger.info("Preparing environment for process run")

    # Create temporary work directory
    work_dir = tempfile.mkdtemp(prefix="platform_problem_monitoring_")
    logger.info(f"Created temporary work directory: {work_dir}")

    # Ensure the directory exists and is writable
    ensure_dir_exists(work_dir)

    work_path = Path(work_dir)
    if not work_path.exists() or not os.access(work_dir, os.W_OK):
        logger.error(f"No write access to temporary directory: {work_dir}")
        sys.exit(1)

    logger.info("Environment preparation complete")
    return work_dir


def main() -> None:
    """Execute the script when run directly."""
    parser = argparse.ArgumentParser(description="Prepare environment for a process run")
    # Parse arguments but don't assign to a variable since we don't use them
    parser.parse_args()

    try:
        work_dir = prepare_environment()
        # Print the work directory path for the next step to use
        print(work_dir)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error preparing environment: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
