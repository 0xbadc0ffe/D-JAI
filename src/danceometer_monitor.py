"""
Continuous danceometer monitoring that samples camera every T seconds.
Processes the last chunk of frames and outputs metrics periodically.
"""

import cv2
import time
import numpy as np
from collections import deque
from threading import Thread, Lock, Event
from danceometer import Danceometer
from typing import Tuple, Optional
import json
from datetime import datetime


class DanceometerMonitor:
    """
    Continuously monitors camera and outputs metrics every T seconds.
    Buffers frames and processes them in chunks.
    """
    
    def __init__(self, 
                 camera_index: int = 0,
                 interval: int = 30,
                 buffer_fps: int = 10,
                 model_size: str = 'yolov8n.pt'):
        """
        Initialize the monitor.
        
        Args:
            camera_index: Camera device index (0 for default)
            interval: Seconds between metric calculations
            buffer_fps: FPS to capture for buffering (lower = less CPU)
            model_size: YOLO model to use
        """
        self.camera_index = camera_index
        self.interval = interval
        self.buffer_fps = buffer_fps
        self.frame_interval = 1.0 / buffer_fps
        
        # Calculate buffer size (store interval seconds of frames)
        self.max_frames = buffer_fps * interval
        
        # Frame buffer (circular)
        self.frame_buffer = deque(maxlen=self.max_frames)
        
        # Threading components
        self.lock = Lock()
        self.stop_event = Event()
        self.capture_thread = None
        self.process_thread = None
        
        # Metrics storage
        self.current_metrics = {
            'num_people': 0,
            'danciness': 0.0,
            'timestamp': None
        }
        self.metrics_lock = Lock()
        
        # Danceometer
        self.danceometer = Danceometer(model_size=model_size)
        
        # Camera
        self.cap = None
        
    def _capture_loop(self):
        """Capture frames continuously and store in buffer."""
        print(f"[Capture] Starting frame capture at {self.buffer_fps} FPS...")
        
        last_capture_time = time.time()
        
        while not self.stop_event.is_set():
            current_time = time.time()
            
            # Maintain target FPS
            if current_time - last_capture_time < self.frame_interval:
                time.sleep(0.001)  # Small sleep to avoid busy waiting
                continue
            
            ret, frame = self.cap.read()
            if not ret:
                print("[Capture] Failed to read frame")
                time.sleep(0.1)
                continue
            
            # Add frame to buffer with timestamp
            with self.lock:
                self.frame_buffer.append({
                    'frame': frame.copy(),
                    'timestamp': current_time
                })
            
            last_capture_time = current_time
        
        print("[Capture] Capture loop stopped")
    
    def _process_loop(self):
        """Process buffered frames every T seconds."""
        print(f"[Process] Starting periodic analysis every {self.interval}s...")
        
        # Wait for buffer to fill initially
        time.sleep(self.interval)
        
        while not self.stop_event.is_set():
            start_time = time.time()
            
            # Get frames from buffer
            with self.lock:
                if len(self.frame_buffer) == 0:
                    print("[Process] No frames in buffer, waiting...")
                    time.sleep(1)
                    continue
                
                # Copy buffer for processing
                frames_to_process = list(self.frame_buffer)
            
            print(f"\n[Process] Analyzing {len(frames_to_process)} frames...")
            
            # Reset danceometer state
            self.danceometer.reset()
            
            # Process frames
            people_counts = []
            danciness_scores = []
            
            for frame_data in frames_to_process:
                frame = frame_data['frame']
                num_people, danciness = self.danceometer.process_frame(frame)
                people_counts.append(num_people)
                danciness_scores.append(danciness)
            
            # Calculate metrics
            avg_people = np.mean(people_counts) if people_counts else 0
            avg_danciness = np.mean(danciness_scores) if danciness_scores else 0
            
            # Update metrics
            with self.metrics_lock:
                self.current_metrics = {
                    'num_people': round(avg_people, 2),
                    'danciness': round(avg_danciness, 2),
                    'timestamp': datetime.now().isoformat(),
                    'frames_analyzed': len(frames_to_process)
                }
            
            # Print results with enhanced formatting
            print("\n" + "="*60)
            print("DANCEOMETER UPDATE")
            print("="*60)
            print(f"👥 People detected: {avg_people:.2f}")
            print(f"💃 Danciness level: {avg_danciness:.2f}/100")
            print(f"🎬 Frames analyzed: {len(frames_to_process)}")
            print(f"⏱  Analysis time: {time.time() - start_time:.1f}s")
            print("="*60 + "\n")
            
            # Wait for next interval
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            
            if sleep_time > 0:
                self.stop_event.wait(sleep_time)
        
        print("[Process] Process loop stopped")
    
    def start(self):
        """Start monitoring."""
        print("=" * 60)
        print("DANCEOMETER MONITOR")
        print("=" * 60)
        print(f"Camera: {self.camera_index}")
        print(f"Interval: {self.interval}s")
        print(f"Buffer FPS: {self.buffer_fps}")
        print(f"Buffer size: {self.max_frames} frames")
        print("=" * 60)
        
        # Open camera
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {self.camera_index}")
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("\nCamera opened successfully!")
        print("Press Ctrl+C to stop monitoring\n")
        
        # Start threads
        self.stop_event.clear()
        
        self.capture_thread = Thread(target=self._capture_loop, daemon=True)
        self.process_thread = Thread(target=self._process_loop, daemon=True)
        
        self.capture_thread.start()
        self.process_thread.start()
    
    def stop(self):
        """Stop monitoring."""
        print("\nStopping monitor...")
        self.stop_event.set()
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.process_thread:
            self.process_thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
        
        print("Monitor stopped")
    
    def get_current_metrics(self) -> dict:
        """Get the latest metrics."""
        with self.metrics_lock:
            return self.current_metrics.copy()
    
    def run(self, display_metrics: bool = True, save_log: Optional[str] = None):
        """
        Run the monitor continuously.
        
        Args:
            display_metrics: Print metrics to console
            save_log: Path to save metrics log (JSON)
        """
        self.start()
        
        log_data = []
        
        try:
            while True:
                time.sleep(5)  # Check every 5 seconds
                
                if display_metrics:
                    metrics = self.get_current_metrics()
                    if metrics['timestamp']:
                        print(f"\r[Current] People: {metrics['num_people']} | "
                              f"Danciness: {metrics['danciness']:.2f} | "
                              f"Last update: {metrics['timestamp']}", end='')
                
                if save_log:
                    metrics = self.get_current_metrics()
                    if metrics['timestamp']:
                        log_data.append(metrics)
                        
                        # Save periodically
                        with open(save_log, 'w') as f:
                            json.dump(log_data, f, indent=2)
                
        except KeyboardInterrupt:
            print("\n\nReceived interrupt signal")
        finally:
            self.stop()
            
            if save_log and log_data:
                with open(save_log, 'w') as f:
                    json.dump(log_data, f, indent=2)
                print(f"Metrics log saved to {save_log}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Continuous danceometer monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor with 30s interval (default)
  python danceometer_monitor.py
  
  # Monitor with 15s interval
  python danceometer_monitor.py --interval 15
  
  # Save metrics to log file
  python danceometer_monitor.py --log metrics.json
  
  # Use different camera
  python danceometer_monitor.py --camera 1
  
  # Lower FPS for less CPU usage
  python danceometer_monitor.py --fps 5
        """
    )
    
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device index (default: 0)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Analysis interval in seconds (default: 30)')
    parser.add_argument('--fps', type=int, default=10,
                       help='Buffer capture FPS (default: 10)')
    parser.add_argument('--log', type=str, default=None,
                       help='Path to save metrics log (JSON)')
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                       help='YOLO model size (default: yolov8n.pt)')
    
    args = parser.parse_args()
    
    # Create and run monitor
    monitor = DanceometerMonitor(
        camera_index=args.camera,
        interval=args.interval,
        buffer_fps=args.fps,
        model_size=args.model
    )
    
    monitor.run(display_metrics=True, save_log=args.log)


if __name__ == "__main__":
    main()
