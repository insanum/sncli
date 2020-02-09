# docker build . -t sncli
# docker run --rm -it -v /tmp:/tmp -v "$HOME/.sncli/:/root/.sncli/" -v "$HOME/.snclirc:/root/.snclirc" sncli
FROM python:3.8-buster

RUN pip3 install pipenv

COPY . /sncli
WORKDIR /sncli
RUN pipenv install

ENTRYPOINT pipenv run ./sncli

# Install editors and tools of your choice
RUN apt-get update && apt-get install -y neovim && apt-get clean
# ENV EDITOR /usr/bin/nvim
