"""
Nidhi — Document Ingestion

Handles uploading and processing of PDF, DOCX, TXT, and image files.
Extracts text and prepares for chunking and embedding.
"""

from __future__ import annotations

import uuid
import logging
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUPPORTED_TYPES = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".txt": "txt",
    ".md": "txt",
    ".csv": "txt",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}


async def ingest_file(
    file_path: Path,
    original_filename: str,
) -> tuple[str, list[str]]:
    """
    Ingest a file and extract text content.

    Args:
        file_path: Path to the saved file.
        original_filename: Original filename from upload.

    Returns:
        Tuple of (file_type, list_of_text_pages)
    """
    suffix = Path(original_filename).suffix.lower()
    file_type = SUPPORTED_TYPES.get(suffix)

    if not file_type:
        raise ValueError(f"Unsupported file type: {suffix}")

    if file_type == "pdf":
        return file_type, await _extract_pdf(file_path)
    elif file_type == "docx":
        return file_type, await _extract_docx(file_path)
    elif file_type == "txt":
        return file_type, await _extract_text(file_path)
    elif file_type == "image":
        return file_type, await _extract_image(file_path)
    else:
        raise ValueError(f"Unknown file type: {file_type}")


async def _extract_pdf(file_path: Path) -> list[str]:
    """
    Extract text from a PDF file using PyMuPDF (fitz), falling back to OCR
    for pages with empty text streams.
    """
    try:
        import fitz
        from PIL import Image
        import io
        try:
            import pytesseract
            has_pytesseract = True
        except ImportError:
            has_pytesseract = False

        doc = fitz.open(str(file_path))
        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if not text.strip():
                # Empty text stream, fall back to OCR
                if has_pytesseract:
                    logger.info(f"Page {page_num + 1} of {file_path.name} is empty. Attempting OCR fallback.")
                    try:
                        # Get pixmap
                        pix = page.get_pixmap(dpi=150)  # 150 DPI is standard for legible OCR
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        # Perform OCR
                        ocr_text = pytesseract.image_to_string(img)
                        if ocr_text.strip():
                            text = ocr_text
                        else:
                            text = f"[Page {page_num + 1}: Empty scanned page — no text detected via OCR]"
                    except Exception as ocr_err:
                        logger.error(f"OCR failed for page {page_num + 1} of {file_path.name}: {ocr_err}")
                        text = f"[Page {page_num + 1}: Empty page — OCR failed: {ocr_err}]"
                else:
                    text = f"[Page {page_num + 1}: Empty page — OCR not available]"
            
            pages.append(text)

        logger.info(f"Extracted {len(pages)} pages from PDF: {file_path.name}")
        doc.close()
        return pages
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to extract PDF: {e}")


async def _extract_docx(file_path: Path) -> list[str]:
    """Extract text from a DOCX file."""
    try:
        from docx import Document

        doc = Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        # Group paragraphs into logical pages (~500 words each)
        pages = []
        current_page = []
        word_count = 0

        for para in paragraphs:
            current_page.append(para)
            word_count += len(para.split())
            if word_count >= 500:
                pages.append("\n\n".join(current_page))
                current_page = []
                word_count = 0

        if current_page:
            pages.append("\n\n".join(current_page))

        logger.info(f"Extracted {len(pages)} sections from DOCX: {file_path.name}")
        return pages
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise ValueError(f"Failed to extract DOCX: {e}")


async def _extract_text(file_path: Path) -> list[str]:
    """Extract text from a plain text file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Split into pages of ~500 words
        words = content.split()
        pages = []
        for i in range(0, len(words), 500):
            pages.append(" ".join(words[i:i + 500]))

        logger.info(f"Extracted {len(pages)} sections from text: {file_path.name}")
        return pages or [content]
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise ValueError(f"Failed to extract text: {e}")


async def _extract_image(file_path: Path) -> list[str]:
    """Extract text from an image using OCR."""
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(str(file_path))
        text = pytesseract.image_to_string(image)

        if not text.strip():
            return [f"[Image: {file_path.name} — no text detected via OCR]"]

        logger.info(f"Extracted text from image: {file_path.name}")
        return [text]
    except ImportError:
        logger.warning("pytesseract not available — returning placeholder")
        return [f"[Image: {file_path.name} — OCR not available]"]
    except Exception as e:
        logger.error(f"Image OCR failed: {e}")
        return [f"[Image: {file_path.name} — OCR failed: {e}]"]
