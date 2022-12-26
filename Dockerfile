FROM python

COPY . /home
WORKDIR /home/AdminBot

RUN apt-get update && \
        apt-get upgrade --assume-yes && \
        apt-get install --assume-yes screen && \
        apt-get install nano && \
        pip install --upgrade pip && \
        pip install -r ../requirements.txt

CMD ["python", "admin_bot.py"]