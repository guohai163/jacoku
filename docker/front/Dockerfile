FROM node:lts-bookworm AS base


FROM base AS deps

WORKDIR /opt/front-jacoco

COPY front-jacoco/package.json front-jacoco/yarn.lock* front-jacoco/package-lock.json* front-jacoco/pnpm-lock.yaml* front-jacoco/.npmrc* ./

RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi


FROM base AS builder

WORKDIR /opt/front-jacoco
COPY --from=deps /opt/front-jacoco/node_modules ./node_modules

COPY front-jacoco/ ./

RUN \
  if [ -f yarn.lock ]; then yarn run build; \
  elif [ -f package-lock.json ]; then npm run build; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm run build; \
  else echo "Lockfile not found." && exit 1; \
  fi


FROM base AS runner
WORKDIR /opt/front-jacoco

LABEL org.opencontainers.image.authors="GUOHAI.ORG"
LABEL org.opencontainers.image.source=https://github.com/guohai163/jacoku

ENV NODE_ENV=production
# Uncomment the following line in case you want to disable telemetry during runtime.
# ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /opt/front-jacoco/public ./public

COPY --from=builder --chown=nextjs:nodejs /opt/front-jacoco/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /opt/front-jacoco/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/config/next-config-js/output
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]