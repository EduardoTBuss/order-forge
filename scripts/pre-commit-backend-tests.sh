#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Pre-commit wrapper for backend pytest.
#
# Optimisations over running `run-tests.sh` directly:
#   1. Skips Docker service startup when services are already running.
#   2. Detects which backend modules have staged changes and runs only
#      those tests instead of the full suite.
#   3. If no testable module was changed, skips pytest entirely.
#
# Safeguards (added 2026-05-24 after a Postgres pool-exhaustion incident):
#   4. Pre-flight check: refuses to start the test container when Postgres
#      is already at >=70% of `max_connections`. Otherwise a leak from a
#      previous aborted run (e.g. a stale `backend-test` container) compounds
#      with the new run and locks every Postgres-using process out.
#   5. EXIT trap that force-removes the `backend-test` service even if the
#      script is killed mid-run (Ctrl-C, parent prek timeout, etc.). The
#      `--rm` on `docker compose run` only fires on a clean exit; the trap
#      covers the rest.
# ---------------------------------------------------------------------------

log() { printf "  %s\n" "$*" >&2; }

# Pre-flight: refuse to run when Postgres is already congested.
preflight_pg_connections() {
    # Skip the check if postgres isn't running yet — ensure_docker_compose_up
    # will start it shortly.
    docker compose ps postgres --status running -q 2>/dev/null | grep -q . || return 0

    local in_use max threshold
    in_use=$(docker compose exec -T postgres \
        psql -U postgres -d postgres -tAc \
        "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null \
        | tr -d ' [:cntrl:]' || echo "")
    max=$(docker compose exec -T postgres \
        psql -U postgres -d postgres -tAc \
        "SHOW max_connections;" 2>/dev/null \
        | tr -d ' [:cntrl:]' || echo "")

    # If psql returned non-numeric (e.g. itself blocked by "too many clients
    # already"), treat that as the worst case — bail loudly with recovery hints.
    if ! [[ "$in_use" =~ ^[0-9]+$ ]] || ! [[ "$max" =~ ^[0-9]+$ ]]; then
        log "  ✗ Postgres is unreachable (likely already at max_connections)."
        log "  ✗ Aborting test run to avoid worsening the situation."
        log "  → Inspect:  docker logs --tail 20 invoice-workshop-postgres-1"
        log "  → Restart:  docker restart invoice-workshop-backend-1   # frees the backend's pool"
        log "  → Nuclear: docker compose restart postgres     # nukes every connection"
        exit 1
    fi

    threshold=$(( max * 70 / 100 ))
    if (( in_use > threshold )); then
        log "  ✗ Postgres is at ${in_use} / ${max} connections (threshold ${threshold})."
        log "  ✗ Refusing to start the test container — would risk exhausting the pool."
        log "  → Inspect: docker exec invoice-workshop-postgres-1 psql -U postgres -d postgres -c \\"
        log "             \"SELECT pid, usename, application_name, state, query_start FROM pg_stat_activity ORDER BY query_start NULLS LAST;\""
        log "  → Stale test container?  docker compose --profile test rm -fsv backend-test"
        log "  → Leaky dev backend?     docker restart invoice-workshop-backend-1"
        exit 1
    fi
}

# Cleanup: force-remove the ephemeral test container on script exit.
# `docker compose run --rm` cleans up on a clean exit; this trap covers
# signal, timeout, and unexpected-error paths.
cleanup_test_container() {
    docker compose --profile test rm -fsv backend-test >/dev/null 2>&1 || true
}
trap cleanup_test_container EXIT INT TERM

# ---------------------------------------------------------------------------
# 1. Ensure Docker compose services are running for backend tests.
# ---------------------------------------------------------------------------
ensure_docker_compose_up() {
    local services=(postgres blobstorage backend)
    for svc in "${services[@]}"; do
        if ! docker compose ps "$svc" --status running -q 2>/dev/null | grep -q .; then
             log "  ✓ Services already running"
            return 0
        fi
    done

    log "  → Starting Docker services: $services"
    docker compose up -d $services >/dev/null 2>&1

    log "  → Waiting for services to be healthy..."
    # Wait for postgres to be healthy
    local retries=30
    while ! docker compose exec -T postgres pg_isready -U postgres -d postgres >/dev/null 2>&1; do
        retries=$((retries - 1))
        if [ $retries -le 0 ]; then
        log "  ✗ Postgres failed to become ready"
        exit 1
        fi
        sleep 1
    done

    # Wait for backend to be ready using Python (curl may not be installed)
    retries=30
    while ! docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/core/info/health', timeout=2)" >/dev/null 2>&1; do
        retries=$((retries - 1))
        if [ $retries -le 0 ]; then
        log "  ✗ Backend failed to become ready"
        exit 1
        fi
        sleep 1
    done

    log "  ✓ Services ready"
}

# ---------------------------------------------------------------------------
# 2. Resolve the set of tests.py files to run
# ---------------------------------------------------------------------------
resolve_test_files() {
    # Staged backend files that live inside src/app/modules/
    local module_files
    module_files=$(git diff --cached --name-only --diff-filter=ACMR \
        -- 'backend/src/app/modules/' 2>/dev/null || true)

    # Staged backend files *outside* modules (services, conftest, etc.)
    local infra_files
    infra_files=$(git diff --cached --name-only --diff-filter=ACMR \
        -- 'backend/src/' 'backend/conftest.py' 2>/dev/null \
        | grep -v 'backend/src/app/modules/' || true)

    # If infrastructure files changed, we can't know what's affected → run all
    if [ -n "$infra_files" ]; then
        echo "ALL"
        return
    fi

    # No module files changed → nothing to test
    if [ -z "$module_files" ]; then
        echo "NONE"
        return
    fi

    # Walk up from each changed file to find the nearest tests.py
    local -A seen
    local test_files=()

    while IFS= read -r file; do
        local rel="${file#backend/}"
        local dir
        dir=$(dirname "$rel")

        while [ "$dir" != "src/app/modules" ] && [ "$dir" != "." ]; do
            if [ -f "backend/${dir}/tests.py" ]; then
                if [ -z "${seen[$dir]+_}" ]; then
                    seen[$dir]=1
                    test_files+=("${dir}/tests.py")
                fi
                break
            fi
            dir=$(dirname "$dir")
        done
    done <<< "$module_files"

    if [ ${#test_files[@]} -eq 0 ]; then
        echo "NONE"
        return
    fi

    printf '%s\n' "${test_files[@]}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
test_target=$(resolve_test_files)

case "$test_target" in
    NONE)
        log "→ No testable backend modules changed — skipping pytest"
        exit 0
        ;;
    ALL)
        ensure_docker_compose_up
        preflight_pg_connections
        log "→ Infrastructure files changed — running full test suite"
        # NOTE: `exec` is intentionally NOT used here — we need this script's
        # EXIT trap to fire after run-tests.sh returns (so the test container
        # gets cleaned up even when pytest itself exits non-zero).
        PYTEST_ARGS="--tb=short" ./backend/run-tests.sh
        ;;
    *)
        ensure_docker_compose_up
        preflight_pg_connections
        file_list=$(echo "$test_target" | tr '\n' ' ')
        log "→ Running tests for changed modules: $file_list"
        # Same: no `exec`, so the cleanup trap can run.
        PYTEST_ARGS="--tb=short ${file_list}" ./backend/run-tests.sh
        ;;
esac
