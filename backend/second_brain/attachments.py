"""Validate original files and build transient Meta multimodal input."""

import base64
import io
import warnings
import zipfile
from pathlib import PurePath
from xml.etree import ElementTree

from fastapi import HTTPException
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_FILE_BYTES = 4_000_000  # Below the hosted function's 4.5 MB request cap.
MAX_FILES = 5
MAX_CONTEXT_BYTES = 20_000_000
MAX_TEXT = 100000
MEDIA = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
PUBLIC_FIELDS = ("id", "filename", "media_type", "size", "page_count", "created_at")


def public_file(record):
    return {key: record[key] for key in PUBLIC_FIELDS}


def validate_file(filename, data):
    # The filename is a display label only, never a filesystem path.
    filename = filename.replace("\\", "/").split("/")[-1].strip()
    if not filename or len(filename) > 255 or any(ord(c) < 32 for c in filename):
        raise HTTPException(422, "Use a filename of 1–255 characters")
    extension = PurePath(filename).suffix.lower()
    if extension not in MEDIA:
        raise HTTPException(
            415, "Choose a PDF, TXT, Word (.docx), PNG, JPEG, WebP or GIF file"
        )
    if not data or len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, "Choose a nonempty file up to 4 MB")
    text, pages = None, 0
    try:
        if extension == ".txt":
            text = data.decode(
                "utf-16" if data[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
            )
            if "\x00" in text:
                raise ValueError
        elif extension == ".docx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if (
                    len(entries) > 2000
                    or sum(e.file_size for e in entries) > 20_000_000
                ):
                    raise HTTPException(
                        422, "This Word document is too large when expanded"
                    )
                xml = archive.read("word/document.xml")
                if b"<!DOCTYPE" in xml or len(xml) > 4_000_000:
                    raise ValueError
                root = ElementTree.fromstring(xml)
                ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                text = "\n".join(
                    "".join(n.text or "" for n in paragraph.iter(ns + "t"))
                    for paragraph in root.iter(ns + "p")
                )
                if not text.strip():
                    raise HTTPException(
                        422,
                        "This Word document has no readable text. Upload it as a PDF to include its visual content.",
                    )
        elif extension == ".pdf":
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise HTTPException(422, "Unlock this PDF before uploading it")
            pages = len(reader.pages)
            if not 1 <= pages <= 50:
                raise HTTPException(422, "Choose a PDF with 1–50 pages")
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as picture:
                    expected = {
                        ".jpg": "JPEG",
                        ".jpeg": "JPEG",
                        ".png": "PNG",
                        ".webp": "WEBP",
                        ".gif": "GIF",
                    }[extension]
                    if (
                        picture.format != expected
                        or picture.width * picture.height > 25_000_000
                    ):
                        raise ValueError
                    picture.verify()
            pages = 1
        if text is not None and (not text.strip() or len(text) > MAX_TEXT):
            raise HTTPException(
                422, "Choose a document with readable text up to 100,000 characters"
            )
    except HTTPException:
        raise
    except (
        ValueError,
        OSError,
        KeyError,
        RuntimeError,
        SyntaxError,
        UnicodeError,
        zipfile.BadZipFile,
        ElementTree.ParseError,
        PyPdfError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        # Parser errors can contain document content. Do not expose them.
        raise HTTPException(
            422,
            "This file could not be read. Check its format and try exporting it again.",
        ) from None
    return {
        "filename": filename,
        "media_type": MEDIA[extension],
        "size": len(data),
        "page_count": pages,
        "text": text,
        "data": data,
    }


def model_file(record):
    if record["text"] is not None:
        return {
            "type": "input_text",
            "text": f"Attached file: {record['filename']}\n{record['text']}",
        }
    data_url = f"data:{record['media_type']};base64," + base64.b64encode(
        record["data"]
    ).decode("ascii")
    if record["media_type"].startswith("image/"):
        return {"type": "input_image", "image_url": data_url}
    return {"type": "input_file", "filename": record["filename"], "file_data": data_url}
