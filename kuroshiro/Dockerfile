ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache \
      curl \
      jq \
      postgresql17 \
      postgresql17-client \
      su-exec \
      tzdata

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
