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
    headers = {"Content-Type": "application/json", "accept": "application/json"}

    gpt_payload = {
        "model": "gpt-3.5-turbo",
        'messages': [{'role': 'user', 'content': text_prompt}],
        'functions': [
            {
                'name': 'generate_song',
                'description': 'Generate song based on the text prompt',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'prompt': {'type': 'string'},
                        'title': {'type': 'string'}
                    },
                    'required': ['prompt', 'title']
                }
            }
        ],
        'function_call': {'name': 'generate_song'}
    }

    gpt_response = requests.post(GPT_API_URL, headers=headers, json=gpt_payload)
    gpt_response.raise_for_status()  # Raise an error for bad status codes

    gpt_data = gpt_response.json()
    function_call_result = gpt_data.get('choices', [{}])[0].get('message', {}).get('function_call', {}).get('arguments', '{}')
    function_call_result = json.loads(function_call_result)
    generated_prompt = function_call_result.get('prompt')
    generated_title = function_call_result.get('title')


    # Step 2: Generate song using Suno API
    suno_payload = {
        "prompt": generated_prompt,
        "title": generated_title,
    }
    suno_response = requests.post(SONO_API_URL, json=suno_payload, headers=headers)
    song_url = suno_response.json().get("song_url")

    return song_url


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
