"""
Test script for the Danceometer module.
Tests person detection and danciness estimation with webcam or video file.
"""

import sys
import argparse
from danceometer import Danceometer


def test_webcam():
    """Test danceometer with webcam."""
    print("=" * 50)
    print("Testing Danceometer with Webcam")
    print("=" * 50)
    print("\nInitializing danceometer...")
    
    danceometer = Danceometer(model_size='yolov8n.pt')
    
    print("Opening webcam (press 'q' to quit)...\n")
    try:
        danceometer.process_video(video_source=0, display=True)
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure your webcam is connected and accessible.")
        return False
    
    print("\nWebcam test completed successfully!")
    return True


def test_video_file(video_path: str):
    """Test danceometer with a video file."""
    print("=" * 50)
    print("Testing Danceometer with Video File")
    print("=" * 50)
    print(f"\nVideo path: {video_path}")
    print("Initializing danceometer...")
    
    danceometer = Danceometer(model_size='yolov8n.pt')
    
    print("Processing video (press 'q' to quit early)...\n")
    try:
        danceometer.process_video(video_source=video_path, display=True)
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the video file exists and is accessible.")
        return False
    
    print("\nVideo file test completed successfully!")
    return True


def test_batch_analysis(video_path: str):
    """Test batch analysis of a video file."""
    print("=" * 50)
    print("Testing Batch Analysis")
    print("=" * 50)
    print(f"\nVideo path: {video_path}")
    print("Initializing danceometer...")
    
    danceometer = Danceometer(model_size='yolov8n.pt')
    
    print("Analyzing video (no display)...\n")
    try:
        avg_people, avg_danciness = danceometer.get_metrics_from_video(
            video_path, 
            sample_rate=5
        )
        
        print(f"\nResults:")
        print(f"  Average number of people: {avg_people:.2f}")
        print(f"  Average danciness: {avg_danciness:.2f}/100")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure the video file exists and is accessible.")
        return False
    
    print("\nBatch analysis test completed successfully!")
    return True


def run_all_tests():
    """Run quick unit tests."""
    print("=" * 50)
    print("Running Unit Tests")
    print("=" * 50)
    
    # Test 1: Initialization
    print("\n[Test 1] Testing initialization...")
    try:
        danceometer = Danceometer()
        print("✓ Danceometer initialized successfully")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False
    
    # Test 2: Check model
    print("\n[Test 2] Testing YOLO model...")
    try:
        import numpy as np
        # Create a dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results = danceometer.model(dummy_frame, verbose=False)
        print("✓ YOLO model working")
    except Exception as e:
        print(f"✗ YOLO model test failed: {e}")
        return False
    
    # Test 3: Process frame
    print("\n[Test 3] Testing frame processing...")
    try:
        num_people, danciness = danceometer.process_frame(dummy_frame)
        assert num_people >= 0, "Number of people should be non-negative"
        assert 0 <= danciness <= 100, "Danciness should be between 0 and 100"
        print(f"✓ Frame processed: {num_people} people, danciness {danciness:.2f}")
    except Exception as e:
        print(f"✗ Frame processing failed: {e}")
        return False
    
    # Test 4: Reset
    print("\n[Test 4] Testing reset...")
    try:
        danceometer.reset()
        assert danceometer.frame_count == 0, "Frame count should be 0 after reset"
        print("✓ Reset successful")
    except Exception as e:
        print(f"✗ Reset failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("All unit tests passed! ✓")
    print("=" * 50)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test the Danceometer module",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run unit tests
  python test_danceometer.py --unit
  
  # Test with webcam
  python test_danceometer.py --webcam
  
  # Test with video file
  python test_danceometer.py --video path/to/video.mp4
  
  # Batch analysis of video
  python test_danceometer.py --batch path/to/video.mp4
        """
    )
    
    parser.add_argument('--unit', action='store_true',
                       help='Run unit tests')
    parser.add_argument('--webcam', action='store_true',
                       help='Test with webcam')
    parser.add_argument('--video', type=str,
                       help='Path to video file for testing')
    parser.add_argument('--batch', type=str,
                       help='Path to video file for batch analysis')
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any([args.unit, args.webcam, args.video, args.batch]):
        parser.print_help()
        print("\n" + "=" * 50)
        print("Quick Start: Run unit tests first")
        print("=" * 50)
        print("Command: python test_danceometer.py --unit\n")
        sys.exit(0)
    
    success = True
    
    # Run tests based on arguments
    if args.unit:
        success = success and run_all_tests()
    
    if args.webcam:
        success = success and test_webcam()
    
    if args.video:
        success = success and test_video_file(args.video)
    
    if args.batch:
        success = success and test_batch_analysis(args.batch)
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("All tests completed successfully! ✓")
    else:
        print("Some tests failed. Check the output above.")
    print("=" * 50)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
