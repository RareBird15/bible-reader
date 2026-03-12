import re
import os

INPUT_FILE = "plan.md"
OUTPUT_DIR = "days-commentary"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    text = f.read()

# split on headings like "# Day 1", "# Chapter 1", etc
sections = re.split(r"\n# ", text)

count = 1

for section in sections:
    section = section.strip()
    if not section:
        continue

    filename = f"{OUTPUT_DIR}/day{count:04}.txt"

    with open(filename, "w", encoding="utf-8") as out:
        out.write(section)

    count += 1

print(f"Created {count-1} reading files.")
