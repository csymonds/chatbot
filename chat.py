import sys
import warnings
import brain
import utils
import keyboard
import openai
from pydub import AudioSegment
from scipy.io.wavfile import write
import sounddevice as sd
import numpy as np
from queue import Queue
import threading
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from enum import Enum, auto

class Model(Enum):
    hf = auto()
    oai = auto()

# Define the model to use
using_model = Model.oai

# Set OpenAI API Key
openai.api_key = utils.open_file('key_openai.txt')

# Define the control state of the app
app_running = True
ignore_warnings = True

# Define the listening state
listening = False

# Define the "push to talk" key
ptt_key = 'z'

# Set the sampling rate (number of samples per second)
sr = 16000

# Set a signal floor to identify "silence"
signal_floor = 0.003

# Create an output array to store the recorded audio
out = np.zeros((0, 1))

# Create a processing queue
q = Queue()

def startListening():
    """
    This function handles starting the listening process. It records audio data and 
    adds it to the processing queue when the 'push to talk' key is held down.
    """
    global listening, out, q
    device_info = sd.query_devices(sd.default.device, 'input')
    print(f"Started listening on device: {device_info['name']}")
    with sd.Stream(channels=1, callback=audio_callback, blocksize=2048, samplerate=sr):
        while listening:
            pass

    out_copy = np.copy(out)  # Deep copy the out array
    q.put(out_copy)
    q.put(None)
    out = np.zeros((0, 1))  # Reset the out array to an empty array


def on_key_event(key):
    """
    This function handles key events. It starts the listening process when the 'push to talk' key is held down,
    and it stops the process when the key is released.
    """
    global listening, app_running

    if (listening==False and key.name == ptt_key and key.event_type == keyboard.KEY_DOWN):
        listening=True
        threading.Thread(target=startListening).start()
    if (key.name == ptt_key and key.event_type == keyboard.KEY_UP):
        listening=False
    elif (key.name == 'esc' and key.event_type == keyboard.KEY_UP):
        app_running=False

def audio_callback(indata, outdata, frames, time, status):
    """
    This function handles incoming audio. The audio data is added to the output array.
    Note: only 2 args are used, but all are required for the callback to work.
    """
    global out, listening

    # Check for and print any errors
    if status:
        print(status, file=sys.stderr)

    if listening:
        data = indata.T.reshape(-1,)
        out = np.concatenate((out, data)) if len(out) > 0 else data
    else:
        out = np.zeros((0, 1))  # Reset the out array if not listening


def process_output():
    """
    This function handles processing the output arrays from the queue. The audio data is transcribed using a model,
    and the transcribed text is used as input to a chatbot.
    """
    global listening, app_running, sr, q, using_model

    processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en")

    print("\nHold " + ptt_key + " key to talk to CodeBot")
    print("Press ESC any time to quit\n\nUSER: ")

    while app_running:
        while listening:
            sample = q.get()
            if sample is None:
                break
            if len(sample) == 0:
                continue
            if using_model == Model.hf:
                input_features = processor(sample, sampling_rate=sr, return_tensors="pt").input_features
                predicted_ids = model.generate(input_features)
                transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
                if transcription[0].strip().lower() != "you":
                    prompt = transcription[0]
                    print(prompt)
            elif using_model == Model.oai:
                wav_file = "output.wav"
                write(wav_file, sr, sample)
                mp3_file = "output.mp3"
                sound = AudioSegment.from_file(wav_file, format="wav")
                sound.export(mp3_file, format="mp3")
                with open(mp3_file, "rb") as audio_file:
                    transcript = openai.Audio.transcribe("whisper-1", audio_file)
                    prompt = transcript["text"]
                    print(prompt)
            brain.chat(prompt)
            print("\nUSER: ")

if ignore_warnings:
    warnings.filterwarnings("ignore")

utils.clear()

processing_thread = threading.Thread(target=process_output)
processing_thread.start()

brain.init()
print("Welcome to CodeBot!")

keyboard.hook(on_key_event, suppress=False)

keyboard.wait('esc')

processing_thread.join()
