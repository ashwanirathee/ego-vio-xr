# Ego VIO XR

We aim to build a visual odometry, visual-inertial odometry, and SLAM evaluation and development framework that supports widely used datasets and tools.

### Tools:
- Language: Python
- SLAM systems evaluated: ORB-SLAM3, Kimera VIO
- Datasets: EuRoC, Lamaria, inhouse data
- Infrastructure: Docker, Rerun
- Evaluation metrics: ATE, RPE, scale drift

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 ./run_euroc.py --log-level INFO
```

### Running Tests

```bash
pytest
```

### Results

The sequences below are from the EuRoC dataset, and the metrics are computed using evo_traj with SE(3) alignment of the ORB-SLAM estimate to the reference trajectory before computing metrics. The RMSE, mean, median, std, min, and max are in meters.

| Sequence        | Difficulty | RMSE (m) | Mean (m) | Median (m) | Std (m) | Min (m) | Max (m) |
| --------------- | ---------- | -------: | -------: | ---------: | ------: | ------: | ------: |
| MH_01_easy      | easy       |   0.0416 |   0.0382 |     0.0434 |  0.0164 |  0.0030 |  0.0857 |
| MH_02_easy      | easy       |   0.0306 |   0.0252 |     0.0190 |  0.0173 |  0.0039 |  0.0931 |
| MH_03_medium    | medium     |   0.0267 |   0.0235 |     0.0226 |  0.0127 |  0.0017 |  0.1036 |
| MH_04_difficult | difficult  |   0.0452 |   0.0374 |     0.0280 |  0.0254 |  0.0012 |  0.1857 |
| MH_05_difficult | difficult  |   0.0656 |   0.0570 |     0.0465 |  0.0325 |  0.0044 |  0.1711 |
