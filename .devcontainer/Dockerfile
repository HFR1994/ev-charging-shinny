ARG VARIANT=3.14-trixie
FROM mcr.microsoft.com/devcontainers/python:${VARIANT}

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
RUN pip install --upgrade pip wheel && pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

RUN echo 'unset PS1' >> /home/vscode/.zshrc && \
    echo '# Ensure prompt is set by Oh My Zsh, not container default' >> /home/vscode/.zshrc && \
    chown vscode:vscode /home/vscode/.zshrc