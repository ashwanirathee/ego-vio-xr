import logging
import os
import subprocess
from pathlib import Path

from src.common.visualizer import Visualizer
from src.common.sequence import Sequence
from src.common.loading import load_sequence_ids
from src.common.evaluation import evaluate_trajectory
from src.common.plotting import plot_trajectory_results
from evo.tools import file_interface
from evo.core import sync
from evo.core.metrics import PoseRelation, APE
from evo.tools import plot
import matplotlib.pyplot as plt
import numpy as np

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
        sequence_path = os.path.join(
            "data_outputs",
            "machine_hall",
            sequence.name,
        )
        orb_slam_output_path = os.path.join(
            "data_outputs", "machine_hall", sequence.name, "orb_slam"
        )
        os.makedirs(orb_slam_output_path, exist_ok=True)
        orb_slam_output_path = Path(orb_slam_output_path).resolve()
        orb_slam_output_path.mkdir(parents=True, exist_ok=True)
        output_file = os.path.join(orb_slam_output_path, "CameraTrajectory.txt")

        if os.path.exists(output_file):
            logger.info(
                f"ORB-SLAM output already exists for sequence {sequence.name}, skipping ORB-SLAM run."
            )
        else:
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
                logger.info(
                    f"Mounting ORB-SLAM output to: {orb_slam_output_path}"
                )
                logger.info(
                    f"{sequence.name} - Running ORB-SLAM in Docker container..."
                )
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
                        sequence.name,
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
        kimera_slam_output_path = os.path.join(
            "data_outputs", "machine_hall", sequence.name, "kimera_slam"
        )
        os.makedirs(kimera_slam_output_path, exist_ok=True)
        kimera_slam_output_path = Path(kimera_slam_output_path).resolve()
        kimera_slam_output_path.mkdir(parents=True, exist_ok=True)
        output_file = os.path.join(kimera_slam_output_path, "traj_vio.csv")
        if os.path.exists(output_file):
            logger.info(
                f"Kimera-SLAM output already exists for sequence {sequence.name}, skipping Kimera-SLAM run."
            )
        else:
            try:
                param_path = "/Users/ash/Documents/resources/job-search/job-projects/ego-vio-xr/data/assets/params"
                logger.info(
                    f"Running Kimera-SLAM for sequence {sequence.name}..."
                )
                env = os.environ.copy()
                env["DISPLAY"] = ":0"
                env["PATH"] = f"/opt/X11/bin:{env.get('PATH', '')}"
                image = "orbslam:latest"  # replace with your actual image name
                subprocess.run(
                    ["xhost", "+localhost"],
                    check=True,
                    env=env,
                )
                # -it -e DISPLAY=host.docker.internal:0
                commands = [
                    "docker",
                    "run",
                    "--rm",
                    "-it",
                    "-e",
                    "DISPLAY=host.docker.internal:0",
                    "-v",
                    f"{input_path}:/datasets:ro",
                    "-v",
                    f"{kimera_slam_output_path}:/output:rw",
                    "-v",
                    f"{param_path}/:/kimera_params:ro",
                    "kimera:latest",  # replace with your actual image name
                    "bash",
                    "/datasets/run_single_machine_hall_kimera_slam.sh",
                    sequence.name,
                ]
                logger.info(
                    f"Running Docker container with command: {' '.join(commands)}"
                )
                subprocess.run(
                    commands,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"Error running Kimera-SLAM for sequence {sequence.name}: {e}"
                )
                return
            finally:
                subprocess.run(
                    ["xhost", "-localhost"],
                    check=False,
                    env=env,
                )

        euroc_csv = f"{input_path}/{sequence.name}/mav0/state_groundtruth_estimate0/data.csv"
        tum_out = f"{input_path}/{sequence.name}/mav0/state_groundtruth_estimate0/data.tum"

        traj = file_interface.read_euroc_csv_trajectory(euroc_csv)
        file_interface.write_tum_trajectory_file(tum_out, traj)
        traj_ref = file_interface.read_tum_trajectory_file(tum_out)

        # ---------- Method 1: ORB-SLAM3 ----------
        orb_raw_path = f"{orb_slam_output_path}/CameraTrajectory.txt"
        orb_tum_path = f"{orb_slam_output_path}/orb_slam3.txt"

        assert os.path.exists(orb_raw_path), (
            f"ORB-SLAM output file not found for sequence {sequence.name}"
        )

        if not os.path.exists(orb_tum_path):
            traj_est_1_raw = file_interface.read_tum_trajectory_file(
                orb_raw_path
            )
            traj_est_1_raw.timestamps = traj_est_1_raw.timestamps / 1e9
            file_interface.write_tum_trajectory_file(
                orb_tum_path, traj_est_1_raw
            )

        traj_est_1 = file_interface.read_tum_trajectory_file(orb_tum_path)

        # ---------- Method 2: Kimera ----------
        kimera_raw_path = f"{kimera_slam_output_path}/traj_vio.csv"
        kimera_tum_path = f"{kimera_slam_output_path}/kimera.txt"

        assert os.path.exists(kimera_raw_path), (
            f"Kimera-SLAM output file not found for sequence {sequence.name}"
        )

        if not os.path.exists(kimera_tum_path):
            traj_est_2_raw = file_interface.read_euroc_csv_trajectory(
                kimera_raw_path
            )
            file_interface.write_tum_trajectory_file(
                kimera_tum_path, traj_est_2_raw
            )

        traj_est_2 = file_interface.read_tum_trajectory_file(kimera_tum_path)

        # ---------- Evaluate ----------
        traj_ref_sync_1, traj_est_sync_1, stats_1 = evaluate_trajectory(
            traj_ref, traj_est_1, name="ORB-SLAM3", align=True
        )

        traj_ref_sync_2, traj_est_sync_2, stats_2 = evaluate_trajectory(
            traj_ref, traj_est_2, name="Kimera", align=True
        )

        synced_methods = [
            ("ORB-SLAM3", traj_ref_sync_1, traj_est_sync_1),
            ("Kimera", traj_ref_sync_2, traj_est_sync_2),
        ]

        plot_trajectory_results(synced_methods, Path(sequence_path))
