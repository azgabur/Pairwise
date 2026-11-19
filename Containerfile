FROM quay.io/sclorg/python-312-minimal-c9s:latest

LABEL name="pairwise" \
      summary="Pairwise test configuration generator" \
      org.opencontainers.image.source="https://github.com/azgabur/Pairwise"

RUN pip install --no-cache-dir click

COPY main/ /opt/app-root/src/main/

ENTRYPOINT ["python3", "/opt/app-root/src/main/main.py"]
CMD ["--help"]
