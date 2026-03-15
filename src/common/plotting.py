# Example:
# synced_methods = [
#     ("ORB-SLAM3", traj_ref_sync_1, traj_est_sync_1),
#     ("Method2",   traj_ref_sync_2, traj_est_sync_2),
# ]

from scipy.spatial.transform import Rotation as R
import numpy as np
import matplotlib.pyplot as plt

def _rel_time_seconds( traj):
    t = np.asarray(traj.timestamps)
    return (t - t[0]).astype(np.float64)


def compute_speed(traj):
    t = _rel_time_seconds(traj)
    p = np.asarray(traj.positions_xyz)

    dt = np.diff(t)
    dp = np.diff(p, axis=0)

    speed = np.linalg.norm(dp, axis=1) / np.clip(dt, 1e-12, None)
    t_speed = 0.5 * (t[:-1] + t[1:])
    return t_speed, speed


def quat_wxyz_to_rpy_deg(quat_wxyz):
    quat_wxyz = np.asarray(quat_wxyz)
    quat_xyzw = np.column_stack(
        [quat_wxyz[:, 1], quat_wxyz[:, 2], quat_wxyz[:, 3], quat_wxyz[:, 0]]
    )
    return R.from_quat(quat_xyzw).as_euler("xyz", degrees=True)


def plot_trajectory_results(synced_methods, output_path):
    """
    synced_methods: list of tuples
        [
            (method_name, traj_ref_sync, traj_est_sync),
            ...
        ]
    output_path: pathlib.Path
    """

    if not synced_methods:
        return

    # Use the first reference for plotting ground truth
    # Usually all references are the same underlying GT, just separately associated.
    ref_name, traj_ref_sync, _ = synced_methods[0]

    t_ref = _rel_time_seconds(traj_ref_sync)
    pos_ref = np.asarray(traj_ref_sync.positions_xyz)
    quat_ref = np.asarray(traj_ref_sync.orientations_quat_wxyz)
    rpy_ref = quat_wxyz_to_rpy_deg(quat_ref)

    # ---------- 3D Trajectory ----------
    fig_traj = plt.figure(figsize=(10, 8))
    ax_traj = fig_traj.add_subplot(111, projection="3d")

    ax_traj.plot(
        pos_ref[:, 0], pos_ref[:, 1], pos_ref[:, 2], label="ground truth"
    )

    for method_name, _, traj_est_sync in synced_methods:
        pos_est = np.asarray(traj_est_sync.positions_xyz)
        ax_traj.plot(
            pos_est[:, 0],
            pos_est[:, 1],
            pos_est[:, 2],
            linestyle="--",
            label=method_name,
        )

    ax_traj.set_title("Trajectory (3D)")
    ax_traj.set_xlabel("x [m]")
    ax_traj.set_ylabel("y [m]")
    ax_traj.set_zlabel("z [m]")
    ax_traj.legend()
    fig_traj.tight_layout()
    fig_traj.savefig(output_path / "trajectories_3d.png", dpi=200)
    plt.close(fig_traj)

    # ---------- XYZ vs time ----------
    fig_xyz, axarr_xyz = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    xyz_labels = ["x [m]", "y [m]", "z [m]"]
    for k in range(3):
        axarr_xyz[k].plot(t_ref, pos_ref[:, k], label="ground truth")

        for method_name, _, traj_est_sync in synced_methods:
            t_est = _rel_time_seconds(traj_est_sync)
            pos_est = np.asarray(traj_est_sync.positions_xyz)

            axarr_xyz[k].plot(
                t_est, pos_est[:, k], linestyle="--", label=method_name
            )

        axarr_xyz[k].set_ylabel(xyz_labels[k])
        axarr_xyz[k].grid(True)
        axarr_xyz[k].legend()

    axarr_xyz[-1].set_xlabel("time [s]")
    fig_xyz.suptitle("Position vs Time")
    fig_xyz.tight_layout()
    fig_xyz.savefig(output_path / "xyz.png", dpi=200)
    plt.close(fig_xyz)

    # ---------- RPY vs time ----------
    fig_rpy, axarr_rpy = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    rpy_labels = ["roll [deg]", "pitch [deg]", "yaw [deg]"]
    for k in range(3):
        axarr_rpy[k].plot(t_ref, rpy_ref[:, k], label="ground truth")

        for method_name, _, traj_est_sync in synced_methods:
            t_est = _rel_time_seconds(traj_est_sync)
            quat_est = np.asarray(traj_est_sync.orientations_quat_wxyz)
            rpy_est = quat_wxyz_to_rpy_deg(quat_est)

            axarr_rpy[k].plot(
                t_est, rpy_est[:, k], linestyle="--", label=method_name
            )

        axarr_rpy[k].set_ylabel(rpy_labels[k])
        axarr_rpy[k].grid(True)
        axarr_rpy[k].legend()

    axarr_rpy[-1].set_xlabel("time [s]")
    fig_rpy.suptitle("Roll / Pitch / Yaw vs Time")
    fig_rpy.tight_layout()
    fig_rpy.savefig(output_path / "rpy.png", dpi=200)
    plt.close(fig_rpy)

    # ---------- Speed vs time ----------
    t_speed_ref, speed_ref = compute_speed(traj_ref_sync)

    fig_speed = plt.figure(figsize=(10, 5))
    ax_speed = fig_speed.add_subplot(111)
    ax_speed.plot(t_speed_ref, speed_ref, label="ground truth")

    for method_name, _, traj_est_sync in synced_methods:
        t_speed_est, speed_est = compute_speed(traj_est_sync)
        ax_speed.plot(
            t_speed_est, speed_est, linestyle="--", label=method_name
        )

    ax_speed.set_title("Speed vs Time")
    ax_speed.set_xlabel("time [s]")
    ax_speed.set_ylabel("speed [m/s]")
    ax_speed.grid(True)
    ax_speed.legend()
    fig_speed.tight_layout()
    fig_speed.savefig(output_path / "speeds.png", dpi=200)
    plt.close(fig_speed)