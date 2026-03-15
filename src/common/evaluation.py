from evo.core.metrics import APE, PoseRelation
from evo.core import sync
from evo.tools import file_interface
import logging

logger = logging.getLogger(__name__)

def evaluate_trajectory(traj_ref, traj_est, name: str, align: bool = True):
    # sync
    traj_ref_sync, traj_est_sync = sync.associate_trajectories(traj_ref, traj_est)

    # optional alignment
    if align:
        traj_est_sync.align(traj_ref_sync)

    # metric
    ape_metric = APE(PoseRelation.translation_part)
    ape_metric.process_data((traj_ref_sync, traj_est_sync))
    stats = ape_metric.get_all_statistics()

    logger.info(f"[{name}] APE results: {stats}")
    logger.info(f"[{name}] APE translation RMSE: {stats['rmse']:.4f} m")
    logger.info(f"[{name}] APE translation mean: {stats['mean']:.4f} m")
    logger.info(f"[{name}] APE translation median: {stats['median']:.4f} m")
    logger.info(f"[{name}] APE translation std: {stats['std']:.4f} m")
    logger.info(f"[{name}] APE translation min: {stats['min']:.4f} m")
    logger.info(f"[{name}] APE translation max: {stats['max']:.4f} m")

    return traj_ref_sync, traj_est_sync, stats