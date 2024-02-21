#!/usr/bin/env python3
# server.py
# Author: Ash Collins
# Edited: 2/20/2024
# import smbus
from flask import Flask, render_template, flash
import numpy as np
import simpleaudio as sa
import time
import gpiod

#frequency = 440  # Our played note will be 440 Hz
fs = 44100  # 44100 samples per second
seconds = 20  # Note duration of 3 seconds
numNotes = 17

C4 = 261.63
CS4 = 277.18
D4 = 293.66
DS4 = 311.13
E4 = 329.63
F4 = 349.23
FS4 = 369.99
G4 = 392
GS4 = 415.3
A4 = 440
AS4 = 466.16
B4 = 493.88
C5 = 523.25
CS5 = 554.37
D5 = 587.33
DS5 = 622.25
E5 = 659.25

frequencies = [C4, CS4, D4, DS4, E4, F4, FS4, G4, GS4, A4, AS4, B4, C5, CS5, D5, DS5, E5]
ranges = [4000, 3900, 3800, 3700, 3500, 3350, 3000, 2800, 2500, 2100, 1700, 1300, 1200, 750, 550, 400, 50]
inputF = open('/sys/bus/iio/devices/iio:device0/in_voltage0_raw', "r")
frequency = 0
audios = np.ones(dtype=np.int16, shape=(numNotes, seconds * fs))
CONSUMER = 'sounds'
switchChip = gpiod.Chip('0')
getLines = switchChip.get_lines([30, 31, 5, 13])
getLines.request(consumer=CONSUMER, type=gpiod.LINE_REQ_DIR_IN)
NUM_SONGS = 3
songs = [sa.WaveObject.from_wave_file('Rickroll.wav'), sa.WaveObject.from_wave_file('LateAtNight.wav'), sa.WaveObject.from_wave_file('BlueHair.wav')]
names = ["Never Gonna Give You Up", "Late Night", "Blue Hair"]
curSong = 0
songPlaying = 0
manualInput = False
NUM_RECORD = 200
recording = np.zeros(NUM_RECORD)
rec_times = np.zeros(NUM_RECORD)
record_in = 0

def getIndex(val):
    for i in range(numNotes):
        if val >= ranges[i]:
            return i
    return -1

for i in range(numNotes):
    frequency = frequencies[i]
    # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
    t_short = np.linspace(0, 1/frequency, int(fs/frequency), False)
    #t = np.linspace(0, seconds, seconds * fs, False)

    # Generate a [frequency] Hz sine wave
    note_short = np.sin(frequency*t_short*2*np.pi)
    # Ensure that highest value is in 16-bit range
    note_short = note_short * (2**11 - 1) / np.max(np.abs(note_short))
    note = np.resize(note_short, seconds * fs)
    
    # Convert to 16-bit data
    audios[i] = note.astype(np.int16)


aVal = int(inputF.read())
inputF.seek(0)
frequency = frequencies[getIndex(aVal)]

# Start playback
# play_obj2.stop()
time.sleep(0.3)
play_obj = sa.play_buffer(audios[0], 1, 2, fs)
play_obj.stop()

def playRecording():
    global play_obj
    if play_obj.is_playing():
        play_obj.stop()
        time.sleep(0.3)
    for i in range(record_in):
        if play_obj.is_playing():
            play_obj.stop()
            time.sleep(0.3)
        if recording[i] >= 0:
            play_obj = sa.play_buffer(audios[int(recording[i])], 1, 2, fs)
        time.sleep(rec_times[i])

    play_obj.stop()
    time.sleep(0.3)

app = Flask(__name__)
app.secret_key = "my_key"
@app.route("/")
def index():
    global names
    templateData = {
        'song'  : names[0],
        'play_str'  : "Play",
        'mode_str'  : "Manual"
    }
    return render_template('index.html', **templateData)

@app.route("/<flag>")
def action(flag):
    global curSong
    global play_obj
    global songs
    global names
    global songPlaying
    global manualInput
    global inputF
    global aVal
    global aVal2
    global frequency
    global frequencies
    global getLines
    global audios
    global record_in
    global recording
    if flag == "prev": 
        curSong = (curSong + NUM_SONGS - 1) % NUM_SONGS
        if play_obj.is_playing():
            play_obj.stop()
            time.sleep(0.3)
        play_obj = songs[curSong].play()
        songPlaying = True
        templateData = {
            'song'  : names[curSong],
            'play_str'  : "Pause",
            'mode_str'  : "Manual"
        }
        return render_template('index.html', **templateData)
    if flag == "next":
        curSong = (curSong + 1) % NUM_SONGS
        if play_obj.is_playing():
            play_obj.stop()
            time.sleep(0.3)
        play_obj = songs[curSong].play()
        songPlaying = True
        templateData = {
            'song'  : names[curSong],
            'play_str'  : "Pause",
            'mode_str'  : "Manual"
        }
        return render_template('index.html', **templateData)
    if flag == "play":
        if songPlaying:
            if play_obj.is_playing():
                play_obj.stop()
            songPlaying = False
            templateData = {
                'song'  : names[curSong],
                'play_str'  : "Play",
                'mode_str'  : "Manual"
            }
            return render_template('index.html', **templateData)
        else:
            if play_obj.is_playing():
                play_obj.stop()
                time.sleep(0.3)
            play_obj = songs[curSong].play()
            songPlaying = True
            templateData = {
                'song'  : names[curSong],
                'play_str'  : "Pause",
                'mode_str'  : "Manual"
            }
            return render_template('index.html', **templateData)
    if flag == "playback":
        playRecording()
        templateData = {
            'song'  : names[curSong],
            'play_str'  : "Play",
            'mode_str'  : "Manual"
        }
        return render_template('index.html', **templateData)
    if flag == "mode":
        record = False
        time_start = time.perf_counter()
        time_stop = time.perf_counter()
        prev_in = -1
        while True:
            if getLines.get_values()[1] == 1:
                record = not record
                if record:
                    recording = np.zeros(NUM_RECORD)
                    record_in = 0
                    time_start = time.perf_counter()
                    time_stop = time.perf_counter()
                else:
                    templateData = {
                        'song'  : names[curSong],
                        'play_str'  : "Pause",
                        'mode_str'  : "Manual"
                    }
                    return render_template('index.html', **templateData)
                while getLines.get_values()[1] == 1:
                    pass
            inputF.seek(0)
            aVal = int(inputF.read())
            time.sleep(0.001)
            inputF.seek(0)
            aVal2 = int(inputF.read())
            if aVal != aVal2:
                continue
            index = getIndex(aVal)
            if record and index != prev_in and record_in < NUM_RECORD:
                time_stop = time.perf_counter()
                rec_times[record_in] = time_stop - time_start
                recording[record_in] = prev_in
                record_in += 1
                time_start = time_stop
                prev_in = index
            if index < 0 or aVal <= 30:
                frequency = 0
                play_obj.stop()                    
            if index >= 0 and frequency != frequencies[index] and aVal > 30:
                frequency = frequencies[index]
                # Start playback
                play_obj.stop()
                time.sleep(0.35)
                play_obj = sa.play_buffer(audios[index], 1, 2, fs)
            if getLines.get_values()[0] == 1:
                templateData = {
                    'song'  : names[curSong],
                    'play_str'  : "Pause",
                    'mode_str'  : "Manual"
                }
                return render_template('index.html', **templateData)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=8081, debug=True)