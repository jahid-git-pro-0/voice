import sys
import threading
from pynput import keyboard
from engine import VoiceEngine
from injector import TextInjector
from tray import TrayController

def main():
    injector = TextInjector()
    tray_holder = [None]

    def on_speech_result(text):
        injector.inject(text)

    def on_engine_status(is_recording, lang, mode):
        tray = tray_holder[0]
        if tray:
            tray.update_state(is_recording, lang, mode)
            status_desc = "Listening..." if is_recording else "Stopped"
            tray.notify("Voice", f"Voice Typing: {status_desc}")

    engine = VoiceEngine(
        on_result=on_speech_result,
        on_status=on_engine_status
    )

    def on_hotkey_toggle():
        engine.toggle()

    def on_hotkey_switch():
        engine.toggle_mode_or_lang()
        tray = tray_holder[0]
        if tray:
            curr_mode = engine.mode
            curr_lang = engine.lang
            mode_text = "Bangla" if curr_lang == "bn-BD" and curr_mode == "normal" else "English" if curr_mode == "normal" else "বাংলা ➔ EN" if curr_mode == "bn_to_en" else "EN ➔ বাংলা"
            tray.notify("Voice", f"Switched to: {mode_text}")

    hotkeys = keyboard.GlobalHotKeys({
        "<alt>+v": on_hotkey_toggle,
        "<alt>+l": on_hotkey_switch
    })

    hotkey_thread = threading.Thread(target=hotkeys.run, daemon=True)
    hotkey_thread.start()

    def on_app_exit():
        try:
            hotkeys.stop()
        except Exception:
            pass
        sys.exit(0)

    tray = TrayController(engine=engine, on_exit=on_app_exit)
    tray_holder[0] = tray
    tray.run()

if __name__ == "__main__":
    main()
