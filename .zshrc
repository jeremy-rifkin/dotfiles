fpath=(~/thirdparty/zsh-completions/src $fpath)

ZSH=~/.zsh-aqua/
#DISABLE_CORRECTION="true"
source $ZSH/aqua.zsh
source $ZSH/themes/stingray.zsh

export PATH=$PATH:/snap/bin:~/bin/:~/thirdparty/vcpkg:~/.local/bin

LS_COLORS="$LS_COLORS*.pid=00;90:"

HISTSIZE=50000
SAVEHIST=50000

alias wttr="curl wttr.in/West+Lafayette"

alias serve="python3 -m http.server"
alias servep="python3 -m http.server --bind 0.0.0.0"

alias please=sudo

alias pls=sudo

alias disktop="dstat -D sda,sdb -cdngy"

alias syntax="highlight -O ansi --force"

alias dless="dmesg --color=always | less -R"

function df1() {
        df /scratch/EpsonScannerShare /dev/sd* "$@" | grep -v "^udev"
}

alias ports="pls netstat -tupan"

alias pdsh="noglob pdsh"

alias sshnokey="ssh -o PasswordAuthentication=yes -o PreferredAuthentications=keyboard-interactive,password -o PubkeyAuthentication=no"

export PATH=$PATH:~/projects/ce/infra/bin

function checkout-pr() {
    if [ "$#" -ne 1 ]; then
        echo "Error: Please specify the PR"
        return 1
    fi
    git fetch origin pull/$1/head:$1 && git checkout $1
}

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

function venv() {
    source .venv/bin/activate
}

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

function remote() {
    if [ ! -d .git ]; then
        echo "Error: No .git in current directory, run in project root"
        exit 1
    fi
    rsync -r . --exclude="./build*" --exclude="node_modules" x0:remote/$(basename "$PWD") --checksum
}


# >>> mamba initialize >>>
# !! Contents within this block are managed by 'micromamba shell init' !!
export MAMBA_EXE='/home/rifkin/bin/micromamba';
export MAMBA_ROOT_PREFIX='/home/rifkin/.local/share/mamba';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell zsh --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"  # Fallback on help from micromamba activate
fi
unset __mamba_setup
# <<< mamba initialize <<<
