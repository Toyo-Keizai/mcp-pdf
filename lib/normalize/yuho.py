"""
有価証券報告書 (Securities Report) Markdown Normalizer

This module provides functions to normalize markdown text converted from Japanese securities reports PDFs.
It handles various formatting issues and creates a well-structured document with proper headers.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class HeaderLevel(Enum):
    """Enumeration for header levels in markdown"""

    PART = 1  # 第一部, 第二部 etc. -> #
    CHAPTER = 2  # 第１, 第２ etc. -> ##
    SECTION = 3  # １, ２ etc. -> ###
    SUBSECTION = 4  # (1), （１）, ① etc. -> ####


@dataclass
class HeaderPattern:
    """Data class for header patterns and their properties"""

    pattern: str
    level: HeaderLevel
    description: str


# Define header patterns with their corresponding levels
HEADER_PATTERNS = [
    HeaderPattern(
        pattern=r"^第[一二三四五六七八九十０-９]+部【",
        level=HeaderLevel.PART,
        description="Part level (第一部, 第二部)",
    ),
    HeaderPattern(
        pattern=r"^第[一二三四五六七八九十０-９１-９]+【",
        level=HeaderLevel.CHAPTER,
        description="Chapter level (第１, 第２)",
    ),
    HeaderPattern(
        pattern=r"^[１-９0-9]+【",
        level=HeaderLevel.SECTION,
        description="Section level (１, ２)",
    ),
    HeaderPattern(
        pattern=r"^(\([１-９0-9A-Za-z]+\)|（[１-９0-9A-Za-z]+）|[①-⑩])",
        level=HeaderLevel.SUBSECTION,
        description="Subsection level (parenthetical or circled numbers/letters)",
    ),
]


class TableFixer:
    """Class to handle table normalization"""

    @staticmethod
    def is_malformed_table_header(cells: List[str]) -> bool:
        """Check if table row is a malformed header with placeholder columns"""
        if len(cells) < 3:
            return False

        first_cell = cells[1].strip()
        # Check if first cell has parenthetical pattern (numbers or letters)
        if not re.match(r"^(\([１-９0-9A-Za-z]+\)|（[１-９0-9A-Za-z]+）|[①-⑩])", first_cell):
            return False

        # Check for Col# pattern in other cells
        other_cells = [c.strip() for c in cells[2:-1]]
        return any(re.match(r"^Col\d+$", cell) for cell in other_cells)

    @staticmethod
    def extract_date_from_cells(cells: List[str]) -> Optional[str]:
        """Extract date pattern from table cells"""
        for cell in cells[1:]:
            if cell.strip():
                match = re.search(r"\d{4}年\d{1,2}月\d{1,2}日現在", cell.strip())
                if match:
                    return match.group(0)
        return None

    @staticmethod
    def should_skip_row(cells: List[str]) -> bool:
        """Check if row should be skipped (e.g., all cells contain '当事業年度')"""
        non_empty_cells = [c.strip() for c in cells[1:-1] if c.strip()]
        return bool(non_empty_cells) and all(c == "当事業年度" for c in non_empty_cells)

    @staticmethod
    def create_separator(num_columns: int) -> str:
        """Create a markdown table separator line"""
        return "|" + "|".join(["---"] * num_columns) + "|"


class TOCExtractor:
    """Class to handle table of contents extraction"""

    @staticmethod
    def is_toc_start(line: str) -> bool:
        """Check if line marks the start of table of contents"""
        return bool(re.search(r"目\s*次", line) or line.strip() == "目次")

    @staticmethod
    def is_toc_entry(line: str) -> bool:
        """Check if line is a TOC entry with page number"""
        return bool(re.match(r"^.+[…．\s]+\d+\s*$", line))

    @staticmethod
    def extract_header_from_toc(line: str) -> Optional[str]:
        """Extract header text from TOC entry"""
        # Match patterns for different header types
        patterns = [
            r"^(第[一二三四五六七八九十０-９]+部【[^】]+】)[…\s]*(\d+)?",  # Part
            r"^(第[一二三四五六七八九十０-９１-９]+【[^】]+】)[…\s]*(\d+)?",  # Chapter
            r"^([１-９0-9]+【[^】]+】)[…\s]*(\d+)?",  # Section
            r"^(\([１-９0-9A-Za-z]+\)|（[１-９0-9A-Za-z]+）)\s*([^…]+)[…\s]*(\d+)?",  # Parenthetical
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                return match.group(1)
        return None


def fix_malformed_tables(text: str) -> str:
    """
    Fix malformed tables where headers are included in the table structure.

    Common patterns fixed:
    1. |（２）提出会社の状況|Col2|Col3|2024年３月31日現在|
    2. |① 提出会社|Col2|Col3|Col4|Col5|
    """
    lines = text.split("\n")
    fixed_lines = []
    i = 0
    table_fixer = TableFixer()

    while i < len(lines):
        line = lines[i]

        # Check if this line looks like a malformed table header
        if line.startswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1]

            # Check if next line is separator
            if re.match(r"^\|[\s\-:]+\|", next_line):
                cells = line.split("|")

                if table_fixer.is_malformed_table_header(cells):
                    first_cell = cells[1].strip()

                    # Check if header already exists
                    if i > 0 and lines[i - 1].strip() == f"#### {first_cell}":
                        i += 2  # Skip malformed row and separator
                        continue

                    # Add header as markdown
                    fixed_lines.append(f"#### {first_cell}")

                    # Add date if found
                    date = table_fixer.extract_date_from_cells(cells)
                    if date:
                        fixed_lines.append(date)

                    # Skip malformed header and separator
                    i += 2

                    # Skip rows with only "当事業年度"
                    while i < len(lines) and lines[i].startswith("|"):
                        row_cells = lines[i].split("|")
                        if table_fixer.should_skip_row(row_cells):
                            i += 1
                        else:
                            break

                    # Process remaining table rows
                    first_data_row = True
                    while i < len(lines) and lines[i].startswith("|"):
                        if first_data_row:
                            # Add the first data row (which is the actual header)
                            fixed_lines.append(lines[i])
                            i += 1
                            if i < len(lines) and lines[i].startswith("|"):
                                # Add separator after the header row
                                cells_count = len(lines[i-1].split("|")) - 2
                                fixed_lines.append(table_fixer.create_separator(cells_count))
                            first_data_row = False
                        else:
                            fixed_lines.append(lines[i])
                            i += 1
                    continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def extract_toc_headers(lines: List[str]) -> List[str]:
    """Extract headers from table of contents section"""
    toc_headers = []
    in_toc = False
    toc_extractor = TOCExtractor()

    for line in lines:
        if toc_extractor.is_toc_start(line):
            in_toc = True
            continue

        if in_toc:
            # Extract TOC entries
            header = toc_extractor.extract_header_from_toc(line)
            if header:
                toc_headers.append(header)
                continue

            # Check for end of TOC
            if "監査報告書" in line or "確認書" in line or "内部統制報告書" in line:
                in_toc = False

    return toc_headers


def determine_header_level(header: str) -> str:
    """Determine the markdown header level for a given header text"""
    for pattern_info in HEADER_PATTERNS:
        if re.match(pattern_info.pattern, header):
            return "#" * pattern_info.level.value + " "

    # Default to level 3
    return "### "


def is_header_line(line: str, toc_headers: List[str]) -> Optional[str]:
    """Check if a line should be marked as a header"""
    line_stripped = line.strip()

    # Skip TOC entries with page numbers
    if TOCExtractor.is_toc_entry(line_stripped):
        return None

    # Check against TOC headers
    for toc_header in toc_headers:
        if line_stripped == toc_header:
            return toc_header

    # Check for parenthetical/circled patterns not in TOC
    if not re.match(r".+[…．\s]+\d+\s*$", line_stripped):
        pattern = re.match(
            r"^(\([１-９0-9A-Za-z]+\)|（[１-９0-9A-Za-z]+）|[①-⑩])\s*(.+)$", line_stripped
        )
        if pattern and len(pattern.group(2)) > 2:
            return line_stripped

    return None


def normalize(markdown: str) -> str:
    """
    Normalize markdown text from 有価証券報告書 PDF.

    This function:
    1. Extracts headers from table of contents
    2. Fixes malformed tables
    3. Adds proper markdown header formatting
    4. Ensures consistent structure throughout the document
    """
    lines = markdown.splitlines()

    # Phase 1: Extract TOC headers
    toc_headers = extract_toc_headers(lines)

    # Phase 2: Process content and add markdown headers
    normalized_lines = []
    content_started = False

    for line in lines:
        # Check if we've reached actual content
        if not content_started:
            if line.strip() == "【表紙】" or re.match(
                r"^第[一二三四五六七八九十０-９]+部【", line.strip()
            ):
                content_started = True

        if not content_started:
            # Skip TOC entries before content starts
            if TOCExtractor.is_toc_entry(line):
                continue
            normalized_lines.append(line)
            continue

        # Special case: main document title
        if (
            re.match(r"^#*\s*有\s*価\s*証\s*券\s*報\s*告\s*書\s*$", line.strip())
            and len(normalized_lines) == 0
        ):
            normalized_lines.append("# 有価証券報告書")
            continue

        # Check if line should be a header
        header = is_header_line(line, toc_headers)
        if header:
            level_prefix = determine_header_level(header)
            normalized_lines.append(f"{level_prefix}{header}")
        else:
            normalized_lines.append(line)

    # Phase 3: Fix malformed tables
    normalized_text = "\n".join(normalized_lines)
    normalized_text = fix_malformed_tables(normalized_text)

    return normalized_text


def split_by_headers(markdown: str) -> Dict[str, str]:
    """
    Split normalized markdown into chunks by headers.
    Returns a dictionary with header as key and content as value.
    """
    lines = markdown.splitlines()
    chunks = {}
    current_header = None
    current_content = []

    for line in lines:
        if line.startswith("#"):
            # Save previous chunk
            if current_header:
                chunks[current_header] = "\n".join(current_content).strip()

            # Start new chunk
            current_header = line.lstrip("#").strip()
            current_content = []
        else:
            if current_header:
                current_content.append(line)

    # Save last chunk
    if current_header:
        chunks[current_header] = "\n".join(current_content).strip()

    return chunks


def extract_toc_structure(markdown: str) -> List[Tuple[str, int]]:
    """
    Extract table of contents structure with page numbers.
    Returns list of tuples (header_text, page_number).
    """
    lines = markdown.splitlines()
    toc_entries = []
    in_toc = False
    toc_extractor = TOCExtractor()

    for line in lines:
        if toc_extractor.is_toc_start(line):
            in_toc = True
            continue

        if in_toc:
            # End of TOC detection
            if "監査報告書" in line or "確認書" in line or "内部統制報告書" in line:
                pass  # Continue processing this line

            # Extract entries with page numbers
            match = re.match(r"^(.+?)[…．\s]+(\d+)\s*$", line)
            if match:
                header = match.group(1).strip()
                page = int(match.group(2).strip())

                # Validate header pattern
                if re.match(
                    r"^(第[一二三四五六七八九十０-９１-９]+[部【]|[１-９0-9]+【|\([１-９0-9A-Za-z]+\)|（[１-９0-9A-Za-z]+）)",
                    header,
                ):
                    toc_entries.append((header, page))

            # Check for actual content start
            if line.strip() in ["頁", "ページ"] or "第一部【企業情報】" in line:
                if not any(char.isdigit() for char in line):
                    break

    return toc_entries


def find_section(normalized_markdown: str, section_name: str) -> str:
    """
    Find a specific section by name in the normalized markdown.
    Returns the content of that section.
    """
    chunks = split_by_headers(normalized_markdown)

    # Try exact match first
    if section_name in chunks:
        return chunks[section_name]

    # Try partial match
    for header, content in chunks.items():
        if section_name in header:
            return content

    return ""


def get_section_hierarchy(normalized_markdown: str) -> Dict[str, List[str]]:
    """
    Get the hierarchical structure of sections.
    Returns a dictionary where keys are parent sections and values are lists of child sections.
    """
    lines = normalized_markdown.splitlines()
    hierarchy = {}
    current_headers: dict[HeaderLevel, Optional[str]] = {
        HeaderLevel.PART: None,
        HeaderLevel.CHAPTER: None,
        HeaderLevel.SECTION: None,
        HeaderLevel.SUBSECTION: None,
    }

    for line in lines:
        if not line.startswith("#"):
            continue

        # Count header level
        level_count = len(line) - len(line.lstrip("#"))
        header_text = line.lstrip("#").strip()

        # Update current headers
        try:
            level = HeaderLevel(level_count)
            current_headers[level] = header_text

            # Clear lower levels
            for lower_level in HeaderLevel:
                if lower_level.value > level.value:
                    current_headers[lower_level] = None

            # Add to hierarchy
            if header_text not in hierarchy:
                hierarchy[header_text] = []

            # Add as child to parent level if exists
            parent_level = HeaderLevel(level.value - 1) if level.value > 1 else None
            if parent_level and current_headers.get(parent_level):
                parent = current_headers[parent_level]
                if parent in hierarchy:
                    hierarchy[parent].append(header_text)
        except ValueError:
            # Invalid header level, skip
            pass

    return hierarchy
