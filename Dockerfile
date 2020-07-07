FROM python:3

#ENV QT_X11_NO_MITSHM 1
WORKDIR /usr/src/OMRChecker

RUN apt-get update; apt-get install poppler-utils -y

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-u", "./docker_main.py" ]
