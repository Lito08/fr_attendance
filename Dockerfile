# ────────────────────────────────────────────────────
# Dockerfile  –  Face-Rec Attendance (no Poetry)
# ────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Basic OS packages you need for dlib / OpenCV builds
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        build-essential libgl1 libglib2.0-0 git \
        cmake \
        libgl1 \
        git \
        nodejs \
        npm \
        libboost-python-dev \
        libboost-system-dev \
 && rm -rf /var/lib/apt/lists/*               # keep the image small

# ── Work directory inside the image
WORKDIR /code

# ── Python dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Copy the rest of your project
COPY . /code

# ── Gunicorn entry-point (you can switch to Django’s runserver in dev)
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000"]
