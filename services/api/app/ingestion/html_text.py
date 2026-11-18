"""Convert the HTML found in MedlinePlus summaries into plain-text paragraphs.

Standard library only. Links keep their text, lists stay together as one
paragraph of "- item" lines, and each table becomes one paragraph with one line
per row and " | " between cells, so numbers stay attached to their labels.
Scripts and styles are dropped. The output is plain text; nothing here ever
produces HTML.
"""
import re
from html.parser import HTMLParser

_BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "br"}
_LIST_TAGS = {"ul", "ol"}
_CELL_TAGS = {"td", "th"}
_SKIP_TAGS = {"script", "style"}
_SPACE = re.compile(r"\s+")


class _ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._buffer: list[str] = []
        self._list_items: list[str] = []
        self._list_depth = 0
        self._in_item = False
        self._skip_depth = 0
        self._table_depth = 0
        self._table_rows: list[str] = []
        self._row_cells: list[str] = []
        self._in_cell = False

    def _flush_buffer(self):
        text = _SPACE.sub(" ", "".join(self._buffer)).strip()
        self._buffer = []
        return text

    def _end_block(self):
        text = self._flush_buffer()
        if text:
            self.paragraphs.append(text)

    def _end_item(self):
        text = self._flush_buffer()
        if text:
            self._list_items.append(f"- {text}")
        self._in_item = False

    def _finish_cell(self):
        text = self._flush_buffer()
        if self._in_cell:
            self._row_cells.append(text)
            self._in_cell = False
        elif text:  # stray text inside a table, such as a caption
            self._table_rows.append(text)

    def _finish_row(self):
        if any(self._row_cells):
            self._table_rows.append(" | ".join(self._row_cells))
        self._row_cells = []

    def _finish_table(self):
        self._finish_cell()
        self._finish_row()
        if self._table_rows:
            self.paragraphs.append("\n".join(self._table_rows))
        self._table_rows = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "table":
            if self._table_depth == 0:
                self._end_block()
            self._table_depth += 1
        elif self._table_depth:
            if tag == "tr":
                self._finish_cell()
                self._finish_row()
            elif tag in _CELL_TAGS:
                self._finish_cell()
                self._in_cell = True
            else:  # lists and blocks inside a table cell read as plain running text
                self._buffer.append(" ")
        elif tag in _LIST_TAGS:
            if self._list_depth == 0:
                self._end_block()
            self._list_depth += 1
        elif tag == "li":
            if self._in_item:
                self._end_item()
            self._in_item = True
        elif tag in _BLOCK_TAGS and self._list_depth == 0:
            self._end_block()

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "table":
            if self._table_depth:
                if self._table_depth == 1:
                    self._finish_table()
                self._table_depth -= 1
        elif self._table_depth:
            if tag in _CELL_TAGS:
                self._finish_cell()
            elif tag == "tr":
                self._finish_cell()
                self._finish_row()
            else:
                self._buffer.append(" ")
        elif tag == "li":
            self._end_item()
        elif tag in _LIST_TAGS:
            if self._in_item:
                self._end_item()
            self._list_depth = max(0, self._list_depth - 1)
            if self._list_depth == 0 and self._list_items:
                self.paragraphs.append("\n".join(self._list_items))
                self._list_items = []
        elif tag in _BLOCK_TAGS and self._list_depth == 0:
            self._end_block()

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._buffer.append(data)


def html_to_paragraphs(html: str) -> list[str]:
    """Return the text of `html` as a list of non-empty paragraphs."""
    parser = _ParagraphParser()
    parser.feed(html or "")
    parser.close()
    if parser._table_depth:  # unclosed table at end of input
        parser._table_depth = 0
        parser._finish_table()
    if parser._in_item:  # unclosed list item at end of input
        parser._end_item()
    if parser._list_items:  # unclosed list at end of input
        parser.paragraphs.append("\n".join(parser._list_items))
        parser._list_items = []
    parser._end_block()
    return parser.paragraphs
