"""Build the font-independent copies of the deck from PowerPoint's own slide images.

    python presentation/make_shareable.py <folder with exported slide PNGs>

mizan-alrai-editable.pptx needs the Thmanyah typeface installed. This writes mizan-alrai.pptx
(one image per slide, speaker notes kept) and mizan-alrai.pdf, which look the same on any machine.
"""

from __future__ import annotations

import glob
import io
import os
import re
import sys
from pathlib import Path

import fitz
from PIL import Image
from pptx import Presentation

HERE = Path(__file__).resolve().parent


def main(png_dir: str) -> None:
    files = sorted(glob.glob(os.path.join(png_dir, "*[0-9].PNG")), key=lambda f: int(re.findall(r"(\d+)\.PNG$", f)[0]))
    source = Presentation(HERE / "mizan-alrai-editable.pptx")
    notes = [s.notes_slide.notes_text_frame.text if s.has_notes_slide else "" for s in source.slides]
    assert len(files) == len(notes), (len(files), len(notes))

    deck = Presentation()
    deck.slide_width, deck.slide_height = source.slide_width, source.slide_height
    pdf = fitz.open()
    for path, note in zip(files, notes):
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.shapes.add_picture(path, 0, 0, deck.slide_width, deck.slide_height)
        if note:
            slide.notes_slide.notes_text_frame.text = note
        jpeg = io.BytesIO()
        Image.open(path).convert("RGB").save(jpeg, "JPEG", quality=90)
        page = pdf.new_page(width=960, height=540)
        page.insert_image(page.rect, stream=jpeg.getvalue())
    deck.save(HERE / "mizan-alrai.pptx")
    pdf.save(HERE / "mizan-alrai.pdf", deflate=True)
    print(f"{len(files)} slides -> mizan-alrai.pptx, mizan-alrai.pdf")


if __name__ == "__main__":
    main(sys.argv[1])
