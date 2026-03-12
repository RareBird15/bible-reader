from pathlib import Path

SOURCE = Path.home() / "projects/bible-reader/days-commentary"
DEST = Path.home() / "projects/bible-reader/days"

DEST.mkdir(exist_ok=True)

for file in sorted(SOURCE.glob("day*.txt")):
    lines = file.read_text(encoding="utf-8").splitlines()

    scripture = []
    capture = False
    heading_count = 0

    for line in lines:
        if line.startswith("##"):
            heading_count += 1

            if heading_count == 1:
                capture = True
                continue

            if heading_count == 2:
                break

        if capture:
            scripture.append(line)

    # Trim leading/trailing blank lines
    while scripture and not scripture[0].strip():
        scripture.pop(0)

    while scripture and not scripture[-1].strip():
        scripture.pop()

    out_file = DEST / file.name
    out_file.write_text("\n".join(scripture) + "\n", encoding="utf-8")

print(f"Created scripture-only files in: {DEST}")
