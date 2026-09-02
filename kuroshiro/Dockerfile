ARG BUILD_FROM
ARG KUROSHIRO_VERSION=0.11.0

# Pinned to amd64 because upstream publishes a single-arch image, and only its
# architecture-independent JS bundles and static assets are taken from it - the
# production dependencies are reinstalled below for the add-on's own architecture.
FROM --platform=linux/amd64 ghcr.io/phyberapex/kuroshiro:${KUROSHIRO_VERSION} AS kuroshiro

FROM ${BUILD_FROM}

ENV NODE_ENV=production \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    KUROSHIRO_PORT=3000 \
    KUROSHIRO_DB_HOST=127.0.0.1 \
    KUROSHIRO_DB_PORT=5432 \
    KUROSHIRO_DB_USER=kuroshiro \
    KUROSHIRO_DB_PASSWORD=kuroshiro \
    KUROSHIRO_DB_DB=kuroshiro \
    PGDATA=/data/postgres \
    PGSOCKET=/data/postgres-run \
    PGLOG=/data/postgres.log

RUN apk add --no-cache \
      chromium \
      curl \
      giflib \
      imagemagick \
      jq \
      libjpeg-turbo \
      libpng \
      postgresql17 \
      postgresql17-client \
      su-exec \
      tiff \
      tini \
      tzdata

WORKDIR /app

COPY --from=kuroshiro /app/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=kuroshiro /app/package.json ./package.json
COPY --from=kuroshiro /app/entrypoint.sh ./entrypoint.sh
COPY --from=kuroshiro /app/dist ./dist
COPY --from=kuroshiro /app/public ./public

RUN corepack enable \
    && pnpm install --prod --ignore-scripts \
    && chmod +x ./entrypoint.sh

COPY run.sh /run.sh
RUN chmod a+x /run.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/run.sh"]
