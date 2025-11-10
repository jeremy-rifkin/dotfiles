function venv() {
    source .venv/bin/activate
}

alias serve="python3 -m http.server"
alias servep="python3 -m http.server --bind 0.0.0.0"

alias disktop="dstat -D sda,sdb -cdngy"

alias syntax="highlight -O ansi --force"

alias ports="pls netstat -tupan"

alias pdsh="noglob pdsh"

alias sshnokey="ssh -o PasswordAuthentication=yes -o PreferredAuthentications=keyboard-interactive,password -o PubkeyAuthentication=no"

function sendit() {
    if [ "$#" -lt 1 ]; then
        echo "Error: Please a commit message"
        return 1
    fi
    url=$(git config --get remote.origin.url)
    if [[ $url = git@github.com:* ]]
    then
        value=${url#*git@github.com:}
    else
        value=${https://github.com/:}
    fi
    github_path=${value%.git}
    m1=""
    m2=""
    if [[ $(git branch --show-current) == main ]]; then
        m2="    https://github.com/$github_path/"
    elif [[ $(git branch --show-current) == master ]]; then
        m2="    https://github.com/$github_path/"
    else
        m1="Open a PR at\n"
        m2="    https://github.com/$github_path/pull/new/$(git branch --show-current)"
    fi
    git commit -m "$@" && git push -u origin "$(git branch --show-current)" &&
    echo &&
    echo -n "$m1" &&
    echo "$m2" &&
    echo
}

function fetch() {
    if [[ $(git branch --show-current) == main ]]; then
        git fetch --tags && git rebase origin/main
    elif [[ $(git branch --show-current) == master ]]; then
        git fetch --tags && git rebase origin/master
    else
        echo "Run on master or main"
    fi
    #git fetch --tags && git rebase $(git branch --show-current)
}

alias lsblk="/bin/lsblk -o NAME,LABEL,FSTYPE,SIZE,TYPE,MOUNTPOINT "

# List top disk usage by item
function lu() {
	local d=.
	if [ $# -ne 0 ]
	then
		d=$1
	fi
	du $d/* -shcx | sort -rh
}

# Create directory and cd into it
function take() {
	if [ $# -eq 0 ]
	then
		echo "must specify name or path"
		return 1
	fi
	mkdir -p $1 && cd $1
}

alias getip="curl \"https://api.ipify.org/?format=text\"; echo"

function checksum() {
	if [ $# -eq 0 ]
	then
		echo "Must specify file."
		return 1
	fi
	if [ ! -f $1 ]
	then
		echo "$fg[red]Error:$reset File doesn't exist."
		return 1
	fi
	echo "md5 $(md5sum $1)\nsha1 $(sha1sum $1)\nsha256 $(sha256sum $1)" | column -t -s" "
}

clone_at_commit() {
    local repo_url=$1
    local commit_hash=$2
    local target_dir=$3

    if [[ -z "$repo_url" || -z "$commit_hash" || -z "$target_dir" ]]; then
        echo "Usage: clone_at_commit <repo_url> <commit_hash> <target_dir>"
        return 1
    fi

    mkdir -p "$target_dir"
    git init "$target_dir"
    git -C "$target_dir" remote add origin "$repo_url"
    git -C "$target_dir" fetch --depth 1 origin "$commit_hash"
    git -C "$target_dir" checkout FETCH_HEAD
}

# Navigation helpers
# up - go up n directories
# back - pushes current dir, pops previous one
# forward - re-enters directory pushed to variable

function up() {
    local count="${1:-1}"

    if ! [[ "$count" =~ '^[0-9]+$' ]]; then
        echo "Usage: up [positive integer]"
        return 1
    fi

    if (( count < 0 )); then
        echo "Nice try."
        return 1
    fi

    # Build path like ../../.. for N levels
    local -a parts
    for ((i = 0; i < count; i++)); do
        parts+=("..")
    done

    local path="${(j:/:)parts}"  # join with slashes

    cd "$path" || return 1
}

setopt auto_pushd

# stack holding directories you’ve “backed” out of
typeset -g -a _forward_stack=()

function back() {
  if (( ${#dirstack[@]} == 0 )); then
    echo "No previous directory to return to." >&2
    return 1
  fi

  _forward_stack+=("$PWD")   # save where we are now
  popd > /dev/null || return 1
}

function forward() {
  if (( ${#_forward_stack[@]} == 0 )); then
    echo "No forward history." >&2
    return 1
  fi

  local idx=$(( ${#_forward_stack[@]} - 1 ))
  local next_dir=${_forward_stack[idx]}
  _forward_stack=("${_forward_stack[@]:0:idx}")   # pop

  pushd "$next_dir" > /dev/null || return 1
}
