# docker build . [--build-arg editor_packages=neovim] -t sncli
# docker run --rm -it -v /tmp:/tmp -v "$HOME/.sncli/:/root/.sncli/" -v "$HOME/.snclirc:/root/.snclirc" sncli
FROM python:3.9-bullseye

ARG editor_packages="vim"

# Install editors and tools of your choice
ARG DEBIAN_FRONTEND=noninteractive
RUN \
    apt-get update && \
    apt-get install -y \
      ${editor_packages} \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/

RUN pip3 install --no-cache pipenv

COPY ./Pipfile /sncli/
COPY ./Pipfile.lock /sncli/
WORKDIR /sncli/
RUN \
    pipenv install && \
    pipenv --clear

COPY . /sncli/

ENTRYPOINT [ "pipenv", "run", "./sncli" ]
