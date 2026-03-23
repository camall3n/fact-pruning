#!/usr/bin/env python3
"""Convert HTML tables to LaTeX format."""

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path


# Row name mappings (original -> display name)
ROW_NAMES = {
    "translator_operators - Sum": "Actions - Sum",
    "translator_facts - Sum": "Facts - Sum",
    "translator_variables - Sum": "Variables - Sum",
    "translator_task_size - Sum": "Task Size - Sum",
    "translator_time_done - Sum": "Translation (s) - Sum",
    "coverage - Sum": "Coverage - Sum",
    "pruning_time - Sum": "Pruning (s) - Sum",
    "search_time - Sum": "Search (s) - Sum",
    "total_time - Sum": "Total (s) - Sum",
}

# Row order (use display names)
ROW_ORDER = [
    "Actions - Sum",
    "Facts - Sum",
    "Variables - Sum",
    "Task Size - Sum",
    "Coverage - Sum",
    "Pruning (s) - Sum",
    "Translation (s) - Sum",
    "Search (s) - Sum",
    "Total (s) - Sum",
]

# Insert midrule after these rows (use display names)
MIDRULE_AFTER = {"Task Size - Sum"}


class SummaryTableParser(HTMLParser):
    """Parse HTML and extract only the Summary table."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_cell = False
        self.is_header = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif tag == "tr" and self.in_table:
            self.current_row = []
        elif tag in ("td", "th") and self.in_table:
            self.in_cell = True
            self.is_header = tag == "th"
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table":
            if self.current_table:
                self.tables.append(self.current_table)
            self.in_table = False
            self.current_table = []
        elif tag == "tr" and self.in_table:
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag in ("td", "th") and self.in_table:
            self.in_cell = False
            self.current_row.append((self.current_cell.strip(), self.is_header))

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data

    def get_summary_table(self):
        """Return the table that starts with 'Summary' in the first cell."""
        for table in self.tables:
            if table and table[0]:
                first_cell = table[0][0][0]
                if first_cell == "Summary":
                    return table
        return None


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def rename_row(name: str) -> str:
    """Rename a row label using the mapping."""
    return ROW_NAMES.get(name, name)


def sort_rows(rows: list) -> list:
    """Sort data rows according to ROW_ORDER, keeping header first."""
    if not rows:
        return rows

    header = rows[0]
    data_rows = rows[1:]

    # Create order mapping
    order = {name: i for i, name in enumerate(ROW_ORDER)}

    def sort_key(row):
        if not row:
            return float("inf")
        row_name = rename_row(row[0][0])
        return order.get(row_name, float("inf"))

    sorted_data = sorted(data_rows, key=sort_key)
    return [header] + sorted_data


def html_to_latex(html_content: str, caption: str = None, label: str = None) -> str:
    """Convert HTML table to LaTeX."""
    parser = SummaryTableParser()
    parser.feed(html_content)

    rows = parser.get_summary_table()
    if not rows:
        return ""

    # Sort rows according to ROW_ORDER
    rows = sort_rows(rows)

    num_cols = len(rows[0])
    col_spec = "l" + "r" * (num_cols - 1)

    lines = []
    lines.append(r"\begin{table*}[tbp!]")
    lines.append(r"    \centering")
    lines.append(r"    \resizebox{\linewidth}{!}{")
    lines.append(f"    \\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"        \toprule")

    for i, row in enumerate(rows):
        cells = []
        row_name = None
        for j, (cell_text, is_header) in enumerate(row):
            # Rename first column of data rows
            if j == 0 and i > 0:
                cell_text = rename_row(cell_text)
                row_name = cell_text
            escaped = escape_latex(cell_text)
            if is_header:
                cells.append(r"\textbf{" + escaped + "}")
            else:
                cells.append(escaped)
        line = "        " + " & ".join(cells) + r" \\"
        lines.append(line)

        # Add midrule after header or after specific rows
        if i == 0:
            lines.append(r"        \midrule")
        elif row_name in MIDRULE_AFTER:
            lines.append(r"        \midrule")

    lines.append(r"        \bottomrule")
    lines.append(r"    \end{tabular}")
    lines.append(r"    }")

    if caption:
        lines.append(f"    \\caption{{{caption}}}")
    if label:
        lines.append(f"    \\label{{{label}}}")

    lines.append(r"\end{table*}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Convert HTML tables to LaTeX format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.html                     # Output to stdout
  %(prog)s input.html -o output.tex       # Output to file
  %(prog)s input.html -c "My Table"       # Add caption
  %(prog)s input.html -l tab:results      # Add label
  cat table.html | %(prog)s               # Read from stdin
        """,
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=str,
        default="-",
        help="Input HTML file (default: stdin)",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output LaTeX file (default: stdout)"
    )
    parser.add_argument("-c", "--caption", type=str, help="Table caption")
    parser.add_argument(
        "-l", "--label", type=str, help="Table label for cross-references"
    )

    args = parser.parse_args()

    # Read input
    if args.input == "-":
        html_content = sys.stdin.read()
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        html_content = input_path.read_text()

    # Convert
    latex_output = html_to_latex(html_content, args.caption, args.label)

    if not latex_output:
        print("Error: No Summary table found in input", file=sys.stderr)
        sys.exit(1)

    # Write output
    if args.output:
        Path(args.output).write_text(latex_output + "\n")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(latex_output)


if __name__ == "__main__":
    main()
