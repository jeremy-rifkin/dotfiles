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
    local_count=$(git rev-list --count main..origin/main 2>/dev/null)
    if (( local_count > 0 )); then
        return 0  # upstream changes exist
    else
        return 1  # no changes
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
else
    echo "jr/dotfiles up to date $dotfile_repo_dir."
fi

