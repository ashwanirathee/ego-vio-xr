"""
Argument parsing for Lamaria project.
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser for Lamaria evaluation.
    """
    p = argparse.ArgumentParser()
    p.add_argument(
        "--run_id",
        type=str,
        default="run_default",
        help="Run ID for logging",
    )
    p.add_argument(
        "--data_path", type=str, default="./data/lamaria/"
    )
    p.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    p.add_argument("--visualize", action="store_true", default=False)
    return p


def parse_args(argv=None):
    """
    parse the arguments for Lamaria evaluation.
    """
    return build_parser().parse_args(argv)