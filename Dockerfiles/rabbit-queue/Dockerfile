FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends rabbitmq-server && \
    rm -rf /var/lib/apt/lists/* && \
    rabbitmq-plugins enable --offline rabbitmq_management

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5672 15672
ENTRYPOINT ["/entrypoint.sh"]
