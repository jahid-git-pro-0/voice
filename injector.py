import sys
import time
import pyperclip
from pynput.keyboard import Controller, Key

class TextInjector:
    def __init__(self):
        self.keyboard = Controller()
        self.modifier_key = Key.cmd if sys.platform == "darwin" else Key.ctrl

    def inject(self, text):
        if not text:
            return

        formatted_text = f" {text}"
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        try:
            pyperclip.copy(formatted_text)
            time.sleep(0.03)

            with self.keyboard.pressed(self.modifier_key):
                self.keyboard.press("v")
                self.keyboard.release("v")

            time.sleep(0.05)
        except Exception:
            pass
        finally:
            try:
                if old_clipboard:
                    pyperclip.copy(old_clipboard)
            except Exception:
                pass
