FROM python:3.9
RUN pip3 install poetry
RUN apt update
RUN apt-get -y install libgl1-mesa-glx
COPY . /code
WORKDIR /code
RUN mkdir -p /tmp
RUN poetry install --no-root
CMD ["poetry", "run", "server"]