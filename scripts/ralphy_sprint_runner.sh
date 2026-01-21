#!/bin/bash
# =============================================================================
# RALPHY SPRINT RUNNER V2 - PR Mode for Greptile Review
# =============================================================================
# Autonomous task execution loop that:
# 1. Fetches next task from Supabase sprint_tasks
# 2. Creates a feature branch
# 3. Executes via Claude Code loop
# 4. Creates PR for Greptile review
# 5. Marks task complete
# =============================================================================

set -euo pipefail

# Configuration
SUPABASE_URL="${SUPABASE_URL:-https://mocerqjnksmhcjzxrewo.supabase.co}"
SUPABASE_KEY="${SUPABASE_KEY}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
MAX_TASKS="${MAX_TASKS:-10}"
MAX_ITERATIONS_PER_TASK=50
LOG_DIR="logs/ralphy"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPO_NAME="${GITHUB_REPOSITORY:-$(basename $(git rev-parse --show-toplevel))}"

# PR Mode (for Greptile review)
CREATE_PRS="${CREATE_PRS:-true}"
AUTO_MERGE="${AUTO_MERGE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
# GIT & PR FUNCTIONS
# =============================================================================

# Create a feature branch for the task
create_feature_branch() {
    local task_id=$1
    local task_title=$2
    
    # Sanitize title for branch name
    local branch_name="ralphy/task-${task_id:0:8}-$(echo "$task_title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | cut -c1-30)"
    
    # Ensure we're on main and up to date
    git checkout main 2>/dev/null || git checkout master 2>/dev/null
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    
    # Create and checkout feature branch
    git checkout -b "$branch_name"
    
    echo "$branch_name"
}

# Commit changes to the feature branch
commit_changes() {
    local task_title=$1
    local iteration=$2
    
    git add -A
    if ! git diff --staged --quiet; then
        git commit -m "🤖 Ralphy: $task_title (iteration $iteration)"
        return 0
    fi
    return 1
}

# Create a Pull Request via GitHub API
create_pull_request() {
    local branch_name=$1
    local task_title=$2
    local task_description=$3
    local task_id=$4
    
    # Get default branch
    local default_branch=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')
    default_branch="${default_branch:-main}"
    
    # Push the branch
    git push -u origin "$branch_name"
    
    # Create PR body
    local pr_body="## 🤖 Automated PR by Ralphy Sprint Runner

### Task
**Title:** $task_title
**ID:** $task_id

### Description
$task_description

### Review Instructions
This PR was created autonomously by Claude Code via Ralphy.
Please review carefully - the code was written without human oversight.

---
*Awaiting Greptile AI review before merge.*"

    # Create PR via GitHub API
    local pr_response=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/${GITHUB_REPOSITORY}/pulls" \
        -d "{
            \"title\": \"🤖 $task_title\",
            \"head\": \"$branch_name\",
            \"base\": \"$default_branch\",
            \"body\": $(echo "$pr_body" | jq -Rs .)
        }")
    
    local pr_number=$(echo "$pr_response" | jq -r '.number // empty')
    local pr_url=$(echo "$pr_response" | jq -r '.html_url // empty')
    
    if [ -n "$pr_number" ] && [ "$pr_number" != "null" ]; then
        log_success "PR #$pr_number created: $pr_url"
        
        # Add labels
        curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${pr_number}/labels" \
            -d '{"labels":["ralphy","ai-generated","needs-review"]}'
        
        echo "$pr_url"
    else
        log_error "Failed to create PR: $(echo "$pr_response" | jq -r '.message // "Unknown error"')"
        echo ""
    fi
}

# =============================================================================
# SUPABASE API FUNCTIONS
# =============================================================================

get_next_task() {
    local response=$(curl -s -X GET \
        "${SUPABASE_URL}/rest/v1/sprint_tasks?status=eq.pending&order=priority.desc,created_at.asc&limit=1" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json")
    
    echo "$response"
}

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

complete_task() {
    local task_id=$1
    local result=$2
    local pr_url=$3
    local completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    local escaped_result=$(echo "$result" | jq -Rs .)
    
    local metadata="{\"pr_url\": \"$pr_url\"}"
    
    curl -s -X PATCH \
        "${SUPABASE_URL}/rest/v1/sprint_tasks?id=eq.${task_id}" \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{\"status\": \"completed\", \"completed_at\": \"${completed_at}\", \"result\": ${escaped_result}, \"source_ref\": \"$pr_url\"}"
    
    log_success "Task $task_id completed - PR: $pr_url"
}

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
# TASK EXECUTION
# =============================================================================

check_dependencies() {
    if ! command -v claude &> /dev/null; then
        log_error "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Install with: apt-get install jq"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "git not found"
        exit 1
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        log_error "GITHUB_TOKEN not set - required for PR creation"
        exit 1
    fi
    
    log_info "Dependencies verified ✓"
}

execute_task() {
    local task_id=$1
    local task_title=$2
    local task_description=$3
    local task_context=$4
    
    local iteration=0
    local task_completed=false
    local task_output=""
    local task_log="$LOG_DIR/task_${task_id}_$TIMESTAMP.log"
    local pr_url=""
    
    log_info "Starting task: $task_title"
    
    # Create feature branch
    local branch_name=$(create_feature_branch "$task_id" "$task_title")
    log_info "Created branch: $branch_name"
    
    # Build the prompt
    local prompt="# Task: ${task_title}

## Description
${task_description}

## Context
${task_context}

## Instructions
1. Complete this task fully
2. Write clean, well-documented code
3. Run tests if applicable
4. When COMPLETELY done, include exactly: EXIT_SIGNAL: TASK_COMPLETE
5. If blocked after 3 attempts, include: EXIT_SIGNAL: BLOCKED with explanation

## Important
- This code will be reviewed by Greptile AI before merge
- Follow project coding standards
- Add comments explaining complex logic

## Current Working Directory
$(pwd)
"
    
    # Execution loop
    while [ $iteration -lt $MAX_ITERATIONS_PER_TASK ] && [ "$task_completed" = false ]; do
        iteration=$((iteration + 1))
        log_info "🔄 Iteration $iteration/$MAX_ITERATIONS_PER_TASK for task $task_id"
        
        # Execute Claude Code
        local response=$(claude --print "$prompt" 2>&1) || true
        
        # Log response
        echo "=== Iteration $iteration ===" >> "$task_log"
        echo "$response" >> "$task_log"
        
        # Commit any changes
        if commit_changes "$task_title" "$iteration"; then
            log_info "Changes committed"
        fi
        
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
            git checkout main 2>/dev/null || git checkout master 2>/dev/null
            return 1
        fi
        
        # Rate limiting protection
        if [ $iteration -eq 25 ]; then
            log_warn "⚠️ 25 iterations reached - pausing 30s"
            sleep 30
        fi
        
        # Update prompt for continuation
        prompt="# Continuing Task: ${task_title}

Previous iteration completed. Continue working on the task.

Remember:
- When COMPLETELY done: EXIT_SIGNAL: TASK_COMPLETE
- If blocked: EXIT_SIGNAL: BLOCKED

What's the next step?"
        
        sleep 2
    done
    
    if [ "$task_completed" = true ]; then
        # Create PR for Greptile review
        if [ "$CREATE_PRS" = "true" ]; then
            pr_url=$(create_pull_request "$branch_name" "$task_title" "$task_description" "$task_id")
            if [ -n "$pr_url" ]; then
                complete_task "$task_id" "$task_output" "$pr_url"
                log_insight "$task_id" "pr_created" "PR ready for Greptile review: $pr_url"
            else
                # Fallback: push directly if PR creation fails
                log_warn "PR creation failed, pushing to branch directly"
                git push origin "$branch_name"
                complete_task "$task_id" "$task_output" "branch:$branch_name"
            fi
        else
            # Direct merge mode (not recommended)
            git checkout main 2>/dev/null || git checkout master 2>/dev/null
            git merge "$branch_name" -m "🤖 Merge: $task_title"
            git push origin main 2>/dev/null || git push origin master 2>/dev/null
            complete_task "$task_id" "$task_output" "direct-merge"
        fi
        
        # Return to main branch
        git checkout main 2>/dev/null || git checkout master 2>/dev/null
        return 0
    else
        fail_task "$task_id" "Max iterations ($MAX_ITERATIONS_PER_TASK) reached"
        git checkout main 2>/dev/null || git checkout master 2>/dev/null
        return 1
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    log_info "=========================================="
    log_info "RALPHY SPRINT RUNNER V2 - PR Mode"
    log_info "Max tasks: $MAX_TASKS"
    log_info "Create PRs: $CREATE_PRS"
    log_info "=========================================="
    
    check_dependencies
    
    local tasks_completed=0
    local tasks_failed=0
    local task_count=0
    
    while [ $task_count -lt $MAX_TASKS ]; do
        local task_json=$(get_next_task)
        
        if [ "$task_json" = "[]" ] || [ -z "$task_json" ]; then
            log_info "No more pending tasks in queue"
            break
        fi
        
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
        
        start_task "$task_id"
        
        if execute_task "$task_id" "$task_title" "$task_description" "$task_context"; then
            tasks_completed=$((tasks_completed + 1))
        else
            tasks_failed=$((tasks_failed + 1))
        fi
        
        sleep 5
    done
    
    # Summary
    log_info "=========================================="
    log_info "SPRINT RUN COMPLETE"
    log_info "Tasks attempted: $task_count"
    log_success "Tasks completed: $tasks_completed"
    if [ $tasks_failed -gt 0 ]; then
        log_error "Tasks failed: $tasks_failed"
    fi
    log_info "PRs created for Greptile review"
    log_info "Log file: $LOG_FILE"
    log_info "=========================================="
    
    [ $tasks_failed -eq 0 ]
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-tasks)
            MAX_TASKS="$2"
            shift 2
            ;;
        --no-pr)
            CREATE_PRS="false"
            shift
            ;;
        --auto-merge)
            AUTO_MERGE="true"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

main
