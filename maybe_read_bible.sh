#!/usr/bin/env bash

STAMP_FILE="$HOME/projects/bible-reader/.bible_prompt_last_date"
TODAY="$(date +%F)"

# Only prompt once per day
if [ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$TODAY" ]; then
	return 0 2>/dev/null || exit 0
fi

echo "$TODAY" >"$STAMP_FILE"
python "$HOME/projects/bible-reader/read_today.py"
