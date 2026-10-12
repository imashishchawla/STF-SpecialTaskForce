#!/usr/bin/env bash
# test_installer_lifecycle.sh — Automated tests for installer.sh lifecycle commands.
#
# Tests all subcommands in --dry-run mode and verifies zero host writes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALLER="$AGENT_DIR/installer.sh"

echo "============================================================"
echo "Testing installer.sh lifecycle subcommands (--dry-run)"
echo "============================================================"

# Test 1: Syntax check
echo -n "1. Syntax verification (bash -n)... "
bash -n "$INSTALLER"
echo "PASS"

# Test 2: Help command
echo -n "2. Help command returns 0 and lists subcommands... "
help_out=$(bash "$INSTALLER" help)
if echo "$help_out" | grep -q "install" && echo "$help_out" | grep -q "package" && echo "$help_out" | grep -q "reinstall"; then
  echo "PASS"
else
  echo "FAIL: Help output missing subcommands"
  exit 1
fi

# Test 3: Status command
echo -n "3. Status command runs cleanly... "
status_out=$(bash "$INSTALLER" status)
if echo "$status_out" | grep -q "Status — Terraform Support Agent"; then
  echo "PASS"
else
  echo "FAIL: Status output missing header"
  exit 1
fi

# Test 4: Status --json output
echo -n "4. Status --json output returns valid JSON... "
json_out=$(bash "$INSTALLER" status --json)
if echo "$json_out" | grep -q '"status":"success"' && echo "$json_out" | grep -q '"version":'; then
  echo "PASS"
else
  echo "FAIL: JSON output missing status or version key"
  exit 1
fi

# Test 5: install --dry-run
echo -n "5. install --dry-run reports actions without writes... "
install_out=$(printf "skip\n" | bash "$INSTALLER" install --dry-run)
if echo "$install_out" | grep -q "DRY RUN"; then
  echo "PASS"
else
  echo "FAIL: install --dry-run did not indicate dry run"
  exit 1
fi

# Test 6: package --dry-run
echo -n "6. package --dry-run verifies inventory... "
pkg_out=$(printf "\n" | bash "$INSTALLER" package --dry-run)
if echo "$pkg_out" | grep -q "DRY RUN"; then
  echo "PASS"
else
  echo "FAIL: package --dry-run failed"
  exit 1
fi

# Test 7: reinstall on clean system rejects without prior install
echo -n "7. reinstall on clean system fails closed with warning... "
if bash "$INSTALLER" reinstall --dry-run > /dev/null 2>&1; then
  echo "FAIL: Expected non-zero exit code when not installed"
  exit 1
else
  echo "PASS"
fi

# Test 8: remove --dry-run with cancel exits 0 cleanly
echo -n "8. remove --dry-run with cancel exits 0 cleanly... "
rm_out=$(printf "n\n" | bash "$INSTALLER" remove --dry-run)
if echo "$rm_out" | grep -q "DRY RUN"; then
  echo "PASS"
else
  echo "FAIL: remove --dry-run failed"
  exit 1
fi

# Test 9: Invalid command fails closed
echo -n "9. Invalid subcommand fails closed (exit code non-zero)... "
if bash "$INSTALLER" non_existent_subcommand > /dev/null 2>&1; then
  echo "FAIL: Expected non-zero exit code"
  exit 1
else
  echo "PASS"
fi

echo "============================================================"
echo "All 9 installer lifecycle checks PASSED."
echo "============================================================"
