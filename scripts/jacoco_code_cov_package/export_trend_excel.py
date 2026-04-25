#!/usr/bin/env python3
import argparse
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_percent_line(line: str) -> float | None:
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)%", line)
    if not m:
        return None
    return float(m.group(1))


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", s)
            if m:
                return float(m.group(1))
    return None


def parse_coverage_txt(file_path: Path) -> dict | None:
    branch = None
    line_cov = None
    method = None

    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return None

    for line in lines:
        lower = line.lower()
        if "branch" in lower and branch is None:
            branch = parse_percent_line(line)
        elif "line" in lower and line_cov is None:
            line_cov = parse_percent_line(line)
        elif "method" in lower and method is None:
            method = parse_percent_line(line)

    if branch is None and line_cov is None and method is None:
        return None

    return {
        "file": file_path.name,
        "branch_coverage": branch,
        "line_coverage": line_cov,
        "method_coverage": method,
    }


def _col_to_index(col_ref: str) -> int:
    idx = 0
    for ch in col_ref:
        if not ch.isalpha():
            break
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return max(idx - 1, 0)


def _load_xlsx_rows(xlsx_path: Path) -> list[list]:
    rows: list[list] = []
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    with zipfile.ZipFile(xlsx_path) as zf:
        shared_strings = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sroot = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sroot.findall("a:si", ns):
                texts = [t.text or "" for t in si.findall(".//a:t", ns)]
                shared_strings.append("".join(texts))

        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            sheets = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
            if not sheets:
                return rows
            sheet_name = sorted(sheets)[0]

        root = ET.fromstring(zf.read(sheet_name))
        for row in root.findall(".//a:sheetData/a:row", ns):
            cells: dict[int, object] = {}
            max_idx = -1
            for c in row.findall("a:c", ns):
                ref = c.attrib.get("r", "A1")
                col_ref = "".join(ch for ch in ref if ch.isalpha()) or "A"
                idx = _col_to_index(col_ref)
                max_idx = max(max_idx, idx)

                c_type = c.attrib.get("t")
                val = None
                if c_type == "inlineStr":
                    texts = [t.text or "" for t in c.findall(".//a:is/a:t", ns)]
                    val = "".join(texts)
                else:
                    v = c.find("a:v", ns)
                    if v is not None:
                        raw = v.text
                        if c_type == "s":
                            try:
                                val = shared_strings[int(raw)]
                            except Exception:
                                val = raw
                        else:
                            val = raw

                cells[idx] = val

            if max_idx < 0:
                continue
            row_vals = [cells.get(i) for i in range(max_idx + 1)]
            rows.append(row_vals)

    return rows


def parse_coverage_xlsx(file_path: Path) -> list[dict]:
    rows_raw = _load_xlsx_rows(file_path)
    if not rows_raw:
        return []

    parsed: list[dict] = []
    header_map: dict[str, int] | None = None

    for i, row in enumerate(rows_raw, start=1):
        norm = [(str(v).strip() if v is not None else "") for v in row]
        lower = [v.lower() for v in norm]

        # Header-based parsing: file, branch_coverage, line_coverage, method_coverage
        if header_map is None:
            if any("branch" in x for x in lower) and any("line" in x for x in lower) and any("method" in x for x in lower):
                header_map = {}
                for idx, name in enumerate(lower):
                    if "file" in name:
                        header_map["file"] = idx
                    elif "branch" in name:
                        header_map["branch"] = idx
                    elif "line" in name:
                        header_map["line"] = idx
                    elif "method" in name:
                        header_map["method"] = idx
                continue

        if header_map is not None:
            branch = _to_float(row[header_map.get("branch", -1)] if header_map.get("branch", -1) < len(row) else None)
            line_cov = _to_float(row[header_map.get("line", -1)] if header_map.get("line", -1) < len(row) else None)
            method = _to_float(row[header_map.get("method", -1)] if header_map.get("method", -1) < len(row) else None)
            file_name = None
            file_idx = header_map.get("file", -1)
            if file_idx >= 0 and file_idx < len(row):
                file_name = (row[file_idx] or "").strip() if isinstance(row[file_idx], str) else row[file_idx]

            if branch is None and line_cov is None and method is None:
                continue

            parsed.append(
                {
                    "file": file_name or f"{file_path.stem}#{i}",
                    "branch_coverage": branch,
                    "line_coverage": line_cov,
                    "method_coverage": method,
                }
            )
            continue

        # Headerless compatibility for trend_data:
        # A often empty, B/C/D are branch/line/method numeric.
        branch = _to_float(row[1] if len(row) > 1 else None)
        line_cov = _to_float(row[2] if len(row) > 2 else None)
        method = _to_float(row[3] if len(row) > 3 else None)

        if branch is None and line_cov is None and method is None:
            # fallback when only 3 columns are used
            branch = _to_float(row[0] if len(row) > 0 else None)
            line_cov = _to_float(row[1] if len(row) > 1 else None)
            method = _to_float(row[2] if len(row) > 2 else None)

        if branch is None and line_cov is None and method is None:
            continue

        file_name = None
        if len(row) > 0 and isinstance(row[0], str):
            file_name = row[0].strip() or None

        parsed.append(
            {
                "file": file_name or f"{file_path.stem}#{i}",
                "branch_coverage": branch,
                "line_coverage": line_cov,
                "method_coverage": method,
            }
        )

    return parsed


def write_xlsx(rows: list[dict], output_path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError(
            "openpyxl is required to write xlsx. Install with: pip install openpyxl"
        ) from exc

    wb = Workbook()
    ws = wb.active
    ws.title = "trend_coverage"

    ws.append(["file", "branch_coverage", "line_coverage", "method_coverage"])

    for row in rows:
        ws.append([
            row.get("file"),
            row.get("branch_coverage"),
            row.get("line_coverage"),
            row.get("method_coverage"),
        ])

    wb.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate JaCoCo trend txt files into one Excel sheet."
    )
    parser.add_argument(
        "--service",
        required=True,
        help="Service name, e.g. project/person/user",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Optional custom input directory. Default: requests_coverage_data/<service>, fallback draw/trend_data",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output xlsx path. Default: requests_coverage_data/<service>/<service>_trend_coverage.xlsx",
    )
    parser.add_argument(
        "--last-n",
        type=int,
        default=200,
        help="Only aggregate the latest N txt files by filename sort order (default: 200). Use <=0 to include all.",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    if args.input_dir:
        input_dir = Path(args.input_dir).resolve()
    else:
        default_input = base_dir / "requests_coverage_data" / args.service
        fallback_input = Path(__file__).resolve().parents[2] / "draw" / "trend_data"
        input_dir = default_input if default_input.exists() else fallback_input

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        return 1

    txt_files = sorted(input_dir.glob("*.txt"))
    xlsx_files = sorted(input_dir.glob("*.xlsx"))

    if input_dir.name == "trend_data":
        # Prefer service-specific trend files in draw/trend_data.
        xlsx_files = [p for p in xlsx_files if p.name.startswith(f"{args.service}_")]

    if not txt_files and not xlsx_files:
        print(f"No txt/xlsx files found in: {input_dir}")
        return 1

    rows = []
    if txt_files:
        selected_txt = txt_files[-args.last_n:] if args.last_n > 0 else txt_files
        for txt_file in selected_txt:
            row = parse_coverage_txt(txt_file)
            if row:
                rows.append(row)

    if xlsx_files:
        selected_xlsx = xlsx_files[-args.last_n:] if args.last_n > 0 else xlsx_files
        for xlsx_file in selected_xlsx:
            rows.extend(parse_coverage_xlsx(xlsx_file))

    if args.last_n > 0 and rows:
        rows = rows[-args.last_n:]

    if not rows:
        print(f"No parseable coverage rows found in: {input_dir}")
        return 1

    output_path = (
        Path(args.output).resolve()
        if args.output
        else input_dir / f"{args.service}_trend_coverage.xlsx"
    )

    write_xlsx(rows, output_path)
    print(f"Wrote {len(rows)} rows to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
