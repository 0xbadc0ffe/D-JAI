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

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "queue/"

SONO_API_URL = os.getenv("SONO_API_URL")
GPT_API_URL = os.getenv("GPT_API_URL")
GPT_API_KEY = os.getenv("GPT_API_KEY")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/queue")
def view_queue():
    # Detect songs in the songs folder
    songs = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith(".mp3")]
    return render_template("queue.html", queue=songs)


@app.route("/create", methods=["GET", "POST"])
def create_song():
    if request.method == "POST":
        text_prompt = request.form["text_prompt"]
        song_url = generate_song(text_prompt)
        if song_url:
            download_song(song_url)
        return redirect(url_for("index"))
    return render_template("create_song.html")


def generate_song(text_prompt):
    # Step 1: Generate text using GPT
    generated_title,generated_lyrics,generated_tags,generated_prompt = generate_song_info(text_prompt)
    
    # Step 2: Generate song using Suno API
    suno_payload = {
        "prompt": generated_lyrics,
        "title": generated_title,
        "tags" : generated_tags,
        
    }
    suno_response = requests.post(SONO_API_URL, json=suno_payload, headers=headers)
    song_url = suno_response.json().get("song_url")

    return song_url


def generate_song_info(text_prompt):
    # Step 1: Generate text using GPT
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GPT_API_KEY}',
    }
    gpt_payload = {
        "text": text_prompt,
    }

    gpt_response = requests.post(GPT_API_URL, headers=headers, json=gpt_payload)
    gpt_response.raise_for_status()  # Raise an error for bad status codes

    gpt_data = gpt_response.json()
    function_call_result = gpt_data.get('choices', [{}])[0].get('message', {}).get('function_call', {}).get('arguments', '{}')
        
    return title,lyrics,tags,generated_prompt

def download_song(song_url):
    song_data = requests.get(song_url).content
    song_filename = f"{uuid4()}.mp3"
    song_path = os.path.join(app.config["UPLOAD_FOLDER"], song_filename)

    with open(song_path, "wb") as song_file:
        song_file.write(song_data)

    return song_path


@app.route("/songs/<filename>")
def song_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    app.run(debug=True)
