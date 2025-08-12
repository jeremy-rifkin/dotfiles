# check for updates

dotfile_repo_dir=$HOME/.jrenv/dotfiles

check_upstream_changes() {
    repo_path="$1"
    cd "$repo_path" || { echo "Invalid path: $repo_path"; return 2; }
    git fetch --quiet
    if ! git show-ref --verify --quiet refs/heads/main; then
        echo "'main' branch does not exist in $repo_path"
        return 2
    fi
    count=$(git rev-list --count main..origin/main 2>/dev/null)
    if [ "$count" -gt 0 ]; then
        return 0
    else
        return 1
    fi
}

update_env() {
    cd $dotfile_repo_dir
    git fetch
    git rebase origin/main
    ./bootstreap.sh
}

if check_upstream_changes "$dotfile_repo_dir"; then
    message=$'Upstream changes detected for $dotfile_repo_dir\nRun update_env to update!'
    cowpy -c stegosaurus "$message" || echo "=================================================\n$message\n================================================="
fi
