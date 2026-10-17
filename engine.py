import re
import urllib.parse
import threading
import requests
import speech_recognition as sr

class VoiceEngine:
    def __init__(self, on_result=None, on_status=None):
        self.on_result = on_result
        self.on_status = on_status
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.microphone = None
        self.stop_listening_fn = None
        self.is_recording = False
        self.mode = "normal"
        self.lang = "bn-BD"
        self.translation_cache = {}

    def set_mode(self, mode):
        self.mode = mode
        if self.on_status:
            self.on_status(self.is_recording, self.lang, self.mode)

    def set_language(self, lang):
        self.lang = lang
        self.mode = "normal"
        if self.on_status:
            self.on_status(self.is_recording, self.lang, self.mode)

    def toggle_mode_or_lang(self):
        if self.mode == "normal":
            new_lang = "en-US" if self.lang == "bn-BD" else "bn-BD"
            self.set_language(new_lang)
        else:
            new_mode = "en_to_bn" if self.mode == "bn_to_en" else "bn_to_en"
            self.set_mode(new_mode)

    def translate_text(self, text, from_lang, to_lang):
        if not text or not text.strip():
            return text
        clean_text = text.strip()
        cache_key = f"{from_lang}_{to_lang}_{clean_text.lower()}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        encoded = urllib.parse.quote(clean_text)
        try:
            u1 = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={from_lang}&tl={to_lang}&q={encoded}"
            r1 = requests.get(u1, timeout=5)
            if r1.status_code == 200:
                d1 = r1.json()
                res = ""
                if isinstance(d1, dict) and "sentences" in d1 and isinstance(d1["sentences"], list):
                    res = " ".join([s.get("trans", "") for s in d1["sentences"] if "trans" in s]).strip()
                elif isinstance(d1, list):
                    if len(d1) > 0 and isinstance(d1[0], str):
                        res = " ".join(d1)
                    elif len(d1) > 0 and isinstance(d1[0], list):
                        res = "".join([i[0] for i in d1[0] if i and len(i) > 0 and i[0]])
                if res and res != clean_text:
                    self.translation_cache[cache_key] = res
                    return res
        except Exception:
            pass

        try:
            u2 = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={from_lang}&tl={to_lang}&dt=t&q={encoded}"
            r2 = requests.get(u2, timeout=5)
            if r2.status_code == 200:
                d2 = r2.json()
                if d2 and isinstance(d2, list) and len(d2) > 0 and isinstance(d2[0], list):
                    res = "".join([item[0] for item in d2[0] if item and len(item) > 0 and item[0]]).strip()
                    if res:
                        self.translation_cache[cache_key] = res
                        return res
        except Exception:
            pass

        try:
            u3 = f"https://api.mymemory.translated.net/get?q={encoded}&langpair={from_lang}|{to_lang}"
            r3 = requests.get(u3, timeout=5)
            if r3.status_code == 200:
                d3 = r3.json()
                if "responseData" in d3 and "translatedText" in d3["responseData"]:
                    res = d3["responseData"]["translatedText"].strip()
                    if res and "mymemory" not in res.lower():
                        self.translation_cache[cache_key] = res
                        return res
        except Exception:
            pass

        return clean_text

    def format_bangla_punctuation(self, raw_text):
        if not raw_text:
            return ""
        s = raw_text.strip()
        s = re.sub(r"(^|\s)(কমা|comma)($|\s)", r"\1,\3", s, flags=re.IGNORECASE)
        s = re.sub(r"(^|\s)(দাঁড়ি|দাড়ি|ফুলস্টপ|ফুল স্টপ|full stop)($|\s)", r"\1।\3", s, flags=re.IGNORECASE)
        s = re.sub(r"(^|\s)(প্রশ্নবোধক|প্রশ্নচিহ্ন|কোশ্চেন মার্ক|question mark)($|\s)", r"\1?\3", s, flags=re.IGNORECASE)
        s = re.sub(r"(^|\s)(ঠিক আছে|আচ্ছা|আসলে|শুনুন|শোনো|দেখুন|দেখো|যাইহোক|যাই হোক|হ্যাঁ|না|অবশ্যই|ধন্যবাদ|হ্যালো|হাই)(?=\s|$)", r"\1\2,", s, flags=re.IGNORECASE)
        s = re.sub(r"(^|\s)(কিন্তু|তবে|তাহলে|সুতরাং|নাহলে|নতুবা|অথবা|কারণ)(?=\s)", r", \2", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+(তাই না|নাকি|হবে তো|পারবেন তো|পারবে তো|আছেন তো|আছো তো)($|[।?!,])", r", \1?", s, flags=re.IGNORECASE)

        is_question = bool(re.search(r"(^|\s)(কি|কী|কেন|কোথায়|কোথাও|কখন|কেমন|কে|কার|কাকে|কিসের|কত|কবে|কিভাবে|কই|নাকি)($|\s|[।?!,])", s, flags=re.IGNORECASE)) or s.endswith("?")
        if not re.search(r"[।?!]$", s):
            s = re.sub(r",+$", "", s)
            s += "?" if is_question else "।"

        s = re.sub(r"\s+([,।?!])", r"\1", s)
        s = re.sub(r"([,।?!])(?=[^\s,।?!])", r"\1 ", s)
        s = re.sub(r",+", ",", s)
        s = re.sub(r"\s{2,}", " ", s)
        return s.strip()

    def format_english_punctuation(self, raw_text):
        if not raw_text:
            return ""
        s = raw_text.strip()
        s = re.sub(r"(^|\s)(comma)($|\s)", r"\1,\3", s, flags=re.IGNORECASE)
        s = re.sub(r"(^|\s)(period|full stop)($|\s)", r"\1.\3", s, flags=re.IGNORECASE)
        s = re.sub(r"(^|\s)(question mark)($|\s)", r"\1?\3", s, flags=re.IGNORECASE)

        def capitalize_filler(m):
            return m.group(1) + m.group(2).capitalize() + ","

        s = re.sub(r"(^|\s)(ok|okay|well|actually|yes|no|hello|hi|hey|sure|please)(?=\s|$)", capitalize_filler, s, flags=re.IGNORECASE)
        s = re.sub(r"\s+(right|isn't it|aren't you|won't you)($|[.?!,])", r", \1?", s, flags=re.IGNORECASE)

        is_question = bool(re.search(r"(^|\s)(what|why|when|where|who|whom|whose|which|how|is|are|am|do|does|did|can|could|will|would|should)($|\s)", s, flags=re.IGNORECASE)) or s.endswith("?")
        if not re.search(r"[.?!]$", s):
            s = re.sub(r",+$", "", s)
            s += "?" if is_question else "."

        if s:
            s = s[0].upper() + s[1:]
        s = re.sub(r"\s+([,.?!])", r"\1", s)
        s = re.sub(r"([,.?!])(?=[^\s,.?!])", r"\1 ", s)
        s = re.sub(r",+", ",", s)
        s = re.sub(r"\s{2,}", " ", s)
        return s.strip()

    def _audio_callback(self, recognizer, audio):
        if not self.is_recording:
            return

        active_mode = self.mode
        active_lang = self.lang

        if active_mode == "bn_to_en":
            speech_lang = "bn-BD"
        elif active_mode == "en_to_bn":
            speech_lang = "en-US"
        else:
            speech_lang = active_lang

        try:
            transcript = recognizer.recognize_google(audio, language=speech_lang).strip()
            if not transcript:
                return

            if active_mode == "bn_to_en":
                translated = self.translate_text(transcript, "bn", "en")
                final_text = self.format_english_punctuation(translated)
            elif active_mode == "en_to_bn":
                translated = self.translate_text(transcript, "en", "bn")
                final_text = self.format_bangla_punctuation(translated)
            elif active_lang == "bn-BD":
                final_text = self.format_bangla_punctuation(transcript)
            else:
                final_text = self.format_english_punctuation(transcript)

            if self.on_result and final_text:
                self.on_result(final_text)
        except sr.UnknownValueError:
            pass
        except Exception:
            pass

    def start(self):
        if self.is_recording:
            return
        try:
            if not self.microphone:
                self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
            self.stop_listening_fn = self.recognizer.listen_in_background(
                self.microphone,
                self._audio_callback,
                phrase_time_limit=15
            )
            self.is_recording = True
            if self.on_status:
                self.on_status(self.is_recording, self.lang, self.mode)
        except Exception:
            self.is_recording = False
            if self.on_status:
                self.on_status(self.is_recording, self.lang, self.mode)

    def stop(self):
        if not self.is_recording:
            return
        if self.stop_listening_fn:
            try:
                self.stop_listening_fn(wait_for_stop=False)
            except Exception:
                pass
            self.stop_listening_fn = None
        self.is_recording = False
        if self.on_status:
            self.on_status(self.is_recording, self.lang, self.mode)

    def toggle(self):
        if self.is_recording:
            self.stop()
        else:
            self.start()
