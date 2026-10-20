# Report image: builds the results explorer and the chart PNG. matplotlib is pinned; network only needed at build time.
FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 MPLCONFIGDIR=/tmp/mpl
RUN useradd --create-home --uid 10001 report
RUN pip install --no-cache-dir matplotlib==3.11.2 \
 && pip freeze > /opt/resolved-versions.txt
USER 10001
WORKDIR /work
ENTRYPOINT ["python"]
