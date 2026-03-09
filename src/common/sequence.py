import logging
import os
import pandas as pd

logger = logging.getLogger(__name__)


class Sequence:
    def __init__(self, idx, path):
        self.idx = idx
        self.path = path
        self.name = os.path.basename(path)
        logger.info("Initialized sequence with index: %d, path: %s", idx, path)

        self.timestamps = pd.read_csv(
            os.path.join(path, f"aria/{self.name}.txt"),
            header=None,
            names=["timestamp"],
            dtype={"timestamp": "int64"},
        )
        self.cam0_df = pd.read_csv(
            os.path.join(path, "aria/cam0/data.csv"),
            header=None,
            names=["timestamp", "filename"],
        )
        self.cam1_df = pd.read_csv(
            os.path.join(path, "aria/cam1/data.csv"),
            header=None,
            names=["timestamp", "filename"],
        )
        self.imu0_df = pd.read_csv(
            os.path.join(path, "aria/imu0/data.csv"),
            header=None,
            names=[
                "timestamp",
                "gyro_x",
                "gyro_y",
                "gyro_z",
                "accel_x",
                "accel_y",
                "accel_z",
            ],
        )

        self.stereo_df = self.cam0_df.merge(
            self.cam1_df, on="timestamp", suffixes=("_cam0", "_cam1")
        )

        self.timeline_df = self.timestamps.merge(
            self.cam0_df, on="timestamp", how="left"
        ).merge(
            self.cam1_df,
            on="timestamp",
            how="left",
            suffixes=("_cam0", "_cam1"),
        )

    def get_num_frames(self, cam: str):
        if cam == "cam0":
            return len(self.cam0_df)
        elif cam == "cam1":
            return len(self.cam1_df)
        else:
            raise ValueError(f"Unknown camera: {cam}")

    def get_num_imu_measurements(self):
        return len(self.imu0_df)

    def get_num_timestamps(self):
        return len(self.timestamps)

    def get_cam_df(self, cam: str):
        if cam == "cam0":
            return self.cam0_df
        elif cam == "cam1":
            return self.cam1_df
        else:
            raise ValueError(f"Unknown camera: {cam}")

    def get_cam_data_dir(self, cam: str):
        if cam == "cam0":
            return os.path.join(self.path, "aria/cam0/data")
        elif cam == "cam1":
            return os.path.join(self.path, "aria/cam1/data")
        else:
            raise ValueError(f"Unknown camera: {cam}")

    def get_imu_between(self, t0, t1):
        return self.imu0_df[
            (self.imu0_df["timestamp"] >= t0) & (self.imu0_df["timestamp"] < t1)
        ]

    def get_frame_bundle(self, i: int):
        t0 = self.timestamps.iloc[i]["timestamp"]

        if i < len(self.timestamps) - 1:
            t1 = self.timestamps.iloc[i + 1]["timestamp"]
            imu_chunk = self.get_imu_between(t0, t1)
        else:
            imu_chunk = self.imu0_df[self.imu0_df["timestamp"] >= t0]

        return {
            "timestamp": t0,
            "cam0_file": self.cam0_df.iloc[i]["filename"],
            "cam1_file": self.cam1_df.iloc[i]["filename"],
            "imu": imu_chunk,
        }

    def build_frame_imu_alignment(self):
        return [self.get_frame_bundle(i) for i in range(len(self.timestamps))]
