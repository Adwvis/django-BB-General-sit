FROM docker.arvancloud.ir/python:3.12-slim
ENV PYTHONDONTWRITEBYECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirments.txt .

# RUN pip install --no-cache-dir -r requirments.txt -i https://mirror-pypi.runflare.com/simple

RUN pip install -r requirments.txt

# COPY ./core /app
COPY . /app

# CMD ["python3","manage.py","runserver","0.0.0.0:8000"]


