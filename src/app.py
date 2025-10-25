from opcode import opname
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)
import requests
import os
from uuid import uuid4
from dotenv import load_dotenv
import json
import re
import time
import streamer
from danceometer_monitor import DanceometerMonitor

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "queue/"

SUNO_API_URL = os.getenv("SUNO_API_URL")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")
GPT_API_URL = os.getenv("GPT_API_URL")
GPT_API_KEY = os.getenv("GPT_API_KEY")

# Danceometer monitor (global instance)
danceometer_monitor = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/queue")
def view_queue():
    # Detect songs in the songs folder
    #songs = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith(".mp3")]
    try:
        with open(streamer.TRACKQUEUE, "r") as fqueue:
            songs = fqueue.readlines()
        if len(songs)>0:
            songs.pop(0) # first line is always the logging timestamp
    except FileNotFoundError:
        # Detect songs in the songs folder
        songs = streamer.get_songs_list()
    return render_template("queue.html", queue=songs)


def gen_prompt(form):
    text_prompt = form["text_prompt"]
    song_title = form["song_title"]
    genres = form["genres"]
    lang = form["lang"]
    lyrics = form["lyrics"]
    prompt = f"Title: {song_title}\nLanguage: {lang}\nGenres: {genres}\nIdea: {text_prompt}\n\nLyrics:\n{lyrics}"
    return prompt


@app.route("/create", methods=["GET", "POST"])
def create_song():
    if request.method == "POST":
        text_prompt = gen_prompt(request.form)
        song_url, song_info = generate_song(text_prompt)
        if song_url:
            download_song(song_url, song_info)
        return redirect(url_for("index"))
    return render_template("create_song.html")


def generate_song(text_prompt):
    # Step 1: Get dance metrics from monitor
    num_people = 0
    danciness = 0
    
    if danceometer_monitor is not None:
        try:
            metrics = danceometer_monitor.get_current_metrics()
            if metrics['timestamp']:
                num_people = metrics['num_people']
                danciness = metrics['danciness'] / 100.0  # Normalize to 0-1
                print(f"\nDance metrics: {num_people} people, {danciness*100:.1f} danciness")
        except Exception as e:
            print(f"Warning: Could not get dance metrics: {e}")
    
    # Step 2: Generate text using GPT with dance metrics
    song_info = generate_song_info(text_prompt, num_people, danciness)
    generated_title = song_info["title"]
    generated_lyrics = song_info["lyrics"]
    generated_tags = song_info["genres"] 
    generated_idea = song_info["idea"]
    generated_lang = song_info["language"]
    
    # Step 3: Generate song using new Suno API
    print(f"\nGenerating song: {generated_title}")
    print(f"Genres: {generated_tags}")
    
    task_id = suno_generate(
        prompt=generated_lyrics,
        title=generated_title,
        style=generated_tags,
        instrumental=False,
        model="V4_5"
    )
    
    print(f"Task ID: {task_id}")
    print("Waiting for Suno to complete generation...")
    
    # Step 4: Poll for completion and get audio URL
    song_url = wait_for_suno_task(task_id, interval=5, max_wait=180)
    
    print(f"Song ready: {song_url}")
    return song_url, song_info


def parse_text_to_dict(text):
    # Utilizziamo delle espressioni regolari per identificare i campi
    fields = ['Title', 'Language', 'Genres', 'Idea', 'Lyrics']
    pattern = re.compile(r'(' + '|'.join(fields) + r'):\s*(.*?)(?=(?:\n[A-Z][a-z]+:|\Z))', re.DOTALL)
    
    # Troviamo tutti i match nel testo
    matches = pattern.findall(text)
    
    # Creiamo un dizionario con i valori trovati
    result = {field.lower(): '' for field in fields}
    for match in matches:
        field, value = match
        result[field.lower()] = value.strip()
    
    return result



def generate_song_info(text_prompt, num_people=0, danciness=0):

    ROLE_intro = "You are an amazing songwriter assistant and DJ. Giving you some of the following fields [Title, Language, Generes, Idea] you must fill in the missing ones AND provide lyrics with the right language (preferably {}) and coherent with the concpets described by the Idea and the Title (if provided)." 
    ROLE_intro += "You will have access to the number of people on the dance floor and the overall dacniness level (from 0 to 100) to better adapt the song to the evenet atmosphere. Do whatever you can to maximize these values!" 
    lang_bias = "english, italian or spanish"
    lyrics_format = " Divide the lyrics in sections and specify the section type with tags among these: [Intro], [Outro], [Chorus], [Bridge], [Verse], [Pre-Chorus], [Instrumental], [Drop]. Don't get above 1000 characters (counting tags)"
    genres_format = " If the Genres are missing, they must be a list of up to 4 musical genres/musical characteristics that can represent the mood of the Idea (ex: edm, pop, female voice, cool bassline)."
    genre_bias = " Please have a small bias toward \"dancy\"/not \"boring\" genres as you will be deployed to get some background music during an event."
    danciness = f"\nPeople on the dance floor: {num_people}, Danciness level: {danciness*100}. Increse these values by any means possible è.è .\n"
    ans_format = " Answare with the format:\n\nTitle: $Title\nLanguage: $Language\nGenres: $Genre1, $Genre2, ...\n$Idea: $Idea\n\nLyrics:\n$Lyrics."
    
    # Biases overload:
    try:
        with open("./src/biases.json", "r") as jfile:
            jfile = json.load(jfile)   
        lang_bias = jfile["lang_bias"]
        genre_bias = jfile["genre_bias"]
    except FileNotFoundError:
        print("\nBIASES JSON FILE NOT FOUND")

    if not genre_bias.endswith(".") and genre_bias.strip(" ")!= "":
        genre_bias += "."

    ROLE = ROLE_intro.format(lang_bias) + lyrics_format + genres_format + genre_bias + danciness + ans_format


    # Step 1: Generate text using GPT

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GPT_API_KEY}',
    }

    gpt_payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": ROLE
            },
            {
                "role": "user",
                "content": text_prompt
            }
        ]
    }

    gpt_response = requests.post(GPT_API_URL, headers=headers, json=gpt_payload)
    gpt_response.raise_for_status()  # Raise an error for bad status codes
    answ = gpt_response.json()['choices'][0]['message']['content'] 

    print("\n\n@GPT:\n") #TODO: log
    print(answ)

    song_info = parse_text_to_dict(answ)
    song_info["raw"] = answ

    return song_info


def suno_generate(prompt, **kwargs):
    """Submit a generation task to Suno API."""
    payload = {
        "prompt": prompt,
        "customMode": True,
        "model": kwargs.get("model", "V4_5"),
        "instrumental": kwargs.get("instrumental", False),
        "title": kwargs.get("title"),
        "style": kwargs.get("style"),
        "callBackUrl": "https://example.com/callback",  # Placeholder - API requires this
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    print(f"\nSending request to Suno API...")
    print(f"Payload: {payload}")
    
    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    resp = requests.post(
        f"{SUNO_API_URL}/generate",
        headers=headers,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    
    print(f"Response from Suno: {data}")
    
    if data.get("code") != 200:
        raise RuntimeError(f"Suno rejected request: {data}")
    
    task_id = data["data"]["taskId"]
    print(f"Task created with ID: {task_id}")
    return task_id


def wait_for_suno_task(task_id, interval=5, max_wait=180):
    """Poll Suno API until task completes and return audio URL."""
    deadline = time.time() + max_wait
    
    headers = {
        "Authorization": f"Bearer {SUNO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    elapsed = 0
    while time.time() < deadline:
        try:
            resp = requests.get(
                f"{SUNO_API_URL}/generate/record-info",
                params={"taskId": task_id},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()
            
            print(f"\nPolling response: {result}")  # Debug logging
            
            if result.get("code") != 200:
                print(f"API returned non-200 code: {result}")
                raise RuntimeError(f"Suno API error: {result}")
            
            payload = result["data"]
            status = payload["status"]
            
            print(f"[{elapsed}s] Status: {status}")
            
            if status == "SUCCESS":
                # API returns 'sunoData' not 'data'
                tracks = payload["response"]["sunoData"]
                if tracks and len(tracks) > 0:
                    audio_url = tracks[0]["audioUrl"]
                    print(f"Success! Audio URL: {audio_url}")
                    return audio_url
                else:
                    raise RuntimeError("No audio tracks in successful response")
            
            if status == "FAILED":
                error_msg = payload.get("response", {}).get("error", "Unknown error")
                raise RuntimeError(f"Suno task failed: {error_msg}")
            
            # Status is PENDING or PROCESSING
            time.sleep(interval)
            elapsed += interval
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            time.sleep(interval)
            elapsed += interval
    
    raise TimeoutError(f"Suno task timed out after {max_wait}s")


def download_song(song_url, song_info):
    """Download MP3 from URL to queue folder."""
    print(f"\nDownloading {song_url} ...")
    
    # Direct download - URL is already ready from Suno
    song_data = requests.get(song_url, timeout=30)
    song_data.raise_for_status()
    
    song_filename = f"{song_info['title']}.mp3"
    song_path = os.path.join(app.config["UPLOAD_FOLDER"], song_filename)
    
    with open(song_path, "wb") as song_file:
        song_file.write(song_data.content)
    
    print(f"Done [{song_path}]")
    return song_path


@app.route("/songs/<filename>")
def song_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="D-JAI Music Generation Server")
    parser.add_argument('--enable-danceometer', action='store_true',
                       help='Enable danceometer monitoring')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device index (default: 0)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Danceometer analysis interval in seconds (default: 30)')
    args = parser.parse_args()
    
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    
    # Start danceometer if enabled
    if args.enable_danceometer:
        print("\n" + "="*60)
        print("Starting Danceometer Monitor")
        print("="*60)
        print(f"Camera: {args.camera}")
        print(f"Interval: {args.interval}s")
        print("="*60 + "\n")
        
        try:
            danceometer_monitor = DanceometerMonitor(
                camera_index=args.camera,
                interval=args.interval,
                buffer_fps=10
            )
            danceometer_monitor.start()
            print("Danceometer started successfully!\n")
        except Exception as e:
            print(f"Warning: Could not start danceometer: {e}")
            print("Continuing without danceometer...\n")
            danceometer_monitor = None
    else:
        print("\nDanceometer disabled. Use --enable-danceometer to enable.\n")
    
    try:
        app.run(debug=True)
    finally:
        if danceometer_monitor is not None:
            danceometer_monitor.stop()
