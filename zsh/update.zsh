# check for updates

dotfile_repo_dir=$HOME/.jrenv/dotfiles

check_upstream_changes() {
    current_dir="$PWD"
    repo_path="$1"
    cd "$repo_path" || { echo "Invalid path: $repo_path"; return 2; }
    git fetch --quiet
    if ! git show-ref --verify --quiet refs/heads/main; then
        echo "'main' branch does not exist in $repo_path"
        cd "$current_dir"
        return 2
    fi
    count=$(git rev-list --count main..origin/main 2>/dev/null)
    cd "$current_dir"
    if [ "$count" -gt 0 ]; then
        return 0
    else
        return 1
    fi
}

update_env() {
    echo "Updating: Fetching and resetting"
    git -C "$dotfile_repo_dir" fetch --prune
    git -C "$dotfile_repo_dir" reset --hard origin/main
    (cd "$dotfile_repo_dir" && ./bootstrap.sh) || { printf "bootstrap failed\n"; return 1; }
}

# Check upstream asynchronously
# session-scoped flags (unique per shell)
_dotfiles_flag="/tmp/.dotfiles_update_available.$$"
_dotfiles_done="/tmp/.dotfiles_check_done.$$"

# upstream check in background
(
  if check_upstream_changes "$dotfile_repo_dir"; then
      : >"$_dotfiles_flag"
  fi
  : >"$_dotfiles_done"
) >/dev/null 2>&1 &!

autoload -Uz add-zsh-hook
_dotfiles_notify() {
  # if upstream check check hasn't finished yet, keep the hook for the next prompt
  [ -f "$_dotfiles_done" ] || return

  if [ -f "$_dotfiles_flag" ]; then
    message="Upstream changes detected for $dotfile_repo_dir
Run update_env to update!"
    $HOME/.jrenv/dotfiles/utils/stegosaurus.py "$message" || echo "=================================================\n$message\n================================================="
    rm -f -- "$_dotfiles_flag"
  fi

  rm -f -- "$_dotfiles_done"
  add-zsh-hook -d precmd _dotfiles_notify
}
add-zsh-hook precmd _dotfiles_notify
