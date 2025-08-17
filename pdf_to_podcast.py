#!/usr/bin/env python3
"""
PDF → Podcast (MP3) Converter (Drag & Drop GUI)

This version:
- Assumes PDFs are preprocessed with Adobe OCR, so text extraction is clean
- Removes Python OCR dependencies for faster processing
- Supports edge-tts and gTTS engines only
- Select or drag a PDF file into the window
- Choose minutes per episode and voice engine
- Convert to podcast-style MP3 episodes automatically
- Progress shown in a log window

Instructions for creating a single executable:
Use PyInstaller with the following command:

Windows example:
pyinstaller --onefile --windowed pdf_to_podcast.py

- --onefile bundles everything into a single .exe
- --windowed hides the console (GUI app)
"""

import asyncio
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from pypdf import PdfReader
from gtts import gTTS
import edge_tts

# ---------------------- Core Functions ----------------------

def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    text = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text.append(t)
    full_text = "\n\n".join(text)
    return full_text

async def tts_edge_tts(text: str, out_path: Path, voice: str = "en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(str(out_path))

def tts_gtts(text: str, out_path: Path):
    tts = gTTS(text=text, lang="en")
    tts.save(str(out_path))

def split_text(full_text: str, words_per_episode: int):
    words = full_text.split()
    start = 0
    episodes = []
    idx = 1
    while start < len(words):
        end = min(len(words), start + words_per_episode)
        episode_text = " ".join(words[start:end])
        episodes.append((idx, episode_text))
        start = end
        idx += 1
    return episodes

# ---------------------- GUI ----------------------

def convert_pdf(pdf_path: Path, engine: str, minutes: int, log_widget):
    try:
        log_widget.insert(tk.END, f"[info] Reading {pdf_path}\n")
        text = extract_text(pdf_path)
        if not text.strip():
            messagebox.showerror("Error", "No text could be extracted from PDF.")
            return

        words_per_episode = minutes * 180  # assume ~180 words per min
        episodes = split_text(text, words_per_episode)

        out_dir = pdf_path.with_suffix("").with_name(pdf_path.stem + "_podcast")
        out_dir.mkdir(exist_ok=True)

        for idx, ep_text in episodes:
            out_file = out_dir / f"episode_{idx:02d}.mp3"
            log_widget.insert(tk.END, f"[tts] Generating {out_file.name}\n")
            log_widget.see(tk.END)
            log_widget.update()

            if engine == "edge-tts":
                asyncio.run(tts_edge_tts(ep_text, out_file))
            elif engine == "gtts":
                tts_gtts(ep_text, out_file)
            else:
                log_widget.insert(tk.END, f"[error] Unknown engine {engine}\n")

        messagebox.showinfo("Done", f"Created {len(episodes)} MP3s in {out_dir}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def select_file(entry):
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)

def main():
    root = tk.Tk()
    root.title("PDF to Podcast Converter")
    root.geometry("500x400")

    tk.Label(root, text="PDF File:").pack(anchor="w", padx=10, pady=5)
    file_frame = tk.Frame(root)
    file_frame.pack(fill="x", padx=10)
    entry = tk.Entry(file_frame)
    entry.pack(side="left", fill="x", expand=True)
    tk.Button(file_frame, text="Browse", command=lambda: select_file(entry)).pack(side="left")

    tk.Label(root, text="Engine:").pack(anchor="w", padx=10, pady=5)
    engine_var = tk.StringVar(value="edge-tts")
    ttk.Combobox(root, textvariable=engine_var, values=["edge-tts", "gtts"]).pack(fill="x", padx=10)

    tk.Label(root, text="Minutes per Episode:").pack(anchor="w", padx=10, pady=5)
    minutes_var = tk.IntVar(value=15)
    tk.Entry(root, textvariable=minutes_var).pack(fill="x", padx=10)

    log = tk.Text(root, height=10)
    log.pack(fill="both", padx=10, pady=10, expand=True)

    def run_conversion():
        pdf_file = entry.get()
        if not pdf_file:
            messagebox.showerror("Error", "Please select a PDF file")
            return
        convert_pdf(Path(pdf_file), engine_var.get(), minutes_var.get(), log)

    tk.Button(root, text="Convert", command=run_conversion).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
