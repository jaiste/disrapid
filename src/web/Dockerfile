FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
ADD disrapidAdmin /app
ADD requirements.txt /app

# Switching to a non-root user
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]