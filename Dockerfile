FROM python:3.13-slim
WORKDIR /benchmark
COPY src /benchmark/src
COPY scripts /benchmark/scripts
ENV PATH=""
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["/usr/local/bin/python", "/benchmark/scripts/offline_check.py"]
