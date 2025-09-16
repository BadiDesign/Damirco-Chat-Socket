FROM python:3.10-slim-bookworm


RUN apt-get update && \
    apt-get install -y gettext && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

LABEL maintainer="Ad.BadiDesign@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY ./requirements.txt .
COPY ./captain-entrypoint.sh .
COPY ./core .
RUN chmod +x ./captain-entrypoint.sh

RUN pip config --user set global.index https://mirror-pypi.runflare.com/simple && pip config --user set global.index-url https://mirror-pypi.runflare.com/simple && pip config --user set global.trusted-host mirror-pypi.runflare.com
RUN pip install --upgrade pip && pip install -r requirements.txt


EXPOSE 8080

# execute our entrypoint.sh file
CMD ["sh","./captain-entrypoint.sh"]