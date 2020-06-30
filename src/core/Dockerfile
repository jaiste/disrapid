FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install mariadb-client
RUN apt-get update && apt-get install -y mariadb-client && rm -rf /var/lib/apt

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
ADD disrapidBot /app
ADD requirements.txt /app

# Switching to a non-root user
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden.
CMD ["python", "main.py"]
