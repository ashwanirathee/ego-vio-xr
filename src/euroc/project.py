import logging
import os
import subprocess
from pathlib import Path

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

        sequence = Sequence(idx, sequence_path, entry_folder="mav0")

        # input_path = os.path.join(sequence_path)
        input_path = os.path.join(self.args.data_path)
        orb_slam_output_path = os.path.join(
            "data_outputs", "machine_hall", sequence.name, "orb_slam"
        )
        os.makedirs(orb_slam_output_path, exist_ok=True)
        orb_slam_output_path = Path(orb_slam_output_path).resolve()
        orb_slam_output_path.mkdir(parents=True, exist_ok=True)

        kimera_slam_output_path = os.path.join(
            "data_outputs", "machine_hall", sequence.name, "kimera_slam"
        )
        os.makedirs(kimera_slam_output_path, exist_ok=True)

        # run orb_slam
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        env["PATH"] = f"/opt/X11/bin:{env.get('PATH', '')}"
        image = "orbslam:latest"  # replace with your actual image name
        try:
            subprocess.run(
                ["xhost", "+localhost"],
                check=True,
                env=env,
            )
            logger.info(f"Running Docker container with image: {image}")
            logger.info(f"Mounting sequence data from: {input_path}")
            logger.info(f"Mounting ORB-SLAM output to: {orb_slam_output_path}")
            logger.info(f"{sequence.name} - Running ORB-SLAM in Docker container...")
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-it",
                    "-e",
                    "DISPLAY=host.docker.internal:0",
                    "-v",
                    f"{input_path}:/datasets:ro",
                    "-v",
                    f"{orb_slam_output_path}:/output:rw",
                    image,
                    "bash",
                    "/datasets/run_single_machine_hall_orb_slam.sh",
                    sequence.name
                ],
                check=True,
                env=env,
            )

        finally:
            subprocess.run(
                ["xhost", "-localhost"],
                check=False,
                env=env,
            )

        # run kimera_slam

        # use the ground truth trajectory for visualization

        # visualize the results
