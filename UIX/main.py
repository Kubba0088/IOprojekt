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
import pyautogui
import pytesseract
from PIL import Image

model_path = "C:/Users/Kubba008/Desktop/vosk/vosk-model-small-pl-0.22" #pobierz se voska i zmien sciezke

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


class TeamsScreenMonitor:
    def __init__(self, output_dir=None, ocr_lang="eng", screenshot_prefix="teams_screenshot"):
        self.output_dir = output_dir if output_dir else os.path.join(os.path.expanduser("~"), "Desktop")
        self.ocr_lang = ocr_lang
        self.screenshot_prefix = screenshot_prefix
        self.saved_texts = set()
        self.screen_number = 1

    def capture_fullscreen(self):
        try:
            screenshot = pyautogui.screenshot()
            screenshot_path = os.path.join(self.output_dir, f"{self.screenshot_prefix}_{self.screen_number}.png")
            screenshot.save(screenshot_path)
            print(f"Zrzut ekranu zapisany: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            print(f"Błąd podczas robienia zrzutu ekranu: {e}")
            return None

    def perform_ocr(self, image_path):
        try:
            if not os.path.exists(image_path):
                print(f"Plik obrazu nie istnieje: {image_path}")
                return ""

            print(f"Otwieranie pliku obrazu: {image_path}")
            raw_text = pytesseract.image_to_string(Image.open(image_path), lang=self.ocr_lang)
            filtered_text = " ".join([word for word in raw_text.split() if len(word) > 2])
            return filtered_text
        except Exception as e:
            print(f"Błąd podczas wykonywania OCR: {e}")
            return ""

    def save_text_to_file(self, text):
        try:
            text_file_path = os.path.join(self.output_dir, "recognized_text.txt")
            with open(text_file_path, 'a', encoding='utf-8') as file:
                file.write(f"\n{'-' * 40}\nZrzut ekranu z {time.ctime()}:\n{text}")
            print(f"Rozpoznany tekst zapisany: {text_file_path}")
        except Exception as e:
            print(f"Błąd podczas zapisywania tekstu do pliku: {e}")

    def process_screen(self):
        print("Robię zrzut i wykonuję OCR...")
        screenshot_path = self.capture_fullscreen()
        if screenshot_path:
            recognized_text = self.perform_ocr(screenshot_path)
            if recognized_text:
                if recognized_text not in self.saved_texts:
                    print(f"Rozpoznany tekst:\n{recognized_text}")
                    self.save_text_to_file(recognized_text)
                    self.saved_texts.add(recognized_text)
                else:
                    print("Ten tekst już został zapisany wcześniej, pomijam.")
            else:
                print("Nie udało się rozpoznać tekstu.")
        else:
            print("Nie udało się zrobić zrzutu ekranu.")

        self.screen_number += 1

    def start_monitoring(self, continue_ocr, sleep_interval=20):
        time.sleep(10)
        while continue_ocr():
            self.process_screen()
            time.sleep(sleep_interval)


class MainScreen(Screen):
    ocr_running = False

    def start_transcription(self):
        transcription_screen = self.manager.get_screen('transcription')
        transcription_screen.transcription_text = "Transkrypcja audio w toku..."

        transcription_thread = Thread(target=self.transcribe_audio, args=(transcription_screen,))
        transcription_thread.daemon = True
        transcription_thread.start()

    def start_ocr(self):
        transcription_screen = self.manager.get_screen('transcription')
        transcription_screen.transcription_text += "\nOCR w toku..."
        self.ocr_running = True

        monitor = TeamsScreenMonitor(output_dir="C:/Users/Kubba008/Desktop/screeny",ocr_lang="eng") #zmien na swoje gdzie beda sie zapisywac screeny
        monitor_thread = Thread(target=monitor.start_monitoring, args=(lambda: self.ocr_running,))
        monitor_thread.daemon = True
        monitor_thread.start()

    def stop_ocr(self):
        self.ocr_running = False

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
                    Clock.schedule_once(
                        lambda dt, text=final_transcription: self.update_transcription(transcription_screen, text))
                    last_speech_time = time.time()

            else:
                result = recognizer.PartialResult()
                result_json = json.loads(result)

                if 'partial' in result_json and result_json['partial']:
                    partial_text = result_json['partial']
                    Clock.schedule_once(
                        lambda dt, text=partial_text: self.update_partial_transcription(transcription_screen, text))
                    last_speech_time = time.time()

            if time.time() - last_speech_time > PAUSE_THRESHOLD:
                if final_transcription.strip():
                    final_transcription += ".\n"
                    Clock.schedule_once(lambda dt, text=final_transcription.strip(): self.display_final_transcription(
                        transcription_screen, text))
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