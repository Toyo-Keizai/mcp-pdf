import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from lib.pdf import (
    crop_pdf as crop_pdf_tool,
)
from lib.pdf import (
    get_cropped_pdf_image as get_cropped_pdf_image_tool,
)
from lib.pdf import (
    get_page_rect as get_doc_info_tool,
)
from lib.pdf import (
    get_pdf_image as get_pdf_image_tool,
)
from lib.pdf import (
    read_pdf as read_pdf_tool,
)

log_file = Path(__file__).with_name("mcp.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

mcp = FastMCP(
    "PDF Tools",
    dependencies=[
        "pymupdf",
        "pymupdf4llm",
        "pillow",
    ],
)


@mcp.tool()
def read_pdf(pdf_path: Path, output_path: Path | None = None) -> str:
    """Read a PDF file and return the text content
    Args:
        pdf_path: The full path to the PDF file
        output_path: Optional. The full path to the output file. If provided, the text content will be saved to the path.
    Returns:
        The text content of the pdf will be returned.
    """
    return read_pdf_tool(pdf_path, output_path)


@mcp.tool()
def get_page_rect(pdf_path: Path) -> dict[str, int]:
    """Get the common rectangle of pages of the PDF file. This is useful when cropping rectangle of the pdf since the cropping rectangle must be within the page rectangle.
    Args:
        pdf_path: The full path to the PDF file
    Returns:
        The common rectangle of pages of the pdf will be returned. The format is:
        {
            x: int,
            y: int,
            width: int,
            height: int,
        }
    """
    return get_doc_info_tool(pdf_path)


@mcp.tool()
def get_cropped_pdf(
    pdf_path: Path,
    page_num: int,
    x: int,
    y: int,
    width: int,
    height: int,
    output_path: Path | None = None,
) -> str:
    """Crop a PDF file and return the cropped pdf. The cropping rectangle must be within the page rectangle.
    Args:
        pdf_path: The full path to the PDF file
        page_num: The page number to crop. Starts from 0. (page_num=0 means the first page)
        x: The top-left x coordinate of the crop box
        y: The top-left y coordinate of the crop box
        width: The width of the crop box
        height: The height of the crop box
        output_path: Optional. The full path to the output file. If provided, the cropped image will be saved to the path.
    Returns:
        The cropped markdown text of the pdf will be returned.
    """
    return crop_pdf_tool(pdf_path, page_num, x, y, width, height, output_path)


@mcp.tool()
def get_pdf_image(
    pdf_path: Path,
    page_num: int,
    output_path: Path | None = None,
) -> Image:
    """Get the image of a PDF file
    Args:
        pdf_path: The full path to the PDF file
        page_num: The page number to get the image from. Starts from 0. (page_num=0 means the first page)
        output_path: Optional. The full path to the output file. If provided, the image will be saved to the path.
    Returns:
        The image of the pdf is returned.
    """
    return get_pdf_image_tool(pdf_path, page_num, output_path)


@mcp.tool()
def get_cropped_pdf_image(
    pdf_path: Path,
    page_num: int,
    x: int,
    y: int,
    width: int,
    height: int,
    output_path: Path | None = None,
) -> Image:
    """Get the cropped image of a PDF file. The cropping rectangle must be within the page rectangle.
    Args:
        pdf_path: The full path to the PDF file
        page_num: The page number to get the image from. Starts from 0. (page_num=0 means the first page)
        x: The top-left x coordinate of the crop box
        y: The top-left y coordinate of the crop box
        width: The width of the crop box
        height: The height of the crop box
        output_path: Optional. The full path to the output file. If provided, the cropped image will be saved to the path.
    Returns:
        The cropped image will be returned.
    """
    return get_cropped_pdf_image_tool(
        pdf_path, page_num, x, y, width, height, output_path
    )


def main():
    """Main entry point."""
    mcp.run()


if __name__ == "__main__":
    main()
