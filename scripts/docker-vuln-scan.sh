#!/bin/bash
#
# Pre-commit hook for Docker image vulnerability scanning
# Uses Trivy (via Docker) to scan frontend and backend images for security vulnerabilities
#
# Requirements:
#   - Docker installed and running
#
# Configuration (via environment variables):
#   VULN_SEVERITY: Severity levels to fail on (default: HIGH,CRITICAL)
#   SKIP_VULN_SCAN: Set to "1" to skip the scan entirely
#   FORCE_BUILD: Set to "1" to force rebuild even if images exist

set -e

# Configuration
SEVERITY="${VULN_SEVERITY:-CRITICAL}"
TRIVY_IMAGE="aquasec/trivy:latest"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Results storage
RESULTS_DIR=$(mktemp -d)
FRONTEND_RESULT_FILE="$RESULTS_DIR/frontend.txt"
BACKEND_RESULT_FILE="$RESULTS_DIR/backend.txt"
FRONTEND_EXIT_CODE=0
BACKEND_EXIT_CODE=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${CYAN}${BOLD}$1${NC}"
}

cleanup() {
    rm -rf "$RESULTS_DIR"
}
trap cleanup EXIT

# Check if we should skip the scan
if [ "${SKIP_VULN_SCAN}" = "1" ]; then
    log_warning "Vulnerability scan skipped (SKIP_VULN_SCAN=1)"
    exit 0
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Pull Trivy image if not present
if ! docker image inspect "$TRIVY_IMAGE" >/dev/null 2>&1; then
    log_info "Pulling Trivy image..."
    docker pull "$TRIVY_IMAGE"
fi

# Get image name for a compose service
get_image_name() {
    local service=$1
    # Get image name from compose config and find matching image with tag
    local base_name
    base_name=$(docker compose config --images 2>/dev/null | grep -E "^.*-${service}$" | head -1)

    if [ -z "$base_name" ]; then
        echo ""
        return
    fi

    # Find the actual image with tag
    local full_name
    full_name=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep "^${base_name}:" | head -1)

    if [ -n "$full_name" ]; then
        echo "$full_name"
    else
        # Default to :latest if no tag found
        echo "${base_name}:latest"
    fi
}

# Check if image exists
image_exists() {
    local image=$1
    [ -n "$image" ] && [ "$image" != ":" ] && [ "$image" != "null:null" ] && docker image inspect "$image" >/dev/null 2>&1
}

# Check which files have changed (staged for commit)
check_changes() {
    local path=$1
    git diff --cached --name-only -- "$path" 2>/dev/null | grep -q .
}

# Build images using compose-build.sh
build_images() {
    local need_build=false

    # Get current image names
    FRONTEND_IMAGE=$(get_image_name "frontend")
    BACKEND_IMAGE=$(get_image_name "backend")

    # Check if build is needed
    if [ "${FORCE_BUILD}" = "1" ]; then
        need_build=true
        log_info "Force build requested"
    elif ! image_exists "$FRONTEND_IMAGE"; then
        need_build=true
        log_info "Frontend image not found, will build"
    elif ! image_exists "$BACKEND_IMAGE"; then
        need_build=true
        log_info "Backend image not found, will build"
    elif check_changes "frontend"; then
        need_build=true
        log_info "Frontend files changed, will rebuild"
    elif check_changes "backend"; then
        need_build=true
        log_info "Backend files changed, will rebuild"
    else
        log_info "Images are up to date"
    fi

    # Build using compose-build.sh
    if [ "$need_build" = true ]; then
        echo ""
        log_info "Running compose-build.sh..."
        echo ""

        if bash "$PROJECT_ROOT/scripts/compose-build.sh"; then
            log_success "Build completed"
        else
            log_error "Build failed"
            return 1
        fi

        # Refresh image names after build
        FRONTEND_IMAGE=$(get_image_name "frontend")
        BACKEND_IMAGE=$(get_image_name "backend")
    fi

    # Verify images exist
    if ! image_exists "$FRONTEND_IMAGE"; then
        log_error "Frontend image not found after build: $FRONTEND_IMAGE"
        return 1
    fi

    if ! image_exists "$BACKEND_IMAGE"; then
        log_error "Backend image not found after build: $BACKEND_IMAGE"
        return 1
    fi

    log_info "Frontend image: $FRONTEND_IMAGE"
    log_info "Backend image: $BACKEND_IMAGE"

    return 0
}

# Run trivy scan
run_trivy() {
    local image=$1
    docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$HOME/.cache/trivy:/root/.cache/" \
        "$TRIVY_IMAGE" image \
        --severity "$SEVERITY" \
        --ignore-unfixed \
        --scanners vuln \
        --exit-code 1 \
        --format table \
        "$image"
}

# Scan image for vulnerabilities
scan_image() {
    local name=$1
    local image=$2
    local result_file=$3
    local retry=${4:-false}

    log_info "Scanning $name for vulnerabilities (severity: $SEVERITY)..."
    log_info "Image: $image"
    echo ""

    local tmp_output
    tmp_output=$(mktemp)

    # Run with tee to show output in real-time and capture for error checking
    set +e
    run_trivy "$image" 2>&1 | tee "$tmp_output"
    local exit_code=${PIPESTATUS[0]}
    set -e

    # Check for bbolt cache corruption and retry with fresh cache
    if grep -q "invalid page type" "$tmp_output" && [ "$retry" = "false" ]; then
        log_warning "Trivy cache corrupted, clearing and retrying..."
        rm -rf "$HOME/.cache/trivy"
        rm -f "$tmp_output"
        scan_image "$name" "$image" "$result_file" "true"
        return $?
    fi

    # Store result
    cp "$tmp_output" "$result_file"
    rm -f "$tmp_output"

    echo ""
    return $exit_code
}

# Print summary
print_summary() {
    local has_failures=0

    if [ "$FRONTEND_EXIT_CODE" -ne 0 ]; then
        has_failures=1
    fi
    if [ "$BACKEND_EXIT_CODE" -ne 0 ]; then
        has_failures=1
    fi

    # Always show scan results
    echo ""
    echo "========================================"
    log_header "        SCAN RESULTS"
    echo "========================================"
    echo ""

    echo "----------------------------------------"
    log_header "Frontend Scan Results:"
    echo "----------------------------------------"
    cat "$FRONTEND_RESULT_FILE"
    echo ""

    echo "----------------------------------------"
    log_header "Backend Scan Results:"
    echo "----------------------------------------"
    cat "$BACKEND_RESULT_FILE"
    echo ""

    # Summary
    echo "========================================"
    log_header "           SUMMARY"
    echo "========================================"
    echo ""

    # Frontend summary
    if [ "$FRONTEND_EXIT_CODE" -eq 0 ]; then
        echo -e "  Frontend:  ${GREEN}PASSED${NC} - No $SEVERITY vulnerabilities"
    else
        echo -e "  Frontend:  ${RED}FAILED${NC} - Has $SEVERITY vulnerabilities"
    fi

    # Backend summary
    if [ "$BACKEND_EXIT_CODE" -eq 0 ]; then
        echo -e "  Backend:   ${GREEN}PASSED${NC} - No $SEVERITY vulnerabilities"
    else
        echo -e "  Backend:   ${RED}FAILED${NC} - Has $SEVERITY vulnerabilities"
    fi

    echo ""
    echo "========================================"

    if [ "$has_failures" -eq 1 ]; then
        echo ""
        log_error "Vulnerability scan failed!"
        echo ""
        echo "Options:"
        echo "  - Fix the vulnerabilities in your Dockerfiles"
        echo "  - Skip this check (not recommended): SKIP_VULN_SCAN=1 git commit ..."
        echo "  - Scan for critical only: VULN_SEVERITY=CRITICAL git commit ..."
        echo ""
        return 1
    fi

    echo ""
    log_success "All vulnerability scans passed!"
    echo ""
    return 0
}

# Main execution
main() {
    echo ""
    echo "========================================"
    log_header "    Docker Vulnerability Scan"
    echo "========================================"
    echo ""

    cd "$PROJECT_ROOT"

    # Build phase
    log_header "BUILD PHASE"
    echo ""
    if ! build_images; then
        exit 1
    fi

    echo ""
    echo "========================================"
    log_header "SCAN PHASE"
    echo "========================================"
    echo ""

    # Scan frontend
    log_header "[ Frontend ]"
    scan_image "Frontend" "$FRONTEND_IMAGE" "$FRONTEND_RESULT_FILE" || FRONTEND_EXIT_CODE=$?

    echo ""

    # Scan backend
    log_header "[ Backend ]"
    scan_image "Backend" "$BACKEND_IMAGE" "$BACKEND_RESULT_FILE" || BACKEND_EXIT_CODE=$?

    # Print summary and exit with appropriate code
    print_summary
    exit $?
}

main "$@"
