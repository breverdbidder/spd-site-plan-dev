#!/bin/bash
# =============================================================================
# RALPHY SPRINT RUNNER - BidDeed.AI Integration
# =============================================================================
# Autonomous task execution loop that:
# 1. Fetches next task from Supabase sprint_tasks
# 2. Executes via Ralphy/Claude Code loop
# 3. Marks complete and moves to next
# 
# Usage: ./ralphy_sprint_runner.sh [--max-tasks N] [--dry-run]
# =============================================================================

set -euo pipefail

# Configuration
SUPABASE_URL="${SUPABASE_URL:-https://mocerqjnksmhcjzxrewo.supabase.co}"
SUPABASE_KEY="${SUPABASE_KEY}"
MAX_TASKS="${MAX_TASKS:-10}"
MAX_ITERATIONS_PER_TASK=50
LOG_DIR="logs/ralphy"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# LOGGING
# =============================================================================
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/sprint_run_$TIMESTAMP.log"

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "${BLUE}$1${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$1${NC}"; }
log_warn() { log "WARN" "${YELLOW}$1${NC}"; }
log_error() { log "ERROR" "${RED}$1${NC}"; }

# =============================================================================
# SUPABASE API FUNCTIONS
# =============================================================================

# Get next pending task from sprint_tasks
get_next_task() {
    local response=$(curl -s -X GET \
        "${SUPABASE_URL}/rest/v1/sprint_tasks?status=eq.pending&order=priority.desc,created_at.asc&limit=1" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json")
    
    echo "$response"
}

# Start a task (update status to in_progress)
start_task() {
    local task_id=$1
    local started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    curl -s -X PATCH \
        "${SUPABASE_URL}/rest/v1/sprint_tasks?id=eq.${task_id}" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{\"status\": \"in_progress\", \"started_at\": \"${started_at}\"}"
    
    log_info "Task $task_id started"
}

# Complete a task
complete_task() {
    local task_id=$1
    local result=$2
    local completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Escape JSON in result
    local escaped_result=$(echo "$result" | jq -Rs .)
    
    curl -s -X PATCH \
        "${SUPABASE_URL}/rest/v1/sprint_tasks?id=eq.${task_id}" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{\"status\": \"completed\", \"completed_at\": \"${completed_at}\", \"result\": ${escaped_result}}"
    
    log_success "Task $task_id completed"
}

# Mark task as failed
fail_task() {
    local task_id=$1
    local error_message=$2
    local failed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    local escaped_error=$(echo "$error_message" | jq -Rs .)
    
    curl -s -X PATCH \
        "${SUPABASE_URL}/rest/v1/sprint_tasks?id=eq.${task_id}" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{\"status\": \"failed\", \"completed_at\": \"${failed_at}\", \"error\": ${escaped_error}}"
    
    log_error "Task $task_id failed: $error_message"
}

# Log task attempt to insights table
log_insight() {
    local task_id=$1
    local insight_type=$2
    local message=$3
    
    curl -s -X POST \
        "${SUPABASE_URL}/rest/v1/insights" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{\"source\": \"ralphy_runner\", \"type\": \"${insight_type}\", \"message\": \"Task ${task_id}: ${message}\", \"metadata\": {\"task_id\": \"${task_id}\"}}"
}

# =============================================================================
# RALPHY EXECUTION
# =============================================================================

# Check if Ralphy/Claude Code is available
check_dependencies() {
    if ! command -v claude &> /dev/null; then
        log_error "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Install with: apt-get install jq"
        exit 1
    fi
    
    log_info "Dependencies verified ✓"
}

# Execute a single task via Claude Code with Ralphy-style loop
execute_task() {
    local task_id=$1
    local task_title=$2
    local task_description=$3
    local task_context=$4
    
    local iteration=0
    local task_completed=false
    local task_output=""
    local task_log="$LOG_DIR/task_${task_id}_$TIMESTAMP.log"
    
    log_info "Starting task: $task_title"
    
    # Build the prompt
    local prompt="# Task: ${task_title}

## Description
${task_description}

## Context
${task_context}

## Instructions
1. Complete this task fully
2. Run tests if applicable
3. Commit changes with descriptive message
4. When COMPLETELY done, include exactly: EXIT_SIGNAL: TASK_COMPLETE
5. If blocked after 3 attempts, include: EXIT_SIGNAL: BLOCKED with explanation

## Current Working Directory
$(pwd)
"
    
    # Ralphy-style execution loop
    while [ $iteration -lt $MAX_ITERATIONS_PER_TASK ] && [ "$task_completed" = false ]; do
        iteration=$((iteration + 1))
        log_info "🔄 Iteration $iteration/$MAX_ITERATIONS_PER_TASK for task $task_id"
        
        # Execute Claude Code
        local response=$(claude --print "$prompt" 2>&1) || true
        
        # Log response
        echo "=== Iteration $iteration ===" >> "$task_log"
        echo "$response" >> "$task_log"
        
        # Check for completion signals
        if echo "$response" | grep -q "EXIT_SIGNAL: TASK_COMPLETE"; then
            task_completed=true
            task_output="Completed in $iteration iterations"
            log_success "✅ Task completed in $iteration iterations"
            break
        fi
        
        if echo "$response" | grep -q "EXIT_SIGNAL: BLOCKED"; then
            local block_reason=$(echo "$response" | grep -A5 "EXIT_SIGNAL: BLOCKED" | tail -n5)
            fail_task "$task_id" "Blocked after $iteration iterations: $block_reason"
            log_insight "$task_id" "blocked" "$block_reason"
            return 1
        fi
        
        # Check for stuck loop (same output 3 times)
        if [ $iteration -ge 3 ]; then
            local last_hash=$(tail -n 100 "$task_log" | md5sum | cut -d' ' -f1)
            # Simple stuck detection - if very short response, likely stuck
            if [ ${#response} -lt 50 ]; then
                log_warn "Possible stuck loop detected at iteration $iteration"
                if [ $iteration -ge 5 ]; then
                    fail_task "$task_id" "Stuck loop detected after $iteration iterations"
                    return 1
                fi
            fi
        fi
        
        # Rate limiting protection
        if [ $iteration -eq 25 ]; then
            log_warn "⚠️ 25 iterations reached - pausing 30s for rate limit protection"
            sleep 30
        fi
        
        # Update prompt with continuation context
        prompt="# Continuing Task: ${task_title}

Previous iteration completed. Continue working on the task.

Remember:
- When COMPLETELY done: EXIT_SIGNAL: TASK_COMPLETE
- If blocked: EXIT_SIGNAL: BLOCKED

What's the next step?"
        
        # Brief pause between iterations
        sleep 2
    done
    
    if [ "$task_completed" = true ]; then
        complete_task "$task_id" "$task_output"
        log_insight "$task_id" "completed" "Finished in $iteration iterations"
        return 0
    else
        fail_task "$task_id" "Max iterations ($MAX_ITERATIONS_PER_TASK) reached without completion"
        return 1
    fi
}

# =============================================================================
# MAIN EXECUTION LOOP
# =============================================================================

main() {
    log_info "=========================================="
    log_info "RALPHY SPRINT RUNNER - Starting"
    log_info "Max tasks: $MAX_TASKS"
    log_info "=========================================="
    
    check_dependencies
    
    local tasks_completed=0
    local tasks_failed=0
    local task_count=0
    
    while [ $task_count -lt $MAX_TASKS ]; do
        # Fetch next task
        local task_json=$(get_next_task)
        
        # Check if we got a task
        if [ "$task_json" = "[]" ] || [ -z "$task_json" ]; then
            log_info "No more pending tasks in queue"
            break
        fi
        
        # Parse task details
        local task_id=$(echo "$task_json" | jq -r '.[0].id')
        local task_title=$(echo "$task_json" | jq -r '.[0].title')
        local task_description=$(echo "$task_json" | jq -r '.[0].description // "No description"')
        local task_context=$(echo "$task_json" | jq -r '.[0].context // "{}"')
        
        if [ "$task_id" = "null" ] || [ -z "$task_id" ]; then
            log_info "No valid task found"
            break
        fi
        
        task_count=$((task_count + 1))
        log_info "=========================================="
        log_info "Processing task $task_count/$MAX_TASKS: $task_title"
        log_info "=========================================="
        
        # Mark task as started
        start_task "$task_id"
        
        # Execute the task
        if execute_task "$task_id" "$task_title" "$task_description" "$task_context"; then
            tasks_completed=$((tasks_completed + 1))
        else
            tasks_failed=$((tasks_failed + 1))
        fi
        
        # Brief pause between tasks
        sleep 5
    done
    
    # Final summary
    log_info "=========================================="
    log_info "SPRINT RUN COMPLETE"
    log_info "Tasks attempted: $task_count"
    log_success "Tasks completed: $tasks_completed"
    if [ $tasks_failed -gt 0 ]; then
        log_error "Tasks failed: $tasks_failed"
    fi
    log_info "Log file: $LOG_FILE"
    log_info "=========================================="
    
    # Return non-zero if any failures
    [ $tasks_failed -eq 0 ]
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-tasks)
            MAX_TASKS="$2"
            shift 2
            ;;
        --dry-run)
            log_info "DRY RUN MODE - No changes will be made"
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main
main
