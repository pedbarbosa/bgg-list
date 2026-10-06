#!/bin/sh
# Fetches the collection, serves the web page, and refreshes the collection
# every BGG_REFRESH_HOURS. With arguments, runs bgg-list with them instead.
set -eu

if [ "$#" -gt 0 ]; then
    exec bgg-list "$@"
fi

: "${BGG_API_KEY:?Set BGG_API_KEY to your BoardGameGeek API key}"
: "${BGG_USERS:?Set BGG_USERS to comma-separated BoardGameGeek usernames}"
REFRESH_HOURS="${BGG_REFRESH_HOURS:-24}"
DATA=/app/site/collection.json

case "$REFRESH_HOURS" in
    ''|*[!0-9]*|0)
        echo "BGG_REFRESH_HOURS must be a whole number of hours, 1 or more" >&2
        exit 2
        ;;
esac

refresh() {
    # Write a new file and swap it in, so visitors never get a half-written one.
    # BGG_OPTIONS is split into words on purpose, for options such as -x.
    # shellcheck disable=SC2086
    if bgg-list -u "$BGG_USERS" --no-csv --no-table --json "$DATA.new" ${BGG_OPTIONS:-} && [ -s "$DATA.new" ]; then
        mv "$DATA.new" "$DATA"
    else
        rm -f "$DATA.new"
        echo "Refreshing the collection failed; serving the previous data, if any." >&2
    fi
}

refresh

(
    while sleep "$((REFRESH_HOURS * 3600))"; do
        refresh
    done
) &
refresher=$!

python -m http.server "$PORT" --directory /app/site &
server=$!

# The shell runs as PID 1, so pass docker stop's signal on to both processes
trap 'kill "$server" "$refresher" 2>/dev/null; exit 0' TERM INT
wait "$server"
