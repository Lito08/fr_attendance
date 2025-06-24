FROM python:3.11-slim

# install system‐deps needed to compile dlib and OpenCV‐headless
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      cmake \
      pkg-config \
      libboost-python-dev \
      libboost-system-dev \
      libjpeg-dev \
      libpng-dev \
      libopenblas-dev \
      liblapack-dev \
 && rm -rf /var/lib/apt/lists/*

# set a working directory
WORKDIR /code

# copy your requirements.txt (with numpy<2 pinned!) and install
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# copy the rest of your code
COPY . .

# collect static, migrate, etc., if you like
# RUN python manage.py collectstatic --no-input
# RUN python manage.py migrate

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
