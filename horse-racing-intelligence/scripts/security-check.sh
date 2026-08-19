#!/usr/bin/env sh
set -eu
printf 'Checking ignored sensitive/local artifacts...\n'
for path in .env node_modules/x frontend/node_modules/x logs/x secrets/x credentials/x; do
  git check-ignore -q "$path" || { printf 'NOT IGNORED: %s\n' "$path" >&2; exit 1; }
done
printf 'Searching tracked files for secret markers...\n'
if git grep -nEI 'BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}' -- ':!*.example' 2>/dev/null; then
  echo 'Potential secret found.' >&2; exit 1
fi
printf 'OK\n'
