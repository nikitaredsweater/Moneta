FROM python:3.11-slim

WORKDIR /srv/scheduler

# files are at scheduler_service/requirements.txt (context root), so just:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# src is at scheduler_service/src
COPY src ./src

ENV PYTHONPATH=/srv/scheduler/src

# either of these is fine:
# CMD ["python", "src/scheduler/main.py"]
CMD ["python", "-m", "scheduler.main"]
