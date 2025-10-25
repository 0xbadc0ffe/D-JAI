# Danceometer Feature

A computer vision module that detects people and estimates their dance activity using YOLOv8.

## Overview

The Danceometer analyzes video input (from camera or file) and outputs two metrics:
- **Number of people**: Count of detected people in the frame
- **Danciness**: Movement score (0-100) indicating how much people are dancing

## Installation

Dependencies are in `requirements.txt`:
```bash
pip install ultralytics opencv-python
```

## Usage

### Quick Test
```bash
python src/test_danceometer.py --unit
```

### Use in Your Code
```python
from danceometer import Danceometer

# Initialize
danceometer = Danceometer()

# Process single frame
import cv2
frame = cv2.imread('image.jpg')
num_people, danciness = danceometer.process_frame(frame)
print(f"People: {num_people}, Danciness: {danciness:.2f}")

# Process live camera
danceometer.process_video(0, display=True)  # 0 = default webcam

# Process video file
danceometer.process_video("path/to/video.mp4", display=True)

# Get average metrics from entire video
avg_people, avg_danciness = danceometer.get_metrics_from_video("video.mp4")
```

### Continuous Monitoring

**Monitor camera every T seconds (default 30s):**
```bash
# Default: 30s interval, camera 0
python src/danceometer_monitor.py

# Custom interval (15 seconds)
python src/danceometer_monitor.py --interval 15

# Save metrics to log file
python src/danceometer_monitor.py --log log/dance_metrics.json

# Lower CPU usage (5 FPS buffer)
python src/danceometer_monitor.py --fps 5
```

**Use in code:**
```python
from danceometer_monitor import DanceometerMonitor

# Create monitor
monitor = DanceometerMonitor(interval=30, buffer_fps=10)
monitor.start()

# Get current metrics anytime
metrics = monitor.get_current_metrics()
print(metrics)  # {'num_people': 5, 'danciness': 42.3, 'timestamp': ...}

# Stop when done
monitor.stop()
```

### Testing Options

```bash
# Unit tests
python src/test_danceometer.py --unit

# Test with webcam
python src/test_danceometer.py --webcam

# Test with video file
python src/test_danceometer.py --video path/to/video.mp4

# Batch analysis (no display)
python src/test_danceometer.py --batch path/to/video.mp4
```

## How It Works

1. **Person Detection**: Uses YOLOv8 (nano model by default) to detect people in each frame
2. **Movement Tracking**: Tracks person positions across frames
3. **Danciness Calculation**: 
   - Measures pixel displacement between frames
   - Normalizes by person size
   - Smooths over 30 frames for stability
   - Scales to 0-100 range

## API Reference

### Danceometer Class

```python
class Danceometer(model_size='yolov8n.pt')
```

**Parameters:**
- `model_size`: YOLO model to use ('yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', etc.)

**Methods:**

#### `process_frame(frame)`
Process a single video frame.
- **Input**: `frame` - numpy array (BGR image from cv2)
- **Returns**: `(num_people, danciness)` tuple

#### `process_video(video_source, display=True)`
Process video stream in real-time.
- **Input**: 
  - `video_source` - Camera index (0) or path to video file
  - `display` - Show annotated video window
- Press 'q' to quit

#### `get_metrics_from_video(video_path, sample_rate=5)`
Process entire video and return average metrics.
- **Input**:
  - `video_path` - Path to video file
  - `sample_rate` - Process every Nth frame
- **Returns**: `(avg_people, avg_danciness)` tuple

#### `reset()`
Reset tracking state between videos.

## Future Integration

The metrics can be integrated into the music generation pipeline to:
- Increase tempo/energy when danciness is high
- Generate more upbeat music when crowd is active
- Adjust volume based on number of people
- Trigger specific musical elements at danciness thresholds

## Performance Notes

- YOLOv8n (nano) is fastest, suitable for real-time
- YOLOv8s (small) is more accurate but slower
- Adjust `sample_rate` in batch processing for speed vs accuracy tradeoff
- Typical performance: 30-60 FPS on modern hardware with yolov8n

## Troubleshooting

**No people detected:**
- Check camera is working
- Ensure good lighting
- Try lowering confidence threshold in code (line 113: `if conf > 0.5`)

**Low danciness despite movement:**
- Increase sensitivity by modifying scale factor (line 87: `* 20.0`)
- Reduce smoothing window (line 34: `self.max_history = 30`)

**Too sensitive:**
- Decrease scale factor in line 87
- Increase matching distance threshold (line 65: `dist < 200`)
