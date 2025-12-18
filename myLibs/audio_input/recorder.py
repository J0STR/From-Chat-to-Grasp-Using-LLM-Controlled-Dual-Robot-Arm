import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os
import sys
from multiprocessing.synchronize import Event as EventClass

class AudioRecorder:
    def __init__(self, ):
        self.samplerate = 44100
        sound_file = ("/home/jonas/coding/xArm/myLibs/audio_input/recording.wav")
        self.filename = sound_file
        self.is_recording = False
        self.recording_data = []
        self.start_time = None

    def callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if self.is_recording:
            self.recording_data.append(indata.copy())

    def start_recording(self):
        self.is_recording = True
        self.recording_data = []
        self.start_time = os.times().elapsed

    def stop_recording(self):
        self.is_recording = False
        end_time = os.times().elapsed

        if self.recording_data:
            final_recording = np.concatenate(self.recording_data, axis=0)
            write(self.filename, self.samplerate, final_recording)
            
            duration = (end_time - self.start_time) if self.start_time else 0
            print(f"Recording done ->  Duration: {duration:.2f} seconds.")
        else:
            print("No audio data recorded.")

    def record(self, request_record: EventClass,):       
        try:
            with sd.InputStream(
                samplerate=self.samplerate, 
                channels=2, 
                dtype='int16', 
                callback=self.callback
            ):  
                if request_record.is_set():
                    self.start_recording()
                    while request_record.is_set():
                        # wait while recording...
                        pass
                    self.stop_recording()
                else:
                    pass

        except Exception as e:
            print(f"\nAn error occurred: {e}")