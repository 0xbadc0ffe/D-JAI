"""
Danceometer module for detecting people and estimating dance activity.
Uses YOLOv8 for person detection and movement tracking for danciness estimation.
"""

import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
from typing import Tuple, Optional


class Danceometer:
    """
    Analyzes video input to detect number of people and their dancing activity.
    
    Outputs:
        - number_of_people: Count of detected people in current frame
        - danciness: Metric (0-100) indicating how much people are moving/dancing
    """
    
    def __init__(self, model_size: str = 'yolov8n.pt'):
        """
        Initialize the Danceometer with a YOLO model.
        
        Args:
            model_size: YOLO model to use (yolov8n.pt, yolov8s.pt, etc.)
                       'n' is nano (fastest), 's' is small, 'm' is medium
        """
        self.model = YOLO(model_size)
        self.prev_positions = {}  # Track person positions across frames
        self.movement_history = defaultdict(list)  # Store movement history
        self.frame_count = 0
        self.max_history = 30  # Keep last 30 frames of movement data
        
    def _calculate_movement(self, current_positions: dict, prev_positions: dict) -> float:
        """
        Calculate movement score based on position changes between frames.
        
        Args:
            current_positions: Dict of {person_id: (x, y, w, h)}
            prev_positions: Dict of {person_id: (x, y, w, h)} from previous frame
            
        Returns:
            Movement score (0-100)
        """
        if not prev_positions or not current_positions:
            return 0.0
        
        total_movement = 0.0
        matched_people = 0
        
        # Match people between frames based on position proximity
        for curr_id, curr_bbox in current_positions.items():
            cx1, cy1, w1, h1 = curr_bbox
            
            # Find closest match in previous frame
            min_dist = float('inf')
            matched_bbox = None
            
            for prev_id, prev_bbox in prev_positions.items():
                cx2, cy2, w2, h2 = prev_bbox
                dist = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                
                if dist < min_dist and dist < 200:  # Max matching distance
                    min_dist = dist
                    matched_bbox = prev_bbox
            
            if matched_bbox is not None:
                # Calculate normalized movement
                cx2, cy2, w2, h2 = matched_bbox
                movement = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                
                # Normalize by bbox size (larger people move more pixels for same motion)
                avg_size = (w1 + h1 + w2 + h2) / 4
                normalized_movement = movement / (avg_size + 1e-6)
                
                total_movement += normalized_movement
                matched_people += 1
        
        if matched_people == 0:
            return 0.0
        
        # Average movement per person, scaled to 0-100 range
        avg_movement = total_movement / matched_people
        # Scale factor: empirically chosen, movement of ~5 normalized units = high dancing
        danciness = min(100.0, avg_movement * 20.0)
        
        return danciness
    
    def process_frame(self, frame: np.ndarray) -> Tuple[int, float]:
        """
        Process a single frame and return metrics.
        
        Args:
            frame: Input frame (BGR image from cv2)
            
        Returns:
            Tuple of (number_of_people, danciness)
        """
        # Run YOLO detection
        results = self.model(frame, classes=[0], verbose=False)  # class 0 is 'person'
        
        # Extract person detections
        current_positions = {}
        boxes = results[0].boxes
        
        for idx, box in enumerate(boxes):
            # Get bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            
            if conf > 0.5:  # Confidence threshold
                # Calculate center and size
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                w = x2 - x1
                h = y2 - y1
                
                current_positions[idx] = (cx, cy, w, h)
        
        # Calculate number of people
        number_of_people = len(current_positions)
        
        # Calculate danciness based on movement
        danciness = 0.0
        if self.frame_count > 0:
            danciness = self._calculate_movement(current_positions, self.prev_positions)
            
            # Add to history
            self.movement_history[self.frame_count] = danciness
            
            # Smooth danciness over recent frames
            recent_frames = list(self.movement_history.keys())[-self.max_history:]
            if recent_frames:
                danciness = np.mean([self.movement_history[f] for f in recent_frames])
        
        # Update tracking
        self.prev_positions = current_positions
        self.frame_count += 1
        
        return number_of_people, danciness
    
    def process_video(self, video_source: int | str = 0, display: bool = True) -> None:
        """
        Process video from camera or file and display metrics in real-time.
        
        Args:
            video_source: Camera index (0 for default webcam) or path to video file
            display: Whether to display the video with annotations
        """
        cap = cv2.VideoCapture(video_source)
        
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video source: {video_source}")
        
        print("Starting danceometer... Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                num_people, danciness = self.process_frame(frame)
                
                # Display metrics
                print(f"People: {num_people} | Danciness: {danciness:.2f}", end='\r')
                
                if display:
                    # Add text overlay
                    cv2.putText(frame, f"People: {num_people}", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Danciness: {danciness:.1f}", (10, 70),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Draw bounding boxes
                    results = self.model(frame, classes=[0], verbose=False)
                    annotated_frame = results[0].plot()
                    
                    cv2.imshow('Danceometer', annotated_frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            if display:
                cv2.destroyAllWindows()
            print("\nDanceometer stopped.")
    
    def get_metrics_from_video(self, video_path: str, 
                               sample_rate: int = 5) -> Tuple[float, float]:
        """
        Process an entire video and return average metrics.
        
        Args:
            video_path: Path to video file
            sample_rate: Process every Nth frame (for efficiency)
            
        Returns:
            Tuple of (avg_number_of_people, avg_danciness)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        people_counts = []
        danciness_scores = []
        frame_num = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_num % sample_rate == 0:
                    num_people, danciness = self.process_frame(frame)
                    people_counts.append(num_people)
                    danciness_scores.append(danciness)
                
                frame_num += 1
                
        finally:
            cap.release()
        
        avg_people = np.mean(people_counts) if people_counts else 0
        avg_danciness = np.mean(danciness_scores) if danciness_scores else 0
        
        return avg_people, avg_danciness
    
    def reset(self):
        """Reset tracking state."""
        self.prev_positions = {}
        self.movement_history = defaultdict(list)
        self.frame_count = 0


if __name__ == "__main__":
    # Example usage
    danceometer = Danceometer()
    
    # For webcam (default camera)
    danceometer.process_video(0, display=True)
    
    # For video file
    # danceometer.process_video("path/to/video.mp4", display=True)
