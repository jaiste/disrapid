FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

# Install mariadb-client
RUN apt-get update && apt-get install -y mariadb-client && rm -rf /var/lib/apt

WORKDIR /app
ADD disrapidBot /app
ADD requirements.txt /app

# Switching to a non-root user
RUN useradd appuser && chown -R appuser /app
USER appuser

# Check if db is empty


# During debugging, this entry point will be overridden.
CMD ["python", "main.py"]
