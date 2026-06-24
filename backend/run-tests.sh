#!/bin/bash
# =============================================================================
# Backend Integration Test Runner
# =============================================================================
# Runs backend integration tests against real services using Docker Compose.
#
# Usage:
#   ./backend/run-tests.sh                    # Run all tests
#   ./backend/run-tests.sh -k "test_upload"   # Run tests matching pattern
#   ./backend/run-tests.sh -m "not slow"      # Skip slow tests
#   ./backend/run-tests.sh -m "not openai"    # Skip OpenAI tests
#   ./backend/run-tests.sh --fast             # Alias for -m "not slow"
#   ./backend/run-tests.sh --no-openai        # Alias for -m "not openai"
#   ./backend/run-tests.sh -- src/app/modules/core/pdf/tests.py -v  # Run specific module
#
# Environment variables:
#   PYTEST_ARGS     - Additional pytest arguments
#
# Required for OpenAI tests (set in .env):
#   AZURE_OPENAI_API_KEY      - Azure OpenAI API key
#   AZURE_OPENAI_BASE_URL     - Azure OpenAI endpoint URL
#   AZURE_OPENAI_API_VERSION  - API version (e.g., 2024-10-21)
#
# Note: OpenAI tests are automatically skipped if credentials are not available.
# =============================================================================

set -e

# Navigate to project root (parent of backend folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Parse convenience flags
PYTEST_EXTRA_ARGS=""
for arg in "$@"; do
    case $arg in
        --fast)
            PYTEST_EXTRA_ARGS="$PYTEST_EXTRA_ARGS -m 'not slow'"
            shift
            ;;
        --no-openai)
            PYTEST_EXTRA_ARGS="$PYTEST_EXTRA_ARGS -m 'not openai'"
            shift
            ;;
        *)
            PYTEST_EXTRA_ARGS="$PYTEST_EXTRA_ARGS $arg"
            ;;
    esac
done

# Combine with any PYTEST_ARGS env var
FINAL_PYTEST_ARGS="${PYTEST_ARGS:-} $PYTEST_EXTRA_ARGS"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Backend Integration Test Runner"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Run tests
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "▶ Running tests"
echo "  Args: $FINAL_PYTEST_ARGS"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Export PYTEST_ARGS for the compose command
export PYTEST_ARGS="$FINAL_PYTEST_ARGS"

# Run tests using the test profile
docker compose --profile test run --rm backend-test

TEST_EXIT_CODE=$?

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "   ✓ All tests passed!"
else
    echo "   ✗ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"

exit $TEST_EXIT_CODE
