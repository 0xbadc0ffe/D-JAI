import pyttsx3
import gtts
from gtts import gTTS
import streamer as st
import os
gTTSError = gtts.tts.gTTSError


def get_announcer(text="prova prova", cfg_dict={}):
    try:
        announcer = TTS_ON(**cfg_dict)
        #announcer = tts.TTS_OFF()#voice=1)
        announcer.speak(text)
    except gTTSError as e:
        print(f"ANNOUNCEMENT ERROR: {e}")
        announcer = TTS_OFF(**cfg_dict)
        announcer.speak(text)
    return announcer

def sanitize_voice_query(text):
    if "." in text:
        text = "".join(t for t in text.split(".")[:-1])
    return text


class TTS_OFF:

    def __init__(self, rate=None, volume=None, voice=None):
        self.engine = pyttsx3.init()
        if rate is not None:
            self.engine.setProperty('rate', rate)   # e.g. 150
        if volume is not None:
            self.engine.setProperty('volume', volume)    # between 0 and 1
        if voice is not None:
            if type(voice) is str:
                self.engine.setProperty('voice', voice)    
            elif type(voice) is int:
                voices = self.engine.getProperty('voices') #getting details of current voice
                self.engine.setProperty('voice', voices[voice].id)   #changing index, changes voices. o for male, 1 for female

            # self.engine.setProperty('voices', "french")


    def speak(self,text):
        text = sanitize_voice_query(text)
        self.engine.say(text)
        self.engine.runAndWait()

    def clean(self):
        pass
        


class TTS_ON:

    def __init__(self, lang="it", filename='./voice.mp3'):
        self.lang = lang
        self.filename = filename

    def speak(self, text):
        text = sanitize_voice_query(text)
        tts = gTTS(text=text, lang=self.lang)
        tts.save(self.filename)
        st.playsong(self.filename, do_print=False)
        #os.remove(filename)

    def clean(self):
        os.remove(self.filename)