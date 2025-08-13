#!/bin/bash

# Git Workflow Automation
# Workflow: dev -> main -> release/x.x

set -e

### Sync
VERSION="3.8"
COMMIT_MESSAGE="DEVOPS-885 - latest"

ga . && gc -m "${COMMIT_MESSAGE}" && gp
git switch main
git pull --rebase
git merge dev --ff-only -m "${COMMIT_MESSAGE}"
git push
git fetch -a

git switch release/v${VERSION}
git pull --rebase
git merge main --ff-only -m "${COMMIT_MESSAGE}"
git push

exit 0

check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "Not in a git repository!"
        exit 1
    fi
}

branch_exists() {
    git show-ref --verify --quiet refs/heads/$1
}

remote_branch_exists() {
    git show-ref --verify --quiet refs/remotes/origin/$1
}

get_gitlab_project_path() {
    local remote_url=$(git config --get remote.origin.url)
    # Handle both SSH and HTTPS URLs
    if [[ $remote_url == git@* ]]; then
        # SSH format: git@gitlab.com:group/project.git
        echo "$remote_url" | sed 's/git@gitlab\.com://' | sed 's/\.git$//'
    else
        # HTTPS format: https://gitlab.com/group/project.git
        echo "$remote_url" | sed 's|https://gitlab\.com/||' | sed 's/\.git$//'
    fi
}

# Function to push branch and show MR link
create_mr() {
    local source_branch=$1
    local target_branch=$2
    local title=$3
    
    echo "Pushing $source_branch branch to remote..."
    
    # Push the branch to remote
    if git push origin "$source_branch"; then
        echo "Branch $source_branch pushed successfully!"
        
        # Get project path for GitLab URL
        local project_path=$(get_gitlab_project_path)
        local mr_url="https://gitlab.com/$project_path/-/merge_requests/new"
        mr_url="${mr_url}?merge_request%5Bsource_branch%5D=${source_branch}"
        mr_url="${mr_url}&merge_request%5Btarget_branch%5D=${target_branch}"
        mr_url="${mr_url}&merge_request%5Btitle%5D=$(echo "$title" | sed 's/ /%20/g')"
        
        echo "Create merge request at:"
        echo "  🔗 $mr_url"
        echo ""
        echo "Merge Request Details:"
        echo "  📤 Source: $source_branch"
        echo "  📥 Target: $target_branch"
        echo "  📝 Title: $title"
    else
        echo "Failed to push $source_branch branch to remote"
        return 1
    fi
}

# Function to push changes and create MR to main
push_to_main() {
    echo "Starting workflow: dev -> main"
    
    # Ensure we're on dev branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "dev" ]; then
        echo "Please switch to dev branch first (current: $current_branch)"
        exit 1
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo "You have uncommitted changes. Please commit or stash them first."
        exit 1
    fi
    
    # Pull latest changes from dev
    echo "Pulling latest changes from origin/dev..."
    git pull origin dev
    
    # Push and create MR from dev to main
    create_mr "dev" "main" "Merge dev to main - $(date '+%Y-%m-%d %H:%M')"
}

# Function to merge main to release/3.8
push_to_release() {
    echo "Starting workflow: main -> release/3.8"
    
    # Switch to main branch
    echo "Switching to main branch..."
    git checkout main
    
    # Pull latest changes from main
    echo "Pulling latest changes from origin/main..."
    git pull origin main
    
    # Ensure main is pushed (in case of local commits)
    echo "Ensuring main branch is up to date on remote..."
    git push origin main
    
    # Check if release/3.8 branch exists remotely
    if ! remote_branch_exists "release/3.8"; then
        echo "release/3.8 branch doesn't exist on remote!"
        echo "Available release branches:"
        git branch -r | grep "origin/release/" || echo "  No release branches found"
        exit 1
    fi
    
    # Create MR from main to release/3.8 (no need to switch branches)
    create_mr "main" "release/3.8" "Release merge: main to release/3.8 - $(date '+%Y-%m-%d %H:%M')"
}

# Function to show current status
show_status() {
    echo "Current Git Status:"
    echo "  Current branch: $(git branch --show-current)"
    echo "  Repository: $(git config --get remote.origin.url)"
    echo ""
    
    echo "Available commands:"
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
            echo "Step 1 complete. After the MR to main is merged, run:"
            echo "./git-workflow.sh main-to-release"
            ;;
        "status")
            show_status
            ;;
        *)
            echo "Unknown command: $1"
            show_status
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"