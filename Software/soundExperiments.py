import numpy as np
import simpleaudio as sa
import time

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
ranges = [4000, 3900, 3800, 3700, 3500, 3350, 3100, 2800, 2500, 2100, 1700, 1300, 1200, 750, 550, 400, 50]
inputF = open('/sys/bus/iio/devices/iio:device0/in_voltage0_raw', "r")
frequency = 0
audios = np.ones(dtype=np.int16, shape=(numNotes, seconds * fs))

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
play_obj = sa.play_buffer(audios[i], 1, 2, fs)
play_obj.stop()

firstTime = 1
while True:
    inputF.seek(0)
    aVal = int(inputF.read())
    time.sleep(0.001)
    inputF.seek(0)
    aVal2 = int(inputF.read())
    if aVal != aVal2:
        continue
    index = getIndex(aVal)
    if index < 0 or aVal <= 30:
        frequency = 0
        play_obj.stop()
    if index >= 0 and frequency != frequencies[index] and aVal > 30:
        frequency = frequencies[index]
        # Start playback
        play_obj.stop()
        time.sleep(0.35)
        play_obj = sa.play_buffer(audios[index], 1, 2, fs)
