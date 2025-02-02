FROM node as build

WORKDIR /opt/front-jacoco/
COPY front-jacoco/ ./

RUN pnpm build


FROM nginx

LABEL org.opencontainers.image.authors="GUOHAI.ORG"
LABEL org.opencontainers.image.source=https://github.com/guohai163/jacoco-report