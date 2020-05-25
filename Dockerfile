FROM python:3

#ENV QT_X11_NO_MITSHM 1
WORKDIR /usr/src/OMRChecker

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./docker_main.py" ]
