#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STAMP_FILE="$SCRIPT_DIR/.bible_prompt_last_date"
LOCK_DIR="$SCRIPT_DIR/.bible_prompt.lockdir"

# Ensure only one instance runs this prompt workflow at a time.
# This lock prevents duplicate same-day prompting/stamp races in the shell layer.
# read_today.py uses a separate lock for the counter file update path.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
	# Another instance is already handling today's prompt.
	exit 0
fi

cleanup() {
	# Release lock directory on all exit paths.
	if [[ -d "$LOCK_DIR" ]]; then
		if ! rmdir "$LOCK_DIR"; then
			rc=$?
			echo "Warning: failed to remove lock directory $LOCK_DIR (exit code $rc). Manual removal may be required." >&2
		fi
	fi
}
trap cleanup EXIT
TODAY="$(date +%F)"

reader_args=()
for arg in "$@"; do
	case "$arg" in
	--debug)
		reader_args+=("$arg")
		;;
	*)
		echo "Unknown option for maybe_read_bible.sh: $arg" >&2
		echo "Supported options: --debug" >&2
		exit 2
		;;
	esac
done

# Only prompt once per day
last_stamp=""
if [[ -f "$STAMP_FILE" ]]; then
	# Use read with explicit error handling instead of cat in a command substitution,
	# to avoid unintended exits under `set -e` if the file is unreadable or empty/whitespace-only,
	# which would cause read to return a non-zero status.
	if ! IFS= read -r last_stamp <"$STAMP_FILE"; then
		last_stamp=""
	fi
fi
if [[ "$last_stamp" = "$TODAY" ]]; then
	return 0 2>/dev/null || exit 0
fi

# Run the reading script and branch by explicit completion status.
if python3 "$SCRIPT_DIR/read_today.py" "${reader_args[@]}"; then
	status=0
else
	status=$?
fi

case "$status" in
0)
	# Reading was marked complete in read_today.py; record completion for today.
	echo "$TODAY" >"$STAMP_FILE"
	exit 0
	;;
2)
	# User chose not to mark complete; do not stamp.
	exit 2
	;;
*)
	# Real error in read_today.py; do not stamp and propagate failure.
	echo "read_today.py failed with exit code $status" >&2
	exit "$status"
	;;
esac
