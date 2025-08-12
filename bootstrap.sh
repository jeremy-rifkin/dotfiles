#!/bin/bash

set -e

echo "Installing environment"
echo "Will install to ~/bin, ~/.jrenv, and various dotfiles"
echo "Dotfile backups will be made to ~/.jrenv/bak"

mkdir -p ~/.jrenv

# Clean up any previous stuff
rm -rf ~/.jrenv/ohmyzsh
rm -rf ~/.jrenv/zsh

backup_dir=~/.jrenv/bak
mkdir -p $backup_dir

mkdir -p ~/bin
mkdir -p ~/micromamba

bak() {
    local source_file="$1"
    if [[ ! -f "$source_file" ]]; then
        echo "Error: Source file '$source_file' does not exist."
        return 1
    fi
    if [[ ! -d "$backup_dir" ]]; then
        echo "Error: Backup directory '$backup_dir' does not exist."
        return 1
    fi
    local filename=$(basename -- "$source_file")
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${backup_dir}/${filename}_${timestamp}"
    cp "$source_file" "$backup_file"
    echo "Backup created at: $backup_file"
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

for f in dots/.*; do
    [[ -e $f ]] || continue
    [[ -d $f ]] && continue
    [[ $f == */. || $f == */.. ]] && continue
    bf=$(basename $f)
    if [[ -f "$HOME/$bf" ]]; then
        bak "$HOME/$bf"
    fi
    cp -v $f ~
done

mkdir -p ~/.config/atuin
cp -v dots/.config/atuin/config.toml ~/.config/atuin/config.toml

cp -rv zsh ~/.jrenv

cp -vp scripts/* ~/bin

echo "Downloading micromamba"

curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C ~ bin/micromamba

~/bin/micromamba -r ~/micromamba create -f mamba/devtools.yml -y

clone_at_commit https://github.com/ohmyzsh/ohmyzsh.git ef96242b9baad6b2211c386cb9af9418ace5d876 ~/.jrenv/ohmyzsh
clone_at_commit https://github.com/zsh-users/zsh-autosuggestions 85919cd1ffa7d2d5412f6d3fe437ebdbeeec4fc5 ~/.jrenv/ohmyzsh/custom/plugins/zsh-autosuggestions
clone_at_commit https://github.com/zsh-users/zsh-syntax-highlighting.git 5eb677bb0fa9a3e60f0eff031dc13926e093df92 ~/.jrenv/ohmyzsh/custom/plugins/zsh-syntax-highlighting
clone_at_commit https://github.com/zsh-users/zsh-completions.git 1488badf72d9214e9e368201758c4eb08af55016 ~/.jrenv/ohmyzsh/custom/plugins/zsh-completions
