import os
import pyaudio
import json
import time
from vosk import Model, KaldiRecognizer

# Ścieżka do modelu
model_path = "C:/Users/Kubba008/Desktop/vosk/vosk-model-small-pl-0.22"

# Załaduj model Vosk
if not os.path.exists(model_path):
    print("Model nie jest dostępny, pobierz model")
    exit(1)

model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)

# Inicjalizowanie PyAudio i otwieranie strumienia z urządzenia wejściowego
p = pyaudio.PyAudio()

# Wskazanie ręcznie urządzenia wejściowego, np. "Cable Input" lub inne
input_device_index = 1  # Zmień na odpowiedni numer urządzenia wejściowego

# Otwórz strumień audio
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, input_device_index=input_device_index,
                frames_per_buffer=8000)

print("Nasłuchuję...")

# Zmienna do przechowywania całej transkrypcji
final_transcription = ""
last_speech_time = time.time()  # Ostatni czas, gdy wykryto dźwięk

# Nasłuchiwanie dźwięku i transkrypcja
while True:
    data = stream.read(4000)
    if len(data) == 0:
        continue  # Ignoruj pustą ramkę

    # Przesyłanie danych do rozpoznawania mowy
    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()  # Pełna transkrypcja
        result_json = json.loads(result)

        # Sprawdzenie, czy transkrypcja zawiera tekst
        if result_json['text']:
            final_transcription += " " + result_json['text']  # Dodaj do finalnej transkrypcji
            last_speech_time = time.time()  # Zaktualizuj czas ostatniej mowy

    else:
        result = recognizer.PartialResult()  # Częściowa transkrypcja
        result_json = json.loads(result)

        # Sprawdzenie, czy częściowa transkrypcja zawiera tekst
        if result_json['partial']:
            last_speech_time = time.time()  # Zaktualizuj czas ostatniej mowy

    # Jeśli brak mowy przez 3 sekundy, wyświetl ostateczną transkrypcję
    if time.time() - last_speech_time > 3:
        if final_transcription.strip():
            print("Ostateczna transkrypcja:", final_transcription.strip())
            final_transcription = ""  # Zresetuj transkrypcję po wyświetleniu
        last_speech_time = time.time()  # Resetuj czas ciszy
