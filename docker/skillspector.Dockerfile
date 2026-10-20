# NVIDIA SkillSpector, pinned to the v2.13.0 commit. Network is only needed while building this image.
FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN useradd --create-home --uid 10001 scan
RUN pip install --no-cache-dir \
    "https://github.com/NVIDIA/skillspector/archive/091a509b3d6ba8ff5be528966e1f43c2e68cf214.tar.gz" \
 && pip freeze > /opt/resolved-versions.txt
USER 10001
ENTRYPOINT ["skillspector"]
