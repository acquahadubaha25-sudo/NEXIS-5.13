# NEXIS 5.13 — VOICE ENGINE UPGRADE
import math  
import random  
import datetime  
import ast  
import operator  
import re  
import sqlite3  
import urllib.parse  
import os  
import platform  
import threading  
import queue
import time

# Optional Windows microphone backend. This lets NEXIS listen even when
# SpeechRecognition cannot load PyAudio.
SOUNDDEVICE_AVAILABLE = False
NUMPY_AVAILABLE = False
sd = None
np = None

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
    print("NEXIS: sounddevice microphone backend loaded.")
except Exception as error:
    print("NEXIS: sounddevice backend unavailable:", error)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception as error:
    print("NEXIS: NumPy unavailable for sounddevice backend:", error)
import webbrowser  
import traceback  
  
  
# ============================================================  
# NEXIS 5.13  
# ADVANCED INTELLIGENCE & CONTEXT UPGRADE  
# ============================================================  
  
  
# ============================================================  
# SAFE KIVY IMPORTS  
# ============================================================  
  
try:  
  
    from kivy.app import App  
    from kivy.clock import Clock  
    from kivy.uix.widget import Widget  
    from kivy.uix.boxlayout import BoxLayout  
    from kivy.uix.textinput import TextInput  
    from kivy.uix.button import Button  
    from kivy.uix.label import Label  
    from kivy.graphics import Color, Ellipse, Line, Rectangle  
    from kivy.animation import Animation  
    from kivy.properties import NumericProperty, StringProperty  
  
    KIVY_AVAILABLE = True  
  
except Exception as error:  
  
    print("FATAL KIVY IMPORT ERROR")
    print(error)  
  
    traceback.print_exc()  
  
    KIVY_AVAILABLE = False  
  
  
# ============================================================  
# LAPTOP TEXT TO SPEECH  
# ============================================================  
  
TTS_AVAILABLE = False
tts_queue = None
tts_worker = None
tts_stop_event = threading.Event()
tts_state_lock = threading.Lock()
tts_is_speaking = False
tts_current_text = ""
tts_rate = 165
tts_volume = 1.0
  
  
try:  
  
    import pyttsx3
  
    tts_queue = queue.Queue()
  
    TTS_AVAILABLE = True  
  
    print("NEXIS: Laptop TTS module loaded.")
  
except Exception as error:  
  
    print("NEXIS: TTS unavailable:", error)  


def _set_tts_state(speaking, text=""):
    global tts_is_speaking, tts_current_text
    with tts_state_lock:
        tts_is_speaking = bool(speaking)
        tts_current_text = str(text or "")


def is_tts_speaking():
    with tts_state_lock:
        return tts_is_speaking


def _create_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", tts_rate)
    engine.setProperty("volume", tts_volume)
    return engine


def _windows_native_tts(text):
    """Speak text through Windows' native System.Speech engine.

    This is intentionally independent of pyttsx3.  On some Windows/SAPI
    installations pyttsx3 can report success while only speaking part of an
    utterance or silently losing later queued utterances.  System.Speech is
    used as the primary Windows path so NEXIS does not depend on pyttsx3's
    COM/event-loop behavior.
    """
    if platform.system() != "Windows":
        return False

    try:
        import base64
        import subprocess

        encoded = base64.b64encode(
            str(text).encode("utf-8")
        ).decode("ascii")

        # Windows PowerShell 5.1 includes System.Speech on supported desktop
        # Windows installations.  Base64 keeps quotes, punctuation and
        # non-English characters out of the PowerShell command itself.
        ps_script = (
            "Add-Type -AssemblyName System.Speech; "
            "$b=[Convert]::FromBase64String('" + encoded + "'); "
            "$t=[Text.Encoding]::UTF8.GetString($b); "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate=0; $s.Volume=100; "
            "$s.Speak($t); $s.Dispose()"
        )

        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_script,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=max(30, min(180, 30 + len(str(text)) // 8)),
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0
            ),
        )

        if completed.returncode != 0:
            print(
                "NEXIS WINDOWS TTS ERROR:",
                completed.stderr.strip() or
                "PowerShell speech command failed."
            )
            return False

        return True

    except Exception as error:
        print("NEXIS WINDOWS TTS ERROR:", error)
        return False


def _pyttsx3_tts(text):
    """Fallback speech path for systems where native Windows speech fails."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", tts_rate)
        engine.setProperty("volume", tts_volume)
        engine.say(str(text))
        engine.runAndWait()
        try:
            engine.stop()
        except Exception:
            pass
        return True
    except Exception as error:
        print("NEXIS PYTTSX3 FALLBACK ERROR:", error)
        return False


def _tts_worker_loop():
    """Reliable sequential speech worker for complete NEXIS responses."""
    while True:
        item = None
        callback = None

        try:
            item = tts_queue.get()

            if item is None:
                tts_queue.task_done()
                return

            if isinstance(item, tuple):
                text, callback = item
            else:
                text = item

            text = _prepare_tts_text(text)

            if not text:
                if callback is not None:
                    callback()
                continue

            if tts_stop_event.is_set():
                tts_stop_event.clear()
                continue

            _set_tts_state(True, text)
            print("NEXIS TTS: speaking response (%d characters)." % len(text))

            completed = False

            # Windows native speech is the primary path.  It speaks the
            # complete response in one call, avoiding the pyttsx3/SAPI issue
            # where only the first sentence may be heard.
            if platform.system() == "Windows":
                completed = _windows_native_tts(text)

                if not completed and not tts_stop_event.is_set():
                    print("NEXIS TTS: trying pyttsx3 fallback...")
                    completed = _pyttsx3_tts(text)
            else:
                completed = _pyttsx3_tts(text)

            if tts_stop_event.is_set():
                tts_stop_event.clear()
                completed = False

            if completed:
                print("NEXIS TTS: response completed.")
                if callback is not None:
                    try:
                        callback()
                    except Exception as callback_error:
                        print(
                            "NEXIS TTS CALLBACK ERROR:",
                            callback_error
                        )
            else:
                print("NEXIS TTS: response was not spoken.")

        except Exception as error:
            print("NEXIS TTS WORKER ERROR:", error)
            traceback.print_exc()

        finally:
            _set_tts_state(False, "")
            if item is not None:
                try:
                    tts_queue.task_done()
                except Exception:
                    pass


def _ensure_tts_worker():
    global tts_worker

    if tts_worker is None or not tts_worker.is_alive():
        tts_stop_event.clear()
        tts_worker = threading.Thread(
            target=_tts_worker_loop,
            name="NEXIS-TTS-Worker",
            daemon=True
        )
        tts_worker.start()

def _prepare_tts_text(text):
    """Convert a NEXIS response into clean, speakable text."""
    if text is None:
        return ""

    cleaned = str(text)
    cleaned = cleaned.replace("\r\n", "\n")
    cleaned = cleaned.replace("\r", "\n")

    # Remove common UI/markdown formatting before sending text to SAPI.
    cleaned = re.sub(r"```.*?```", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*•]\s+", "", cleaned)

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)

    return cleaned.strip()


def _split_tts_text(text):
    """Split long responses into reliable Windows speech units."""
    if not text:
        return []

    chunks = [
        chunk.strip()
        for chunk in re.split(
            r"(?<=[.!?])\s+|\n+",
            str(text)
        )
        if chunk.strip()
    ]

    if not chunks:
        return [str(text).strip()]

    safe_chunks = []

    for chunk in chunks:
        if len(chunk) <= 700:
            safe_chunks.append(chunk)
            continue

        pieces = re.split(
            r"(?<=[,;:])\s+",
            chunk
        )

        current = ""

        for piece in pieces:
            piece = piece.strip()

            if not piece:
                continue

            if not current:
                current = piece

            elif len(current) + 1 + len(piece) <= 700:
                current += " " + piece

            else:
                safe_chunks.append(current)
                current = piece

        if current:
            safe_chunks.append(current)

    return safe_chunks


def _ensure_tts_worker():
    global tts_worker
    if tts_worker is None or not tts_worker.is_alive():
        tts_stop_event.clear()
        tts_worker = threading.Thread(
            target=_tts_worker_loop,
            name="NEXIS-TTS-Worker",
            daemon=True
        )
        tts_worker.start()


def set_tts_rate(rate):
    global tts_rate
    try:
        tts_rate = max(80, min(260, int(rate)))
    except Exception:
        pass
    return tts_rate


def set_tts_volume(volume):
    global tts_volume
    try:
        tts_volume = max(0.0, min(1.0, float(volume)))
    except Exception:
        pass
    return tts_volume


def stop_tts():
    """Cancel active speech and clear queued responses."""
    if not TTS_AVAILABLE or tts_queue is None:
        return
    tts_stop_event.set()
    try:
        while True:
            tts_queue.get_nowait()
            tts_queue.task_done()
    except queue.Empty:
        pass
    except Exception as error:
        print("NEXIS TTS STOP ERROR:", error)


# ============================================================  
# SPEECH TO TEXT  
# KEPT FOR FUTURE DEVELOPMENT  
# ============================================================  
  
STT_AVAILABLE = False  
sr = None  
  
  
try:  
  
    import speech_recognition as speech_recognition  
  
    sr = speech_recognition  
  
    STT_AVAILABLE = True  
  
    print("NEXIS: Speech Recognition module loaded.")  
  
except Exception as error:  
  
    print("NEXIS: Speech Recognition unavailable:", error)  
  
  
# ============================================================  
# PLATFORM DETECTION  
# ============================================================  
  
IS_ANDROID = (  
  
    platform.system() == "Linux"  
  
    and (  
  
        "ANDROID_ARGUMENT" in os.environ  
  
        or  
  
        "ANDROID_PRIVATE" in os.environ  
  
    )  
  
)  
  
  
ANDROID_AVAILABLE = False  
  
  
PythonActivity = None  
Context = None  
IntentFilter = None  
Intent = None  
BatteryManager = None  
Build = None  
Version = None  
Uri = None  
  
  
# ============================================================  
# SAFE ANDROID / PYJNIUS LOADING  
# ============================================================  
  
if IS_ANDROID:  
  
    try:  
  
        from jnius import autoclass  
  
        PythonActivity = autoclass(  
            "org.kivy.android.PythonActivity"  
        )  
  
        Context = autoclass(  
            "android.content.Context"  
        )  
  
        IntentFilter = autoclass(  
            "android.content.IntentFilter"  
        )  
  
        Intent = autoclass(  
            "android.content.Intent"  
        )  
  
        BatteryManager = autoclass(  
            "android.os.BatteryManager"  
        )  
  
        Build = autoclass(  
            "android.os.Build"  
        )  
  
        Version = autoclass(  
            "android.os.Build$VERSION"  
        )  
  
        Uri = autoclass(  
            "android.net.Uri"  
        )  
  
        ANDROID_AVAILABLE = True  
  
        print(  
            "NEXIS: Android PyJNIus system loaded."  
        )  
  
    except Exception as error:  
  
        print(  
            "NEXIS: Android system unavailable:",  
            error  
        )  
  
        traceback.print_exc()  
  
  
# ============================================================  
# DATABASE LOCATION  
# ============================================================  
  
def get_database_path():  
  
    try:  
  
        if KIVY_AVAILABLE:  
  
            running_app = App.get_running_app()  
  
            if (  
  
                running_app  
  
                and hasattr(  
                    running_app,  
                    "user_data_dir"  
                )  
  
                and running_app.user_data_dir  
  
            ):  
  
                folder = running_app.user_data_dir  
  
            else:  
  
                folder = os.path.join(  
                    os.path.expanduser("~"),  
                    ".nexis"  
                )  
  
        else:  
  
            folder = os.path.join(  
                os.path.expanduser("~"),  
                ".nexis"  
            )  
  
        os.makedirs(  
            folder,  
            exist_ok=True  
        )  
  
        return os.path.join(  
            folder,  
            "nexis_memory.db"  
        )  
  
    except Exception:  
  
        return "nexis_memory.db"  
  
print("[File truncated for space - full file available in repository]")
print("This is NEXIS 5.13 core. See GitHub for complete code.")
