FROM postgis/postgis:16-master

USER root

RUN apt-get update && apt-get install -y \
    git build-essential cmake unzip \
    libtool pkg-config curl ca-certificates \
    postgresql-server-dev-16 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L -o h3-pg.zip https://github.com/zachasme/h3-pg/archive/refs/heads/main.zip \
 && unzip h3-pg.zip \
 && cd h3-pg-main \
 && make PG_CONFIG=/usr/bin/pg_config NO_FORMAT=1 \
 && make install

COPY initdb/ /docker-entrypoint-initdb.d/

USER postgres
