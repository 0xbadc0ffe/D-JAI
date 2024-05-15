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
    song_info = generate_song_info(text_prompt) 
    generated_title = song_info["title"]
    generated_lyrics = song_info["lyrics"]
    generated_tags = song_info["genres"] 
    generated_idea = song_info["idea"]
    generated_lang = song_info["language"]
    
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

    ROLE_intro = "You are an amazing songwriter assistant and DJ. Giving you some of the following fields [Title, Language, Generes, Idea] you must fill in the missing ones AND provide lyrics with the right language (preferably english, italian or spanish) and coherent with the concpets described by the Idea and the Title (if provided)." 
    lyrics = " Divide the lyrics in sections and specify the section type with tags among these: [Intro], [Outro], [Chorus], [Bridge], [Verse], [Pre-Chorus], [Instrumental], [Drop]. Don't get above 1000 characters (counting tags)"
    genres = " If the Genres are missing, they must be a list of up to 4 musical genres/musical characteristics that can represent the mood of the Idea (ex: edm, pop, female voice, cool bassline)."
    genre_bias = " Please have a small bias toward \"dancy\"/not \"boring\" genres as you will be deployed to get some background music during an event."
    ans_format = " Answare with the format:\n\nTitle: $Title\nLanguage: $Language\nGenres: $Genre1, $Genre2, ...\n$Idea: $Idea\n\nLyrics:\n$Lyrics."
    ROLE = ROLE_intro + lyrics + genres+ genre_bias + ans_format


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

    pattern = re.compile(r"Title: (.*)\nLanguage: (.*)\nGenres: (.*)\nIdea: (.*)")
    match = pattern.search(answ)
    lyr = re.search("Lyrics:", answ)
    song_info = {
        "title": match[0],
        "language": match[1],
        "genres": match[2],
        "idea": match[3],
        "lyrics": answ[lyr.start()+7:]
    }

    return song_info


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
