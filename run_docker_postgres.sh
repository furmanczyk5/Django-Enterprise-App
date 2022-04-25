#!/usr/bin/env bash


docker run --name apa-postgres -e POSTGRES_USER=planning -e POSTGRES_DB=apa -e POSTGRES_PASSWORD=planning -p 5432:5432 postgres:9.6

# docker run --name apa-postgres -v "${PWD}/dbdump":/data -e POSTGRES_USER=planning -e POSTGRES_DB=apa -e POSTGRES_PASSWORD=planning -p 5432:5432 postgres:9.6
