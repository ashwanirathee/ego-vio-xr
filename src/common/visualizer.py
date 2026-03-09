import logging
import rerun as rr
import os 
import numpy as np
import cv2

logger = logging.getLogger(__name__)

class Visualizer:
    def __init__(self, name="visualizer", spawn=True):
        rr.init(name, spawn=spawn)
        if not spawn:
            rr.serve_web_viewer(connect_to=rr.serve_grpc())

    def initial_input(self, sequence):
        logger.info(f"Visualizing initial input for sequence...")

        cam0 = "cam0"
        n = int(sequence.get_num_frames(cam0) / 10)
        df = sequence.get_cam_df(cam0)
        img_dir = sequence.get_cam_data_dir(cam0)

        if len(df) == 0:
            return
        
        cam1 = "cam1"
        df1 = sequence.get_cam_df(cam1)
        img_dir1 = sequence.get_cam_data_dir(cam1)

        if len(df1) == 0:
            return

        # sample evenly across the whole sequence
        sample_idx = np.linspace(0, len(df) - 1, min(n, len(df)), dtype=int)
        sampled_df = df.iloc[sample_idx].reset_index(drop=True)
        sampled_df1 = df1.iloc[sample_idx].reset_index(drop=True)

        for i, row in sampled_df.iterrows():
            img_path = os.path.join(img_dir, row["filename"])
            print(f"Visualizing image: {img_path}")
            if not os.path.exists(img_path):
                continue


            img_path1 = os.path.join(img_dir1, sampled_df1.iloc[i]["filename"])
            print(f"Visualizing image: {img_path1}")
            if not os.path.exists(img_path1):
                continue

            img = np.array(cv2.imread(img_path))
            img1 = np.array(cv2.imread(img_path1))

            # rr.set_time("frame", sequence=i)
            rr.set_time(
                "timestamp",
                timestamp=np.datetime64(int(row["timestamp"]), "ns")
            )

            rr.log(f"{sequence.name}/{cam0}/image", rr.Image(img))
            rr.log(f"{sequence.name}/{cam1}/image", rr.Image(img1))
            
    def initial_scene(self, sequence):
        logger.info(f"Visualizing initial scene for sequence...")
        cam0_dir = os.path.join(sequence.path, "aria/cam0/data")
        cam1_dir = os.path.join(sequence.path, "aria/cam1/data")

        for i in range(sequence.get_num_timestamps()):
            bundle = sequence.get_frame_bundle(i)

            # Timelines
            rr.set_time("frame", sequence=i)

            # Treat these as relative sensor times unless you know they are Unix timestamps
            rr.set_time(
                "sensor_time",
                duration=np.timedelta64(int(bundle["timestamp"]), "ns")
            )

            # Images
            cam0_path = os.path.join(cam0_dir, bundle["cam0_file"])
            cam1_path = os.path.join(cam1_dir, bundle["cam1_file"])

            if os.path.exists(cam0_path):
                cam0_img = cv2.imread(cam0_path)
                rr.log(f"{sequence.name}/cam0/image", rr.Image(cam0_img))

            if os.path.exists(cam1_path):
                cam1_img = cv2.imread(cam1_path)
                rr.log(f"{sequence.name}/cam1/image", rr.Image(cam1_img))

            # Optional text panel
            rr.log(
                "world/frame_info",
                rr.TextDocument(
                    f"frame: {i}\n"
                    f"timestamp: {bundle['timestamp']}\n"
                    f"cam0: {bundle['cam0_file']}\n"
                    f"cam1: {bundle['cam1_file']}\n"
                    f"num_imu: {len(bundle['imu'])}"
                )
            )

            imu = bundle["imu"]
            if len(imu) > 0:
                rr.log(f"{sequence.name}/imu/gyro_x", rr.SeriesLines(names="gyro_x"), static=True)
                rr.log(f"{sequence.name}/imu/gyro_y", rr.SeriesLines(names="gyro_y"), static=True)
                rr.log(f"{sequence.name}/imu/gyro_z", rr.SeriesLines(names="gyro_z"), static=True)
                rr.log(f"{sequence.name}/imu/accel_x", rr.SeriesLines(names="accel_x"), static=True)
                rr.log(f"{sequence.name}/imu/accel_y", rr.SeriesLines(names="accel_y"), static=True)
                rr.log(f"{sequence.name}/imu/accel_z", rr.SeriesLines(names="accel_z"), static=True)

                for _, row in imu.iterrows():
                    rr.set_time(
                        "imu_time",
                        duration=np.timedelta64(int(row["timestamp"]), "ns")
                    )
                    rr.log(f"{sequence.name}/imu/gyro_x", rr.Scalars([row["gyro_x"]]))
                    rr.log(f"{sequence.name}/imu/gyro_y", rr.Scalars([row["gyro_y"]]))
                    rr.log(f"{sequence.name}/imu/gyro_z", rr.Scalars([row["gyro_z"]]))
                    rr.log(f"{sequence.name}/imu/accel_x", rr.Scalars([row["accel_x"]]))
                    rr.log(f"{sequence.name}/imu/accel_y", rr.Scalars([row["accel_y"]]))