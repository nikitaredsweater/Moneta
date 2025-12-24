#!/bin/bash
# Test runner script for Moneta integration tests
# This script runs tests in Docker containers with an isolated test database.
#
# Usage:
#   ./scripts/run-tests.sh              # Run all tests
#   ./scripts/run-tests.sh unit         # Run only unit tests
#   ./scripts/run-tests.sh integration  # Run only integration tests
#   ./scripts/run-tests.sh auth         # Run auth router tests
#   ./scripts/run-tests.sh user         # Run user router tests
#   ./scripts/run-tests.sh coverage     # Run all tests with coverage report
#   ./scripts/run-tests.sh clean        # Clean up test containers and volumes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all           Run all tests (default)"
    echo "  unit          Run only unit tests"
    echo "  integration   Run only integration tests"
    echo "  auth          Run auth router integration tests"
    echo "  user          Run user router integration tests"
    echo "  coverage      Run all tests with coverage report"
    echo "  clean         Clean up test containers and volumes"
    echo "  shell         Open a shell in the test container"
    echo ""
}

run_tests() {
    local test_args="$1"
    echo -e "${GREEN}Starting test containers...${NC}"

    docker compose -f docker-compose.test.yml run --rm monolith-test \
        pytest $test_args -v --durations=10

    local exit_code=$?

    # Clean up
    docker compose -f docker-compose.test.yml down -v > /dev/null 2>&1

    return $exit_code
}

case "${1:-all}" in
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        run_tests "tests/"
        ;;
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        run_tests "tests/unit/"
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        run_tests "tests/integration/"
        ;;
    auth)
        echo -e "${GREEN}Running auth router tests...${NC}"
        run_tests "tests/integration/routers/test_auth.py"
        ;;
    user)
        echo -e "${GREEN}Running user router tests...${NC}"
        run_tests "tests/integration/routers/test_user.py"
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage...${NC}"
        docker compose -f docker-compose.test.yml run --rm monolith-test \
            pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
        docker compose -f docker-compose.test.yml down -v > /dev/null 2>&1
        echo -e "${GREEN}Coverage report generated in monolith/htmlcov/${NC}"
        ;;
    clean)
        echo -e "${YELLOW}Cleaning up test containers and volumes...${NC}"
        docker compose -f docker-compose.test.yml down -v --remove-orphans
        echo -e "${GREEN}Cleanup complete.${NC}"
        ;;
    shell)
        echo -e "${GREEN}Opening shell in test container...${NC}"
        docker compose -f docker-compose.test.yml run --rm monolith-test /bin/bash
        docker compose -f docker-compose.test.yml down -v > /dev/null 2>&1
        ;;
    help|-h|--help)
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        print_usage
        exit 1
        ;;
esac
