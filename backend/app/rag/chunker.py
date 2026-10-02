"""Language-aware source code chunking with line number and symbol preservation."""

from typing import Any, Dict, List, Optional

from app.repository.parser import parse_generic_symbols, parse_python_ast


class CodeChunk:
    def __init__(
        self,
        chunk_id: str,
        repository_id: str,
        file_path: str,
        language: str,
        content: str,
        start_line: int,
        end_line: int,
        symbol_name: Optional[str] = None,
        symbol_kind: Optional[str] = None,
    ):
        self.chunk_id = chunk_id
        self.repository_id = repository_id
        self.file_path = file_path
        self.language = language
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.symbol_name = symbol_name or ""
        self.symbol_kind = symbol_kind or ""

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "repository_id": self.repository_id,
            "file_path": self.file_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol_name": self.symbol_name,
            "symbol_kind": self.symbol_kind,
        }


def chunk_code_file(
    content: str,
    file_path: str,
    repository_id: str,
    language: str,
    chunk_size_chars: int = 800,
    chunk_overlap_chars: int = 100,
) -> List[CodeChunk]:
    """
    Split source code into language-aware chunks while tracking line numbers and symbols.
    """
    if not content.strip():
        return []

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    chunks: List[CodeChunk] = []

    # If Python, try to use AST symbol boundaries
    symbols: List[Dict[str, Any]] = []
    if language == "python":
        ast_result = parse_python_ast(content)
        symbols = ast_result.get("symbols", [])
    elif language in ("javascript", "typescript", "java", "go"):
        symbols = parse_generic_symbols(content, language)

    # If symbols are present, create symbol-anchored chunks
    covered_ranges = []
    chunk_idx = 0

    for sym in symbols:
        start_l = sym["start_line"]
        end_l = sym["end_line"]
        # If the symbol spans multiple lines, extract its block
        if 1 <= start_l <= total_lines and 1 <= end_l <= total_lines and end_l >= start_l:
            block_lines = lines[start_l - 1: end_l]
            block_content = "".join(block_lines)

            # If block fits in ~ 2 * chunk_size, keep it intact
            if len(block_content) <= chunk_size_chars * 2:
                chunks.append(
                    CodeChunk(
                        chunk_id=f"{repository_id}:{file_path}:{start_l}-{end_l}:{chunk_idx}",
                        repository_id=repository_id,
                        file_path=file_path,
                        language=language,
                        content=block_content,
                        start_line=start_l,
                        end_line=end_l,
                        symbol_name=sym["name"],
                        symbol_kind=sym["kind"],
                    )
                )
                chunk_idx += 1
                covered_ranges.append((start_l, end_l))

    # If no symbols or for code outside covered ranges, use line-based sliding window
    # Also if the file is short, one chunk is sufficient
    if not chunks:
        current_chunk_lines = []
        current_chunk_len = 0
        chunk_start_line = 1

        for i, line in enumerate(lines, start=1):
            current_chunk_lines.append(line)
            current_chunk_len += len(line)

            if current_chunk_len >= chunk_size_chars:
                chunk_end_line = i
                chunk_text = "".join(current_chunk_lines)
                chunks.append(
                    CodeChunk(
                        chunk_id=f"{repository_id}:{file_path}:{chunk_start_line}-{chunk_end_line}:{chunk_idx}",
                        repository_id=repository_id,
                        file_path=file_path,
                        language=language,
                        content=chunk_text,
                        start_line=chunk_start_line,
                        end_line=chunk_end_line,
                    )
                )
                chunk_idx += 1

                # Calculate overlap lines
                overlap_lines = []
                overlap_len = 0
                for rev_line in reversed(current_chunk_lines):
                    if overlap_len + len(rev_line) <= chunk_overlap_chars:
                        overlap_lines.insert(0, rev_line)
                        overlap_len += len(rev_line)
                    else:
                        break

                current_chunk_lines = overlap_lines
                current_chunk_len = overlap_len
                chunk_start_line = i - len(overlap_lines) + 1

        # Final trailing chunk
        if current_chunk_lines:
            chunk_end_line = total_lines
            chunk_text = "".join(current_chunk_lines)
            if chunk_text.strip():
                chunks.append(
                    CodeChunk(
                        chunk_id=f"{repository_id}:{file_path}:{chunk_start_line}-{chunk_end_line}:{chunk_idx}",
                        repository_id=repository_id,
                        file_path=file_path,
                        language=language,
                        content=chunk_text,
                        start_line=chunk_start_line,
                        end_line=chunk_end_line,
                    )
                )

    return chunks
