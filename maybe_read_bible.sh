#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STAMP_FILE="$SCRIPT_DIR/.bible_prompt_last_date"
LOCK_DIR="$SCRIPT_DIR/.bible_prompt.lockdir"
LOCK_PID_FILE="$LOCK_DIR/pid"

get_proc_start_time() {
	local pid="$1"
	local stat_contents rest

	[[ -r "/proc/$pid/stat" ]] || return 1
	if ! IFS= read -r stat_contents <"/proc/$pid/stat"; then
		return 1
	fi

	# Drop the leading "pid (comm) " prefix so field 1 becomes the process state.
	rest="${stat_contents#*) }"
	set -- $rest
	[[ $# -ge 20 ]] || return 1
	printf '%s\n' "$20"
}

write_lock_metadata() {
	local start_time

	if ! start_time="$(get_proc_start_time "$$")"; then
		echo "Bible prompt skipped: could not determine start time for PID $$" >&2
		return 1
	fi

	printf '%s %s\n' "$$" "$start_time" >"$LOCK_PID_FILE"
}

lock_matches_running_process() {
	local pid="$1"
	local expected_start_time="$2"
	local actual_start_time

	[[ "$pid" =~ ^[0-9]+$ ]] || return 1
	[[ "$expected_start_time" =~ ^[0-9]+$ ]] || return 1
	kill -0 "$pid" 2>/dev/null || return 1

	if ! actual_start_time="$(get_proc_start_time "$pid")"; then
		return 1
	fi

	[[ "$actual_start_time" == "$expected_start_time" ]]
}

acquire_lock() {
	if mkdir "$LOCK_DIR" 2>/dev/null; then
		write_lock_metadata
		return 0
	fi

	if [[ -f "$LOCK_PID_FILE" ]]; then
		stale_pid=""
		stale_start_time=""
		if ! read -r stale_pid stale_start_time <"$LOCK_PID_FILE"; then
			stale_pid=""
			stale_start_time=""
		fi

		if lock_matches_running_process "$stale_pid" "$stale_start_time"; then
			echo "Bible prompt skipped: lock held by running PID $stale_pid in $LOCK_DIR" >&2
			return 1
		fi

		echo "Bible prompt: removing stale lock for PID ${stale_pid:-unknown} at $LOCK_DIR" >&2
	else
		echo "Bible prompt: removing stale lock with no PID file at $LOCK_DIR" >&2
	fi

	rm -f "$LOCK_PID_FILE"
	if ! rmdir "$LOCK_DIR" 2>/dev/null; then
		echo "Bible prompt skipped: could not clear existing lock directory at $LOCK_DIR" >&2
		return 1
	fi

	if mkdir "$LOCK_DIR" 2>/dev/null; then
		write_lock_metadata
		return 0
	fi

	echo "Bible prompt skipped: lock directory already exists at $LOCK_DIR" >&2
	return 1
}

# Ensure only one instance runs this prompt workflow at a time.
# This lock prevents duplicate same-day prompting/stamp races in the shell layer.
# read_today.py uses a separate lock for the counter file update path.
if ! acquire_lock; then
	exit 0
fi

cleanup() {
	# Release lock directory on all exit paths.
	if [[ -d "$LOCK_DIR" ]]; then
		rm -f "$LOCK_PID_FILE"
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
