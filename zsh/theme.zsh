autoload -Uz vcs_info
zstyle ':vcs_info:*' enable git
zstyle ':vcs_info:git:*' formats ' %F{black}%b%f%k'  # bblack: black text on white background

# Enable prompt substitution
setopt prompt_subst

# Git branch function
function get_git_branch() {
  vcs_info
  echo $vcs_info_msg_0_
}

function get_username() {
  [[ $EUID -eq 0 ]] && echo "%F{red}%B%n%b" || echo "%F{black}%B%n%b"
}

SEPARATOR="›"

# Left prompt: [pwd] [branch] ›
PROMPT='%F{blue}%B%~%b%f$(get_git_branch) %F{green}%(?..%F{red})%B$SEPARATOR%b%f '

# Right prompt: [exit status] [username] [hostname]
RPROMPT='%(?..%K{red}%F{black} %? %f%k)%K{white} $(get_username) %f%k%K{black}%F{white} %m %f%k'

function timetohuman {
    local T=$1
    local D=$((T/60/60/24))
    local H=$((T/60/60%24))
    local M=$((T/60%60))
    local S=$((T%60))

    local RED=$'\e[31m'
    local YELLOW=$'\e[33m'
    local GREEN=$'\e[32m'
    local BLUE=$'\e[34m'
    local RESET=$'\e[0m'

    (( D > 0 )) && printf "${RED}%d ${RESET}day%s " $D $([[ $D -ne 1 ]] && echo s)
    (( H > 0 )) && printf "${YELLOW}%d ${RESET}hour%s " $H $([[ $H -ne 1 ]] && echo s)
    (( M > 0 )) && printf "${GREEN}%d ${RESET}minute%s " $M $([[ $M -ne 1 ]] && echo s)
    (( D > 0 || H > 0 || M > 0 )) && printf "and "
    printf "${BLUE}%d ${RESET}second%s\n" $S $([[ $S -ne 1 ]] && echo s)
}

# Capture the start time of the command
preexec() {
    timer=$EPOCHSECONDS
}

# After command finishes, if time > 5s, show human-readable duration
precmd() {
    local dir_name="${PWD##*/}"
    print -Pn "\e]0;%n@%m: $dir_name\a"

    if [[ -n "$timer" ]]; then
        local elapsed=$(( EPOCHSECONDS - timer ))
        if (( elapsed > 5 )); then
            echo -e "\nCommand took $(timetohuman $elapsed)"
        fi
        unset timer
    fi
}
