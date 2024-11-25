from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.lang import Builder

Builder.load_file("main_screen.kv")
Builder.load_file("transcription_screen.kv")
Builder.load_file("settings_screen.kv")


class MainScreen(Screen):
    pass


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
