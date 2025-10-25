# What's New - Danceometer Branch

## Branch: `danceometer`

This branch contains two major features added on 2025-10-25:

---

## 🕺 1. Danceometer - Dance Activity Detection

**What it does:** Analyzes camera feed to detect number of people and how much they're dancing.

**Files:**
- `src/danceometer.py` - Core detection module using YOLOv8
- `src/danceometer_monitor.py` - Continuous monitoring (runs every T seconds)
- `src/test_danceometer.py` - Test suite
- `src/example_integration.py` - Integration examples
- `DANCEOMETER_README.md` - Full documentation

**Quick Start:**
```bash
# Test it works
python src/test_danceometer.py --unit

# Monitor camera (30s intervals)
python src/danceometer_monitor.py

# Monitor with custom interval
python src/danceometer_monitor.py --interval 15

# Save metrics to log
python src/danceometer_monitor.py --log log/dance_metrics.json
```

**Use in code:**
```python
from danceometer_monitor import DanceometerMonitor

monitor = DanceometerMonitor(interval=30, buffer_fps=10)
monitor.start()

# Get metrics anytime
metrics = monitor.get_current_metrics()
# {'num_people': 5, 'danciness': 42.3, 'timestamp': '...'}
```

**How it works:**
- Uses YOLOv8 to detect people
- Tracks movement between frames
- Outputs:
  - `num_people`: Count of detected people
  - `danciness`: 0-100 score of movement activity

**Future use:** These metrics can bias music generation (tempo, energy, genre).

---

## 🎵 2. New Suno API Integration

**What changed:** Migrated from old Suno API to new official API.

**Files:**
- `src/app.py` - Updated with new API calls
- `src/.env` - Added `SUNO_API_KEY`
- `test_suno_api.py` - API connection test
- `SUNO_API_MIGRATION.md` - Migration details

**Key differences:**

| Old | New |
|-----|-----|
| POST `/api/custom_generate` | POST `/generate` |
| Get song ID, construct CDN URL | Get task ID, poll for completion |
| Poll CDN until 200 | Poll `/generate/record-info` |
| No auth header needed | Bearer token required |

**New flow:**
1. Submit generation → get `taskId`
2. Poll status endpoint
3. Wait for `SUCCESS` status
4. Get `audio_url` from response
5. Download MP3

**Testing:**
```bash
python test_suno_api.py
```

---

## 📦 Dependencies Added

Updated `requirements.txt`:
```
ultralytics      # YOLO models
opencv-python    # Camera/video processing
```

Install with:
```bash
pip install ultralytics opencv-python
```

---

## 🚀 Quick Commands

```bash
# 1. Monitor camera for dance activity
python src/danceometer_monitor.py

# 2. Start music streaming (existing)
python src/streamer.py

# 3. Start web interface (existing, now with new Suno API)
python src/app.py

# 4. Test danceometer
python src/test_danceometer.py --unit

# 5. Test Suno API
python test_suno_api.py
```

---

## 🔮 Future Integration Ideas

The danceometer metrics can be integrated into music generation:

```python
# Pseudo-code concept
metrics = monitor.get_current_metrics()

if metrics['danciness'] > 70:
    generate_song(genres="EDM, techno", tempo=140)
elif metrics['danciness'] < 30:
    generate_song(genres="ambient, chill", tempo=100)

# Adjust volume based on crowd size
volume = base_volume + (metrics['num_people'] * 2)
```

See `src/example_integration.py` for full examples.

---

## 📚 Documentation

- **Danceometer:** See `DANCEOMETER_README.md`
- **Suno API:** See `SUNO_API_MIGRATION.md`
- **Integration examples:** Run `python src/example_integration.py`

---

## ✅ Status

- ✅ Danceometer implemented and tested
- ✅ Continuous monitoring working
- ✅ Suno API migrated
- ✅ API connection validated
- ⏳ Full song generation test (awaits user test to preserve credits)
- 🔮 Integration between danceometer and music generation (future)

---

**Created:** 2025-10-25  
**Branch:** `danceometer`  
**Ready for:** Testing and integration
