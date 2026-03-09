import os
import logging

logger = logging.getLogger(__name__)


def load_sequence_ids(sequences_file: str):
    """
    Loads the sequence IDs from the specified file.
    """
    if not os.path.exists(sequences_file):
        logger.error("Sequences file not found: %s", sequences_file)
        return [], []

    with open(sequences_file, "r", encoding="utf-8") as f:
        folder_names = [line.strip() for line in f if line.strip()]

    input_paths = [
        os.path.join(os.path.dirname(sequences_file), n) for n in folder_names
    ]
    return input_paths
