FROM gcc:12

RUN useradd -m sandbox
WORKDIR /sandbox
USER sandbox