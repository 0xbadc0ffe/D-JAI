# Danceometer + Music Generation Integration

The danceometer is now fully integrated with the music generation system!

## How It Works

When danceometer is enabled, the system:
1. Continuously monitors the camera every T seconds (default 60s)
2. Analyzes dance activity and counts people
3. When you generate a song, it automatically uses the latest metrics
4. GPT receives the metrics and adapts the song to match the crowd energy

## Running the Integrated System

### Option 1: Without Danceometer (Default)
```bash
python src/app.py
```
Music generation works normally without dance metrics.

### Option 2: With Danceometer
```bash
python src/app.py --enable-danceometer
```

This starts both:
- Flask web server at http://127.0.0.1:5000
- Danceometer monitoring in background

### Custom Settings
```bash
# Custom interval (analyze every 15 seconds)
python src/app.py --enable-danceometer --interval 15

# Different camera
python src/app.py --enable-danceometer --camera 1

# Both
python src/app.py --enable-danceometer --camera 1 --interval 20
```

## How Songs Adapt

The GPT prompt now includes:
```
People on the dance floor: X
Danciness level: Y (0-100)
Increase these values by any means possible!
```

GPT will generate:
- **High danciness (>70)**: EDM, techno, high-energy tracks
- **Medium danciness (30-70)**: Pop, dance, electronic
- **Low danciness (<30)**: More chill, ambient tracks to warm up the crowd

## Example Usage Flow

1. **Start the system:**
   ```bash
   python src/app.py --enable-danceometer
   ```

2. **Wait 60 seconds** for first metrics (default interval)

3. **Generate a song** via web interface

4. **GPT sees the crowd state** and adapts:
   ```
   Current metrics: 5 people, 25.0 danciness
   ```

5. **Song is generated** with appropriate energy level

6. **Metrics update** every 60s automatically

## Monitoring Metrics

The console shows periodic updates:
```
============================================================
DANCEOMETER UPDATE
============================================================
👥 People detected: 5.00
💃 Danciness level: 25.00/100
🎬 Frames analyzed: 600
⏱  Analysis time: 12.3s
============================================================
```

When generating songs:
```
============================================================
DANCE FLOOR METRICS
============================================================
👥 People on dance floor: 5
💃 Danciness level: 25.0/100
⏰ Last updated: 2025-10-25T16:30:00
============================================================
```

## Architecture

```
┌─────────────────┐
│   Camera Feed   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Danceometer    │  (Background thread)
│   Monitor       │  - Captures frames
│                 │  - Runs YOLO every 30s
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Latest Metrics │  (Shared state)
│  - num_people   │
│  - danciness    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask /create  │  (Web request)
│   generate_song │  - Reads metrics
│                 │  - Calls GPT
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GPT Prompt    │  (With metrics)
│  + Suno API     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generated Song │
│   (Adaptive!)   │
└─────────────────┘
```

## Troubleshooting

**Camera not found:**
```bash
# Try different camera index
python src/app.py --enable-danceometer --camera 1
```

**Too slow:**
```bash
# Increase interval
python src/app.py --enable-danceometer --interval 60
```

**Want to see metrics:**
Check the console output - it prints metrics when generating songs.

**Disable danceometer:**
Just run without the flag:
```bash
python src/app.py
```

## Performance Notes

- Danceometer runs in separate thread (non-blocking)
- YOLO processes frames every T seconds (not every frame)
- First metric available after T seconds
- Music generation waits for Suno, not danceometer

## Future Enhancements

Possible improvements:
- Save metrics history to database
- Show metrics in web UI
- Real-time metrics dashboard
- Automatic song queueing based on danciness trends
- Volume adjustment based on crowd size

---

**Integrated:** 2025-10-25  
**Status:** Ready for testing!
