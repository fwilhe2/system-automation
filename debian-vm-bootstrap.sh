#!/bin/bash

# Quick and dirty script to make debian vms more usable

# Add the repositories to sources.list if they don't already exist
if ! grep -q "deb http://deb.debian.org/debian/ testing" /etc/apt/sources.list; then
    echo "
#------------------------------------------------------------------------------#
#                   OFFICIAL DEBIAN REPOS                    
#------------------------------------------------------------------------------#

###### Debian Main Repos
deb http://deb.debian.org/debian/ testing main contrib non-free
deb-src http://deb.debian.org/debian/ testing main contrib non-free

deb http://deb.debian.org/debian/ testing-updates main contrib non-free
deb-src http://deb.debian.org/debian/ testing-updates main contrib non-free

deb http://deb.debian.org/debian-security testing-security main
deb-src http://deb.debian.org/debian-security testing-security main" | sudo tee /etc/apt/sources.list

    # Update package repositories
    sudo apt update
fi

sudo apt install -y git vim

sudo apt-get -y dist-upgrade

sudo apt-get clean

# Set Vim as the default editor if not already set
if [ -z "$(update-alternatives --query editor | grep '/usr/bin/vim.basic')" ]; then
    sudo update-alternatives --set editor /usr/bin/vim.basic
fi

# Enable passwordless sudo if not already enabled
if ! sudo grep -q '%sudo ALL=(ALL) NOPASSWD:ALL' /etc/sudoers.d/nopasswd; then
    echo "%sudo ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/nopasswd
fi

# Add the current user to the sudo group if not already added
if ! groups "$(whoami)" | grep -q '\bsudo\b'; then
    sudo usermod -aG sudo "$(whoami)"
fi

# Add bash aliases if they don't already exist in the .bashrc file
if ! grep -Fxq "alias ls='ls --group-directories-first --time-style=+\"%Y-%m-%d %H:%M\" --color=auto --classify'" ~/.bashrc; then
    echo "
alias ls='ls --group-directories-first --time-style=+\"%Y-%m-%d %H:%M\" --color=auto --classify'
alias ll='ls -lh'
alias la='ls -lah'
alias lh=la

# Git aliases - based on http://www.catonmat.net/blog/git-aliases/
alias g=git
alias ga='git add'
alias gp='git push'
alias gl='git log'
alias gfu='git fetch upstream; git checkout -B master origin/master'
alias gs='git status'
alias gd='git diff'
alias gra='git remote add'
alias gdc='git diff --cached'
alias gm='git commit'
alias gb='git branch'
alias gc='git checkout'
alias gra='git remote add'
alias grr='git remote rm'
alias gci='git commit'
alias gcl='git clone'" >> ~/.bashrc

    # Source the .bashrc file to make the aliases available in the current session
    source ~/.bashrc
fi

git config --global alias.st status 
git config --global alias.co checkout 
git config --global alias.rb rebase 
git config --global alias.ci commit 
git config --global alias.br branch 
git config --global alias.cp cherry-pick
git config --global alias.fa 'fetch --all'
git config --global alias.lg 'log --graph --decorate --pretty=oneline --abbrev-commit' 
git config --global alias.ls 'log --decorate --pretty=oneline --abbrev-commit' 

# Display completion message
echo "System setup complete."
