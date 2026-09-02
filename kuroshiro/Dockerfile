ARG BUILD_FROM
ARG KUROSHIRO_VERSION=0.11.0

# Pinned to amd64 because upstream publishes a single-arch image. Everything taken
# from it is architecture-independent - the JS bundles, the static assets, and
# node_modules, whose production dependencies are all pure JS. Everything
# architecture-specific comes from apk below. Reinstalling the dependencies for the
# target architecture instead is not an option: that runs node under aarch64
# emulation, where V8 dies with SIGILL.
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

COPY --from=kuroshiro /app/package.json ./package.json
COPY --from=kuroshiro /app/entrypoint.sh ./entrypoint.sh
COPY --from=kuroshiro /app/node_modules ./node_modules
COPY --from=kuroshiro /app/dist ./dist
COPY --from=kuroshiro /app/public ./public

COPY run.sh /run.sh
RUN chmod +x /run.sh /app/entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/run.sh"]
