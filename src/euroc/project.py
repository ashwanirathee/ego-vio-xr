import logging
import os
import subprocess
from pathlib import Path

from src.common.visualizer import Visualizer
from src.common.sequence import Sequence
from src.common.loading import load_sequence_ids
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

    def _rel_time_seconds(self, traj):
        t = np.asarray(traj.timestamps)
        return (t - t[0]).astype(np.float64)


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
        
        output_file = os.path.join(orb_slam_output_path, "CameraTrajectory.txt")

        if os.path.exists(output_file):
            logger.info(f"ORB-SLAM output already exists for sequence {sequence.name}, skipping ORB-SLAM run.")
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
        traj_est = file_interface.read_tum_trajectory_file(f"{orb_slam_output_path}/CameraTrajectory.txt")

        traj_est.timestamps = traj_est.timestamps / 1e9

        file_interface.write_tum_trajectory_file(f"{orb_slam_output_path}/orb_slam3.txt", traj_est)

        euroc_csv = f"{input_path}/{sequence.name}/mav0/state_groundtruth_estimate0/data.csv"
        tum_out = f"{orb_slam_output_path}/data.tum"

        traj = file_interface.read_euroc_csv_trajectory(euroc_csv)
        file_interface.write_tum_trajectory_file(tum_out, traj)

        traj_ref = file_interface.read_tum_trajectory_file(tum_out)

        traj_ref_sync, traj_est_sync = sync.associate_trajectories(traj_ref, traj_est)
        align = True  # set to True to perform SE(3) alignment of estimate to reference before computing metrics
        # Optional SE(3) alignment of estimate to reference
        if align:
            traj_est_sync.align(traj_ref_sync)

        # Metrics
        ape_metric = APE(PoseRelation.translation_part)
        ape_metric.process_data((traj_ref_sync, traj_est_sync))
        stats = ape_metric.get_all_statistics()
        logger.info(f"APE results: {stats}")
        logger.info(f"APE translation RMSE: {stats['rmse']:.4f} m")
        logger.info(f"APE translation mean: {stats['mean']:.4f} m")
        logger.info(f"APE translation median: {stats['median']:.4f} m")
        logger.info(f"APE translation std: {stats['std']:.4f} m")
        logger.info(f"APE translation min: {stats['min']:.4f} m")
        logger.info(f"APE translation max: {stats['max']:.4f} m")

        orb_slam_output_path = Path(orb_slam_output_path)
        orb_slam_output_path.mkdir(parents=True, exist_ok=True)

        t_ref = self._rel_time_seconds(traj_ref_sync)
        t_est = self._rel_time_seconds(traj_est_sync)

        pos_ref = np.asarray(traj_ref_sync.positions_xyz)
        pos_est = np.asarray(traj_est_sync.positions_xyz)

        quat_ref = np.asarray(traj_ref_sync.orientations_quat_wxyz)
        quat_est = np.asarray(traj_est_sync.orientations_quat_wxyz)

        # ---------- 3D Trajectory ----------
        fig_traj = plt.figure(figsize=(10, 8))
        ax_traj = fig_traj.add_subplot(111, projection="3d")

        ax_traj.plot(
            pos_ref[:, 0], pos_ref[:, 1], pos_ref[:, 2],
            label="ground truth"
        )
        ax_traj.plot(
            pos_est[:, 0], pos_est[:, 1], pos_est[:, 2],
            linestyle="--",
            label="orb_slam_estimate"
        )

        ax_traj.set_title("Trajectory (3D)")
        ax_traj.set_xlabel("x [m]")
        ax_traj.set_ylabel("y [m]")
        ax_traj.set_zlabel("z [m]")
        ax_traj.legend()
        fig_traj.tight_layout()
        fig_traj.savefig(orb_slam_output_path / "trajectories_3d.png", dpi=200)
        plt.close(fig_traj)

        # ---------- XYZ vs time ----------
        fig_xyz, axarr_xyz = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        xyz_labels = ["x [m]", "y [m]", "z [m]"]
        for k in range(3):
            axarr_xyz[k].plot(t_ref, pos_ref[:, k], label="ground truth")
            axarr_xyz[k].plot(t_est, pos_est[:, k], linestyle="--", label="estimate")
            axarr_xyz[k].set_ylabel(xyz_labels[k])
            axarr_xyz[k].grid(True)
            axarr_xyz[k].legend()

        axarr_xyz[-1].set_xlabel("time [s]")
        fig_xyz.suptitle("Position vs Time")
        fig_xyz.tight_layout()
        fig_xyz.savefig(orb_slam_output_path / "xyz.png", dpi=200)
        plt.close(fig_xyz)

        # ---------- RPY vs time ----------
        # evo stores quaternions as wxyz
        from scipy.spatial.transform import Rotation as R

        rpy_ref = R.from_quat(
            np.column_stack([quat_ref[:, 1], quat_ref[:, 2], quat_ref[:, 3], quat_ref[:, 0]])
        ).as_euler("xyz", degrees=True)

        rpy_est = R.from_quat(
            np.column_stack([quat_est[:, 1], quat_est[:, 2], quat_est[:, 3], quat_est[:, 0]])
        ).as_euler("xyz", degrees=True)

        fig_rpy, axarr_rpy = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        rpy_labels = ["roll [deg]", "pitch [deg]", "yaw [deg]"]
        for k in range(3):
            axarr_rpy[k].plot(t_ref, rpy_ref[:, k], label="ground truth")
            axarr_rpy[k].plot(t_est, rpy_est[:, k], linestyle="--", label="estimate")
            axarr_rpy[k].set_ylabel(rpy_labels[k])
            axarr_rpy[k].grid(True)
            axarr_rpy[k].legend()

        axarr_rpy[-1].set_xlabel("time [s]")
        fig_rpy.suptitle("Roll / Pitch / Yaw vs Time")
        fig_rpy.tight_layout()
        fig_rpy.savefig(orb_slam_output_path / "rpy.png", dpi=200)
        plt.close(fig_rpy)

        # ---------- Speed vs time ----------
        def compute_speed(traj):
            t = self._rel_time_seconds(traj)
            p = np.asarray(traj.positions_xyz)

            dt = np.diff(t)
            dp = np.diff(p, axis=0)

            speed = np.linalg.norm(dp, axis=1) / np.clip(dt, 1e-12, None)
            t_speed = 0.5 * (t[:-1] + t[1:])
            return t_speed, speed

        t_speed_ref, speed_ref = compute_speed(traj_ref_sync)
        t_speed_est, speed_est = compute_speed(traj_est_sync)

        fig_speed = plt.figure(figsize=(10, 5))
        ax_speed = fig_speed.add_subplot(111)
        ax_speed.plot(t_speed_ref, speed_ref, label="ground truth")
        ax_speed.plot(t_speed_est, speed_est, linestyle="--", label="estimate")
        ax_speed.set_title("Speed vs Time")
        ax_speed.set_xlabel("time [s]")
        ax_speed.set_ylabel("speed [m/s]")
        ax_speed.grid(True)
        ax_speed.legend()
        fig_speed.tight_layout()
        fig_speed.savefig(orb_slam_output_path / "speeds.png", dpi=200)
        plt.close(fig_speed)

        # visualize the results
