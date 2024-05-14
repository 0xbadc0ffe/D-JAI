from datetime import datetime
import os, random, subprocess
import subprocess
import time
import numpy as np
import vlc
import platform
import tts 


def clean():
    plat = platform.system()
    if plat == "Windows":
        os.system("cls")
    else:
        os.system("clear")



TRACKSLOG = "../log/tracks_history.log"
TRACKQUEUE = "../log/queue.log"
FOLDERNAME = "../queue"

# TODO
def sanitize_names(songlist):
    return songlist 

# function to retrive the song name from the txt file
def read_tracks_log():
    with open(TRACKSLOG, "r") as fil:
        dataList = fil.readlines()
    dataList = [i.strip("\n") for i in dataList]
    return dataList

# function to reset the txt file
def reset_tracks_log():
    with open(TRACKSLOG, "w") as fil:
        fil.write("")

# log track
def log_track(song):
    with open(TRACKSLOG, "a") as fil:
        fil.write(song+"\n")

def log_queue(queue, curr=None):
    with open(TRACKQUEUE, "w") as fil:
        fil.write(str(datetime.now())+"\n")
        for s, song in enumerate(queue):
            if curr is not None and s==curr:
                fil.write("[ -> PLAYING ] ")
            fil.write(f"{s+1}. " + song + "\n")


def get_songs_list():
    # list containing the song names
    songlist = os.listdir(FOLDERNAME)
    songlist.remove(".gitkeep")
    songlist = sanitize_names(songlist)
    return songlist


def built_queue(reset_tracked=True, MAX=100, shuffle=True):
    
    songlist = get_songs_list()

    if reset_tracked:
        reset_tracks_log()
        playtrack = []
    else:
        playtrack = read_tracks_log()

    # if tracks log is preserved
    # remove the song which is already played from the song list
    for i in songlist:
        i = i.strip("\n")
        if(i in playtrack):
            songlist.remove(i)
    if len(songlist) == 0:
        songlist = get_songs_list()[:MAX]

    if shuffle:
        perm = np.random.permutation(len(songlist))
        songlist = list(np.array(songlist)[perm])

    return songlist

def format_time(T, belowsec=True):
    minutes, seconds = divmod(T, 60)
    #print("{:0>2}:{:05.2f}".format(int(minutes),seconds))
    #return f"{T//60:.0f}:{T%60:.0f}:{(T%1)*100:.0f}"
    if belowsec:
        return "{:0>2}:{:0>2}:{:.0f}".format(int(minutes),int(seconds),(seconds%1)*100)
    else:
        return "{:0>2}:{:0>2}".format(int(minutes),int(seconds))


def playsong(song, next="", do_print=True):
    s = vlc.MediaPlayer(song)
    start = time.time()
    t = 0
    s.play()
    if do_print:
        clean()
    try:
        while True:
            time.sleep(1)
            T = s.get_length()/1000
            t = time.time()-start
            # print(T)
            if do_print:
                print(f"Playing: \"{song.split('/')[-1]}\"      [{format_time(t,belowsec=False)} / {format_time(T,belowsec=False)}]      [next: {next}]", end="\r")
            if t>T:
                break
    except KeyboardInterrupt:
        s.stop()
        raise KeyboardInterrupt
    if do_print:
        print()
    return s


def update_queue(queue):
    songlist = get_songs_list()
    new = set(songlist).difference(set(queue))
    rem = set(queue).difference(set(songlist))
    for r in rem: queue.remove(r)
    return list(new), queue

def playQueue(queue, speaker=None):
    k = 0
    while True:
        priority, queue = update_queue(queue)

        # Add new songs to queue with priority
        if len(priority)>0:
            queue = queue[:k]+priority+queue[k:]

        log_queue(queue, curr=k)
        song = queue[k]
        try:
            if k<len(queue)-1:
                next = f"{queue[k+1]}"
            else:
                next = "END"
            #log_track(f"{datetime.now()} {song}")
            if speaker:
                try:
                    speaker.speak(f"Prossima canzone: {song}")
                except tts.gTTSError:
                    print("ANNOUNCEMENT ERROR")
                    global announcer 
                    announcer = tts.TTS_OFF()
                    speaker = announcer
            log_track(f"{song}")
            sp = playsong(FOLDERNAME+"/"+song, next)
        except KeyboardInterrupt:
            print()
            input("Press Enter to skip")
        k+=1
        if k>=len(queue):
            return




if __name__ == "__main__":
    engine = None
    loop = False
    reset_tracked = True
    writedown = "../queue.txt" #TODO

    instance = vlc.Instance()
    instance.log_unset()

    clean()
    announcer = tts.get_announcer(f"Daje siamo ON")

    input("press Enter to start ...")
    try:
        while True:
            songlist = built_queue(reset_tracked=reset_tracked)
            playQueue(songlist, speaker=announcer)
            if not loop:
                break
            reset_tracked = True
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
    announcer.clean()
    clean()
    print("Bye (o.o)/")
