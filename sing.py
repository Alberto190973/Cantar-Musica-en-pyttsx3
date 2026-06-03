import pyttsx3
import numpy as np
import simpleaudio as sa
import time
import threading
import wave
import os
import tempfile

# Mapa básico de notas (frecuencias en Hz)
NOTE_FREQ = {
    'C3': 130.81,
    'D3': 146.83,
    'E3': 164.81,
    'F3': 174.61,
    'G3': 196.00,
    'A3': 220.00,
    'B3': 246.94,
    'C4': 261.63,
    'D4': 293.66,
    'E4': 329.63,
    'F4': 349.23,
    'G4': 392.00,
    'A4': 440.00,
    'B4': 493.88,
    'C5': 523.25,
    'D5': 587.33,
    'E5': 659.25,
    'F5': 698.46,
    'G5': 783.99,
}

SAMPLE_RATE = 44100

def make_wave(frequency, duration, volume=0.3):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.sin(frequency * t * 2 * np.pi)
    audio = (wave * (2**15 - 1) * volume).astype(np.int16)
    return audio.tobytes()

def play_note(note, duration):
    if note is None:
        time.sleep(duration)
        return
    freq = NOTE_FREQ.get(note, NOTE_FREQ['A4'])
    data = make_wave(freq, duration)
    play_obj = sa.play_buffer(data, 1, 2, SAMPLE_RATE)
    play_obj.wait_done()

def play_melody(melody):
    for note, dur, _ in melody:
        play_note(note, dur)

def sing_with_tts(melody, rate=140, volume=1.0):
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)
    for _, dur, syll in melody:
        # Decir la sílaba y esperar una fracción para mantener el ritmo
        engine.say(syll)
        engine.runAndWait()
        # Pequeña pausa entre sílabas (ajusta según necesites)
        time.sleep(0.01)

# --- Nuevo: sintetizar sílabas a WAV y reproducir cambiando la tasa de muestreo ---
REF_VOICE_FREQ = 220.0  # frecuencia de referencia aproximada de la voz (Hz). Ajusta según tu voz.

def synthesize_syllable_wav(syllable, path):
    engine = pyttsx3.init()
    engine.setProperty('rate', 140)
    engine.save_to_file(syllable, path)
    engine.runAndWait()

def play_syllable_with_pitch(syllable, target_freq):
    # Guardar WAV temporal por sílaba y reutilizar si existe
    safe_name = ''.join(c for c in syllable if c.isalnum()) or 'syll'
    wav_path = os.path.join(tempfile.gettempdir(), f"tts_{safe_name}.wav")
    if not os.path.exists(wav_path):
        synthesize_syllable_wav(syllable, wav_path)

    with wave.open(wav_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)

    # Ratio entre nota objetivo y frecuencia de referencia
    ratio = float(target_freq) / float(REF_VOICE_FREQ)
    if ratio <= 0:
        ratio = 1.0

    # Convertir bytes a numpy array según sample width
    if sampwidth == 1:
        dtype = np.uint8
    elif sampwidth == 2:
        dtype = np.int16
    elif sampwidth == 4:
        dtype = np.int32
    else:
        # Fallback: reproducir sin cambiar pitch
        play_obj = sa.play_buffer(frames, n_channels, sampwidth, framerate)
        play_obj.wait_done()
        return

    audio = np.frombuffer(frames, dtype=dtype)
    if sampwidth == 1:
        # uint8 offset
        audio = audio.astype(np.int16) - 128

    # Manejar canales
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels)

    # Nuevo tamaño después de aplicar factor de velocidad (pitch)
    old_len = audio.shape[0]
    new_len = max(1, int(old_len / ratio))
    old_idx = np.linspace(0, old_len - 1, num=old_len)
    new_idx = np.linspace(0, old_len - 1, num=new_len)

    if n_channels > 1:
        new_audio = np.zeros((new_len, n_channels), dtype=np.float32)
        for ch in range(n_channels):
            new_audio[:, ch] = np.interp(new_idx, old_idx, audio[:, ch])
    else:
        new_audio = np.interp(new_idx, old_idx, audio)

    # Volver a tipo original
    if sampwidth == 1:
        out = (new_audio + 128).clip(0, 255).astype(np.uint8)
    elif sampwidth == 2:
        out = new_audio.clip(-32768, 32767).astype(np.int16)
    else:
        out = new_audio.clip(-2147483648, 2147483647).astype(np.int32)

    play_obj = sa.play_buffer(out.tobytes(), n_channels, sampwidth, framerate)
    play_obj.wait_done()

def sing_melody_with_pitch(melody):
    # Reproduce cada sílaba con el pitch aproximado de la nota objetivo
    for note, dur, syll in melody:
        if note is None:
            time.sleep(dur)
            continue
        freq = NOTE_FREQ.get(note, NOTE_FREQ['A4'])
        # Reproducir la sílaba ajustando la frecuencia
        play_syllable_with_pitch(syll, freq)
        # breve pausa para respetar el ritmo
        time.sleep(0.01)
n = 0.05  # duración de cada nota en segundos
c = n/2  # duración de cada corchea

d = n*2  # duración de las notas largas
estrellita = [
    ('C4', n, 'Do'),
    ('C4', n, 'Do'),
    ('G4', n, 'Sol'),
    ('G4', n, 'Sol'),
    ('A4', n, 'La'),
    ('A4', n, 'La'),
    ('G4', d, 'Sol'),
    ('F4', n, 'Fa'),
    ('F4', n, 'Fa'),
    ('E4', n, 'Mi'),
    ('E4', n, 'Mi'),
    ('D4', n, 'Re'),
    ('D4', n, 'Re'),
    ('C4', d, 'Do'),
]

sobrelepuentedealgo = [
    ('C4', n, 'Sobre'),
    ('D4', n, 'le'),
    ('E4', n, 'puen'),
    ('F4', n, 'te'),
    ('G4', n, 'de'),
    ('A4', n, 'al'),
    ('B4', n, 'go'),
    ('C5', d, 'algo'),
]

def Satr(melody=estrellita):
    # Ejemplo de melodía simple con sílabas (reemplaza las sílabas por tus letras)

    # Reproducir sílabas con pitch aproximado (método local mediante re-muestreo)
    sing_melody_with_pitch(melody)

def Satr2(melody=sobrelepuentedealgo):
    # Ejemplo de melodía simple con sílabas (reemplaza las sílabas por tus letras)

    # Reproducir sílabas con TTS sin ajuste de pitch (método básico)
    sing_with_tts(melody)
if __name__ == '__main__':
    print('Ejemplo: reproduciendo melodía y TTS (usa tus sílabas).')
    Satr(estrellita)
    Satr2(sobrelepuentedealgo)
