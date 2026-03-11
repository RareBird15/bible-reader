from pathlib import Path

BASE = Path.home() / "projects/bible-reader/days"
COUNTER = Path.home() / "projects/bible-reader/current_day.txt"

FIRST_FILE = 2
LAST_FILE = 1190

if not COUNTER.exists():
    COUNTER.write_text(str(FIRST_FILE), encoding="utf-8")

day = int(COUNTER.read_text(encoding="utf-8").strip())

if day > LAST_FILE:
    print("You have reached the end of the reading plan.")
    raise SystemExit

file = BASE / f"day{day:04}.txt"
lines = [
    line.replace("\u00a0", " ")
    for line in file.read_text(encoding="utf-8").splitlines()
]

scripture = lines

commentary_file = (
    Path.home() / "projects/bible-reader/days-commentary" / f"day{day:04}.txt"
)
commentary_lines = [
    line.strip()
    for line in commentary_file.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

day_label = commentary_lines[0]
reference = commentary_lines[1]

print()
print(day_label)
print(reference)
print()

for line in scripture:
    cleaned = line.replace("\u00a0", " ").rstrip()
    print(cleaned)

print()

answer = input("Mark this reading complete? (y/n): ").strip().lower()

if answer == "y":
    COUNTER.write_text(str(day + 1), encoding="utf-8")
    print("Advanced to next day.")
else:
    print("Keeping your place.")
