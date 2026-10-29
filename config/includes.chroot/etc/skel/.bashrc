if [ -r /etc/bash.bashrc ]; then
    . /etc/bash.bashrc
fi

case "$-" in
    *i*) ;;
    *) return ;;
esac

export EDITOR=nano
export PAGER=less
alias ll='ls -lah --color=auto'
alias la='ls -A --color=auto'
alias ..='cd ..'
alias ...='cd ../..'
alias py='python3'
alias gs='git status'

if [ -t 1 ]; then
    PS1='\[\e[1;36m\]nyrox\[\e[0m\] \[\e[1;32m\]\w\[\e[0m\] \$ '
fi

echo "Nyrox Terminal | type 'nyrox help' to get started."
