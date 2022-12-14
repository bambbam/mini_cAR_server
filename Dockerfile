FROM python:3.9
RUN pip3 install poetry
COPY . /code
WORKDIR /code
RUN mkdir -p /tmp
RUN poetry install --no-root
CMD ["poetry", "run", "server"]