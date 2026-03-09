import logging
import os

from src.common.visualizer import Visualizer
from src.common.sequence import Sequence
from src.common.loading import load_sequence_ids

logger = logging.getLogger(__name__)

class Project:
    def __init__(self, args):
        self.args = args
        self.visualizer = Visualizer()

    def run(self):
        logger.info("Running the benchmark...")
        logging.basicConfig(
            level=getattr(logging, self.args.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )

        logger.info("Starting evaluation with run ID: %s", self.args.run_id)

        self.process_all_sequences()

    def process_all_sequences(self):
        logger.info("Processing all sequences for the benchmark...")

        logger.info("Loading sequence IDs...")
        sequences_file = os.path.join(self.args.data_path, "sequences.txt")
        logger.info(f"Sequences file: {sequences_file}")
        sequence_paths = load_sequence_ids(sequences_file)

        for idx, sequence_path in enumerate(sequence_paths):
            self.process_single_sequence(idx, sequence_path)

    def process_single_sequence(self, idx, sequence_path):
        logger.info(f"Processing sequence {sequence_path} for the benchmark...")

        sequence = Sequence(idx, sequence_path)
        self.visualizer.initial_scene(sequence)

