JRENV=$HOME/.jrenv
ZSH=$HOME/.jrenv/ohmyzsh

# ZSH_THEME="agnoster"

plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

fpath+=${ZSH_CUSTOM:-${ZSH:-~/.jrenv/ohmyzsh}/custom}/plugins/zsh-completions/src
autoload -U compinit && compinit

source $ZSH/oh-my-zsh.sh

source $JRENV/zsh/theme.zsh
source $JRENV/zsh/utils.zsh

bindkey '^F' autosuggest-accept # ctrl+f

# Prevents duplicate entries in PATH
typeset -U path PATH
# Prepend to path
path[1,0]=~/micromamba/envs/devtools/bin
path[1,0]=~/micromamba/bin
path[1,0]=~/bin

eval "$(micromamba shell hook --shell zsh)"

alias mm=micromamba

HISTFILE="$HOME/.zsh_history"
HISTSIZE=10000000
SAVEHIST=10000000
setopt BANG_HIST
setopt HIST_VERIFY
setopt EXTENDED_HISTORY
setopt INC_APPEND_HISTORY
setopt SHARE_HISTORY

export PATH=$PATH:~/projects/ce/infra/bin

# fpath=(~/thirdparty/zsh-completions/src $fpath)

# ZSH=~/.zsh-aqua/
# #DISABLE_CORRECTION="true"
# source $ZSH/aqua.zsh
# source $ZSH/themes/stingray.zsh

# export PATH=$PATH:/snap/bin:~/bin/:~/thirdparty/vcpkg:~/.local/bin

# LS_COLORS="$LS_COLORS*.pid=00;90:"

# HISTSIZE=50000
# SAVEHIST=50000

# alias wttr="curl wttr.in/West+Lafayette"

# alias disktop="dstat -D sda,sdb -cdngy"

# alias syntax="highlight -O ansi --force"

# alias dless="dmesg --color=always | less -R"

# function df1() {
#         df /scratch/EpsonScannerShare /dev/sd* "$@" | grep -v "^udev"
# }

# alias ports="pls netstat -tupan"

# alias pdsh="noglob pdsh"

# alias sshnokey="ssh -o PasswordAuthentication=yes -o PreferredAuthentications=keyboard-interactive,password -o PubkeyAuthentication=no"

# export PATH=$PATH:~/projects/ce/infra/bin

# export NVM_DIR="$HOME/.nvm"
# [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
# [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# function remote() {
#     if [ ! -d .git ]; then
#         echo "Error: No .git in current directory, run in project root"
#         exit 1
#     fi
#     rsync -r . --exclude="./build*" --exclude="node_modules" x0:remote/$(basename "$PWD") --checksum
# }
