import io
import logging
from pathlib import Path
from typing import Any, Literal, Optional, TypedDict

import pymupdf
import pymupdf4llm
from fastmcp.utilities.types import Image

logger = logging.getLogger(__name__)


def to_markdown(doc: pymupdf.Document | Path, pages: list[int] | None = None) -> str:
    markdown = pymupdf4llm.to_markdown(
        doc,
        pages=pages,
        ignore_images=True,
    )

    # By default, pymupdf4llm treats a block of text as code block if all of them are rendered by monospace font.
    # This is not what we want. Specifying `ignore_code=True` does not work well so just removing the code block markers.
    markdown = markdown.replace("```", "")

    return markdown


class GeneralResult(TypedDict):
    success: Literal[True] | Literal[False]


class GeneralError(GeneralResult):
    success: Literal[False]
    error: str
    details: str


def read_pdf(
    pdf_path: Path, pages: list[int] | None = None, output_path: Optional[Path] = None
) -> str:
    logger.info(f"Reading PDF from {pdf_path}")
    doc = pymupdf.open(pdf_path)
    markdown = to_markdown(doc, pages)
    logger.info(f"Converted PDF to Markdown. {len(markdown)} characters")
    if output_path:
        logger.info(f"Saving Markdown to {output_path}")
        output_path.write_bytes(markdown.encode())
    return markdown


def get_pdf_summary(pdf_path: Path) -> dict[str, Any]:
    doc = pymupdf.open(pdf_path)
    return {
        "page_count": len(doc),
        "total_characters": sum(len(page.get_text().encode("utf8")) for page in doc),  # type: ignore
        "table_of_contents": doc.get_toc(),  # type: ignore
        "width": doc[0].rect.width,
        "height": doc[0].rect.height,
    }


def crop_pdf(
    pdf_path: Path,
    page_num: int,
    x: int,
    y: int,
    width: int,
    height: int,
    output_path: Optional[Path] = None,
) -> str:
    logger.info(f"Cropping PDF. {pdf_path} -> {output_path}")
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    page.set_cropbox(pymupdf.Rect(x, y, x + width, y + height))
    doc.select([page_num])
    if output_path:
        logger.info(f"Saving cropped PDF to {output_path}")
        doc.save(output_path)
    return to_markdown(doc)


def get_pdf_image(
    pdf_path: Path, page_num: int, output_path: Optional[Path] = None
) -> Image:
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]

    pixmap = page.get_pixmap()  # type: ignore
    img = pixmap.pil_image()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    if output_path:
        pixmap.save(output_path)
        logger.info(f"Saved PDF image to {output_path}")

    return Image(
        data=img_bytes,
        format="PNG",
    )


def get_cropped_pdf_image(
    pdf_path: Path,
    page_num: int,
    x: int,
    y: int,
    width: int,
    height: int,
    output_path: Optional[Path] = None,
) -> Image:
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    page.set_cropbox(pymupdf.Rect(x, y, x + width, y + height))

    pixmap = page.get_pixmap()  # type: ignore
    img = pixmap.pil_image()
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()

    if output_path:
        pixmap.save(output_path)
        logger.info(f"Saved cropped PDF image to {output_path}")

    return Image(
        data=img_bytes,
        format="PNG",
    )
