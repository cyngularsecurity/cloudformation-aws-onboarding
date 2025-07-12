#!/bin/bash

# Git Workflow Automation for Cyngular Client Onboarding
# Workflow: dev -> main -> release/3.8

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository!"
        exit 1
    fi
}

# Function to check if branch exists
branch_exists() {
    git show-ref --verify --quiet refs/heads/$1
}

# Function to check if remote branch exists
remote_branch_exists() {
    git show-ref --verify --quiet refs/remotes/origin/$1
}

# Function to check GitLab CLI authentication
check_glab_auth() {
    if ! command -v glab >/dev/null 2>&1; then
        print_warning "GitLab CLI (glab) not found. Install with: brew install glab"
        return 1
    fi
    
    if ! glab auth status >/dev/null 2>&1; then
        print_error "GitLab CLI not authenticated. Please run:"
        echo "  glab auth login"
        echo "  Or visit: https://gitlab.com/-/user_settings/personal_access_tokens"
        return 1
    fi
    
    return 0
}

# Function to create merge request
create_mr() {
    local source_branch=$1
    local target_branch=$2
    local title=$3
    
    print_status "Creating merge request from $source_branch to $target_branch..."
    
    if check_glab_auth; then
        if glab mr create \
            --source-branch "$source_branch" \
            --target-branch "$target_branch" \
            --title "$title" \
            --description "Automated merge request from $source_branch to $target_branch" \
            --remove-source-branch 2>/dev/null; then
            print_success "Merge request created successfully!"
        else
            print_warning "Failed to create MR automatically. Create manually at:"
            echo "  https://gitlab.com/$(git config --get remote.origin.url | sed 's/.*:\(.*\)\.git/\1/')/-/merge_requests/new?merge_request%5Bsource_branch%5D=$source_branch&merge_request%5Btarget_branch%5D=$target_branch"
        fi
    else
        print_warning "Please create merge request manually:"
        echo "  Source: $source_branch"
        echo "  Target: $target_branch"
        echo "  Title: $title"
        echo "  URL: https://gitlab.com/$(git config --get remote.origin.url | sed 's/.*:\(.*\)\.git/\1/')/-/merge_requests/new?merge_request%5Bsource_branch%5D=$source_branch"
    fi
}

# Function to push changes and create MR to main
push_to_main() {
    print_status "Starting workflow: dev -> main"
    
    # Ensure we're on dev branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "dev" ]; then
        print_error "Please switch to dev branch first (current: $current_branch)"
        exit 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_error "You have uncommitted changes. Please commit or stash them first."
        exit 1
    fi
    
    # Pull latest changes from dev
    print_status "Pulling latest changes from origin/dev..."
    git pull origin dev
    
    # Push dev branch to remote
    print_status "Pushing dev branch to remote..."
    git push origin dev
    
    # Create MR from dev to main
    create_mr "dev" "main" "Merge dev to main - $(date '+%Y-%m-%d %H:%M')"
}

# Function to merge main to release/3.8
push_to_release() {
    print_status "Starting workflow: main -> release/3.8"
    
    # Switch to main branch
    print_status "Switching to main branch..."
    git checkout main
    
    # Pull latest changes from main
    print_status "Pulling latest changes from origin/main..."
    git pull origin main
    
    # Check if release/3.8 branch exists locally
    if ! branch_exists "release/3.8"; then
        if remote_branch_exists "release/3.8"; then
            print_status "Creating local release/3.8 branch from remote..."
            git checkout -b release/3.8 origin/release/3.8
        else
            print_error "release/3.8 branch doesn't exist locally or remotely!"
            exit 1
        fi
    else
        print_status "Switching to release/3.8 branch..."
        git checkout release/3.8
        print_status "Pulling latest changes from origin/release/3.8..."
        git pull origin release/3.8
    fi
    
    # Create MR from main to release/3.8
    create_mr "main" "release/3.8" "Release merge: main to release/3.8 - $(date '+%Y-%m-%d %H:%M')"
}

# Function to show current status
show_status() {
    print_status "Current Git Status:"
    echo "  Current branch: $(git branch --show-current)"
    echo "  Repository: $(git config --get remote.origin.url)"
    echo ""
    
    print_status "Available commands:"
    echo "  ./git-workflow.sh dev-to-main    - Push dev and create MR to main"
    echo "  ./git-workflow.sh main-to-release - Create MR from main to release/3.8"
    echo "  ./git-workflow.sh full-workflow   - Run complete workflow (dev->main->release)"
    echo "  ./git-workflow.sh status         - Show this status"
}

# Main script logic
main() {
    check_git_repo
    
    case "${1:-status}" in
        "dev-to-main")
            push_to_main
            ;;
        "main-to-release")
            push_to_release
            ;;
        "full-workflow")
            push_to_main
            print_success "Step 1 complete. After the MR to main is merged, run:"
            print_status "./git-workflow.sh main-to-release"
            ;;
        "status")
            show_status
            ;;
        *)
            print_error "Unknown command: $1"
            show_status
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"