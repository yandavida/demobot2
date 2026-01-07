import pathlib


def test_no_core_imports_api():
    root = pathlib.Path(__file__).parents[2] / "core"
    bad_lines = []
    for p in root.rglob("*.py"):
        # skip compiled or hidden
        text = p.read_text(encoding="utf8")
        for i, line in enumerate(text.splitlines(), start=1):
            if "from api." in line or "import api." in line:
                bad_lines.append(f"{p}:{i}: {line.strip()}")
    assert not bad_lines, "Found core importing api: \n" + "\n".join(bad_lines)
