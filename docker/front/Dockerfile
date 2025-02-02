FROM node:lts-bookworm AS build

WORKDIR /opt/front-jacoco/
COPY front-jacoco/ ./

RUN pnpm build


FROM nginx:1.26-bookworm AS run

LABEL org.opencontainers.image.authors="GUOHAI.ORG"
LABEL org.opencontainers.image.source=https://github.com/guohai163/jacoco-report

COPY --from=build /opt/front-jacoco /opt/front-jacoco