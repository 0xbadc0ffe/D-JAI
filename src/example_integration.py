"""
Example: How to integrate danceometer monitor with music generation.
This shows how to read metrics and use them to bias music creation.
"""

import time
from danceometer_monitor import DanceometerMonitor


def example_basic_monitoring():
    """Basic example: Just monitor and print metrics."""
    print("Example 1: Basic Monitoring")
    print("-" * 50)
    
    # Create monitor with 10s interval
    monitor = DanceometerMonitor(interval=10, buffer_fps=5)
    monitor.start()
    
    try:
        # Monitor for 30 seconds
        for i in range(6):
            time.sleep(5)
            metrics = monitor.get_current_metrics()
            
            if metrics['timestamp']:
                print(f"\nMetrics update {i+1}:")
                print(f"  People: {metrics['num_people']}")
                print(f"  Danciness: {metrics['danciness']}")
                print(f"  Time: {metrics['timestamp']}")
    
    finally:
        monitor.stop()


def example_music_bias_integration():
    """
    Example: Use metrics to determine music generation parameters.
    This simulates how you'd integrate with the music generation system.
    """
    print("\nExample 2: Music Generation Integration")
    print("-" * 50)
    
    # Create monitor
    monitor = DanceometerMonitor(interval=30, buffer_fps=10)
    monitor.start()
    
    try:
        print("\nWaiting 30s for first metrics...\n")
        time.sleep(30)
        
        # Main loop: Check metrics and adjust music
        for cycle in range(5):
            print(f"\n{'='*60}")
            print(f"Music Generation Cycle {cycle + 1}")
            print('='*60)
            
            # Get current dance metrics
            metrics = monitor.get_current_metrics()
            
            if not metrics['timestamp']:
                print("No metrics yet, using defaults...")
                num_people = 0
                danciness = 0
            else:
                num_people = metrics['num_people']
                danciness = metrics['danciness']
                print(f"Current metrics: {num_people} people, {danciness:.1f} danciness")
            
            # Determine music parameters based on metrics
            music_params = calculate_music_params(num_people, danciness)
            
            print(f"\nMusic parameters:")
            print(f"  Energy level: {music_params['energy']}")
            print(f"  Tempo: {music_params['tempo']} BPM")
            print(f"  Genre bias: {music_params['genre']}")
            print(f"  Volume: {music_params['volume']}%")
            
            # Here you would call your music generation
            # generate_song(music_params)
            print(f"\n→ Generating music with these parameters...")
            
            # Wait for next interval
            time.sleep(30)
    
    finally:
        monitor.stop()


def calculate_music_params(num_people: float, danciness: float) -> dict:
    """
    Convert dance metrics to music generation parameters.
    
    Args:
        num_people: Average number of people
        danciness: Dance activity level (0-100)
    
    Returns:
        Dictionary with music parameters
    """
    # Energy mapping (0-100 scale)
    # Low danciness = chill, high danciness = energetic
    energy = min(100, int(danciness * 1.5))  # Boost danciness to energy
    
    # Tempo mapping (BPM)
    base_tempo = 100
    if danciness < 20:
        tempo = base_tempo + 0  # 100 BPM - chill
    elif danciness < 40:
        tempo = base_tempo + 20  # 120 BPM - moderate
    elif danciness < 60:
        tempo = base_tempo + 30  # 130 BPM - upbeat
    else:
        tempo = base_tempo + 40  # 140+ BPM - high energy
    
    # Genre selection based on danciness
    if danciness < 25:
        genre = "ambient, chill"
    elif danciness < 50:
        genre = "pop, indie"
    elif danciness < 75:
        genre = "dance, electronic"
    else:
        genre = "EDM, techno"
    
    # Volume based on number of people
    base_volume = 70
    volume = min(100, int(base_volume + (num_people * 2)))
    
    return {
        'energy': energy,
        'tempo': tempo,
        'genre': genre,
        'volume': volume,
        'crowd_size': num_people,
        'danciness': danciness
    }


def example_save_to_log():
    """Example: Monitor and save to log file for later analysis."""
    print("\nExample 3: Save Metrics to Log")
    print("-" * 50)
    
    monitor = DanceometerMonitor(interval=15, buffer_fps=8)
    
    print("\nMonitoring for 60s and saving to log/dance_metrics.json")
    print("Press Ctrl+C to stop early\n")
    
    monitor.run(display_metrics=True, save_log='log/dance_metrics.json')


def example_programmatic_access():
    """Example: Access metrics programmatically in real-time."""
    print("\nExample 4: Programmatic Access")
    print("-" * 50)
    
    monitor = DanceometerMonitor(interval=5, buffer_fps=5)
    monitor.start()
    
    try:
        print("\nMonitoring and reacting to changes...\n")
        
        previous_danciness = 0
        
        for i in range(20):
            time.sleep(2)
            metrics = monitor.get_current_metrics()
            
            if metrics['timestamp']:
                current_danciness = metrics['danciness']
                
                # Detect significant changes
                if abs(current_danciness - previous_danciness) > 10:
                    print(f"\n🎵 DANCINESS CHANGE DETECTED!")
                    print(f"   {previous_danciness:.1f} → {current_danciness:.1f}")
                    print(f"   → Consider adjusting music energy!")
                
                previous_danciness = current_danciness
                
                # Show status
                print(f"\r[{i+1}/20] People: {metrics['num_people']} | "
                      f"Danciness: {current_danciness:.1f}", end='')
    
    finally:
        monitor.stop()


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("DANCEOMETER INTEGRATION EXAMPLES")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        if example == "1":
            example_basic_monitoring()
        elif example == "2":
            example_music_bias_integration()
        elif example == "3":
            example_save_to_log()
        elif example == "4":
            example_programmatic_access()
        else:
            print(f"Unknown example: {example}")
    else:
        print("\nAvailable examples:")
        print("  1 - Basic monitoring")
        print("  2 - Music generation integration")
        print("  3 - Save to log file")
        print("  4 - Programmatic access with change detection")
        print("\nUsage: python example_integration.py [1-4]")
        print("\nRunning example 2 (Music Generation Integration)...")
        print()
        
        example_music_bias_integration()
