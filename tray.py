import pystray
from PIL import Image, ImageDraw

class TrayController:
    def __init__(self, engine, on_exit=None):
        self.engine = engine
        self.on_exit = on_exit
        self.icon = None
        self._init_tray()

    def _create_icon_image(self, is_recording=False):
        width = 64
        height = 64
        color = (234, 67, 53) if is_recording else (26, 115, 232)
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((4, 4, width - 4, height - 4), fill=color)
        draw.ellipse((22, 16, 42, 38), fill=(255, 255, 255))
        draw.rectangle((26, 30, 38, 44), fill=(255, 255, 255))
        draw.rectangle((30, 44, 34, 52), fill=(255, 255, 255))
        draw.rectangle((24, 50, 40, 54), fill=(255, 255, 255))
        return image

    def _get_status_text(self):
        if self.engine.is_recording:
            if self.engine.mode == "bn_to_en":
                return "Speaking Bangla... Typing English"
            elif self.engine.mode == "en_to_bn":
                return "Speaking English... Typing Bangla"
            return "Listening..."
        return "Ready"

    def _on_toggle_voice(self, icon, item):
        self.engine.toggle()

    def _on_set_normal_bn(self, icon, item):
        self.engine.set_language("bn-BD")
        self.notify("Voice", "Language: Bangla")

    def _on_set_normal_en(self, icon, item):
        self.engine.set_language("en-US")
        self.notify("Voice", "Language: English")

    def _on_set_trans_bn_en(self, icon, item):
        self.engine.set_mode("bn_to_en")
        self.notify("Voice", "Mode: বাংলা ➔ English")

    def _on_set_trans_en_bn(self, icon, item):
        self.engine.set_mode("en_to_bn")
        self.notify("Voice", "Mode: English ➔ বাংলা")

    def _on_quit(self, icon, item):
        self.engine.stop()
        if self.on_exit:
            self.on_exit()
        if self.icon:
            self.icon.stop()

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(lambda text: f"Status: {self._get_status_text()}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda text: "Stop Listening" if self.engine.is_recording else "Start Listening (Alt+V)",
                self._on_toggle_voice,
                default=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Normal: বাংলা (bn-BD)",
                self._on_set_normal_bn,
                checked=lambda item: self.engine.mode == "normal" and self.engine.lang == "bn-BD"
            ),
            pystray.MenuItem(
                "Normal: English (en-US)",
                self._on_set_normal_en,
                checked=lambda item: self.engine.mode == "normal" and self.engine.lang == "en-US"
            ),
            pystray.MenuItem(
                "Translate: বাংলা ➔ English",
                self._on_set_trans_bn_en,
                checked=lambda item: self.engine.mode == "bn_to_en"
            ),
            pystray.MenuItem(
                "Translate: English ➔ বাংলা",
                self._on_set_trans_en_bn,
                checked=lambda item: self.engine.mode == "en_to_bn"
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Voice", self._on_quit)
        )

    def _init_tray(self):
        icon_image = self._create_icon_image(self.engine.is_recording)
        self.icon = pystray.Icon("Voice", icon_image, "Voice Typing", menu=self._build_menu())

    def update_state(self, is_recording, lang, mode):
        if not self.icon:
            return
        self.icon.icon = self._create_icon_image(is_recording)
        self.icon.title = f"Voice: {self._get_status_text()}"
        self.icon.update_menu()

    def notify(self, title, message):
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def run(self):
        if self.icon:
            self.icon.run()
