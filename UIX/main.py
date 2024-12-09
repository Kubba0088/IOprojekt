import os
import pyaudio
import json
import time
from vosk import Model, KaldiRecognizer
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.lang import Builder
from threading import Thread
from kivy.clock import Clock

model_path = "C:/Users/Kubba008/Desktop/vosk/vosk-model-small-pl-0.22"

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()

input_device_index = 1

final_transcription = ""
last_speech_time = time.time()

PAUSE_THRESHOLD = 3

Builder.load_file("main_screen.kv")
Builder.load_file("transcription_screen.kv")
Builder.load_file("settings_screen.kv")


class MainScreen(Screen):
    def start_transcription(self):
        transcription_screen = self.manager.get_screen('transcription')
        transcription_screen.transcription_text = "Transkrypcja w toku..."

        transcription_thread = Thread(target=self.transcribe_audio, args=(transcription_screen,))
        transcription_thread.daemon = True
        transcription_thread.start()

    def transcribe_audio(self, transcription_screen):
        global final_transcription, last_speech_time

        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                            input=True, input_device_index=input_device_index,
                            frames_per_buffer=8000)
        except Exception as e:
            error_message = f"Nie można otworzyć strumienia audio: {e}"
            print(error_message)
            Clock.schedule_once(lambda dt: setattr(transcription_screen, 'transcription_text', error_message))
            return

        print("Nasłuchuję...")

        while True:
            try:
                data = stream.read(4000, exception_on_overflow=False)
            except Exception as e:
                error_message = f"Błąd podczas czytania strumienia audio: {e}"
                print(error_message)
                Clock.schedule_once(lambda dt: setattr(transcription_screen, 'transcription_text', error_message))
                continue

            if len(data) == 0:
                continue

            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                result_json = json.loads(result)

                if 'text' in result_json and result_json['text']:
                    final_transcription += " " + result_json['text']
                    Clock.schedule_once(lambda dt, text=final_transcription: self.update_transcription(transcription_screen, text))
                    last_speech_time = time.time()

            else:
                result = recognizer.PartialResult()
                result_json = json.loads(result)

                if 'partial' in result_json and result_json['partial']:
                    partial_text = result_json['partial']
                    Clock.schedule_once(lambda dt, text=partial_text: self.update_partial_transcription(transcription_screen, text))
                    last_speech_time = time.time()

            if time.time() - last_speech_time > PAUSE_THRESHOLD:
                if final_transcription.strip():
                    final_transcription += ".\n"
                    Clock.schedule_once(lambda dt, text=final_transcription.strip(): self.display_final_transcription(transcription_screen, text))
                    final_transcription = ""
                last_speech_time = time.time()

    def update_transcription(self, transcription_screen, text):
        transcription_screen.transcription_text = text

    def update_partial_transcription(self, transcription_screen, text):
        transcription_screen.transcription_text = text

    def display_final_transcription(self, transcription_screen, text):
        transcription_screen.transcription_text = text


class TranscriptionScreen(Screen):
    transcription_text = StringProperty("Tu pojawi się podgląd transkrypcji.")


class SettingsScreen(Screen):
    def save_settings(self):
        selected_language = self.ids.language_spinner.text
        selected_format = self.ids.format_spinner.text
        max_space = self.ids.max_space_input.text
        selected_quality = self.ids.quality_spinner.text

        print(f"Wybrano język: {selected_language}")
        print(f"Wybrany format zapisu: {selected_format}")
        print(f"Maksymalne miejsce: {max_space} MB")
        print(f"Jakość nagrania: {selected_quality}")


class MeetNotesApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(TranscriptionScreen(name='transcription'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm


if __name__ == "__main__":
    MeetNotesApp().run()
