ARG VARIANT=3.14-trixie
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

RUN echo 'unset PS1' >> /home/vscode/.zshrc && \
    echo '# Ensure prompt is set by Oh My Zsh, not container default' >> /home/vscode/.zshrc && \
    chown vscode:vscode /home/vscode/.zshrc