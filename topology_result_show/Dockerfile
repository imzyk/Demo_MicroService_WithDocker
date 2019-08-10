FROM ubuntu:16.04
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y -q python-all python-pip 
ADD ./app/requirements.txt /tmp/requirements.txt
RUN pip install -qr /tmp/requirements.txt
ADD ./app /opt/app/
WORKDIR /opt/app
EXPOSE 5000
CMD ["python", "app_show.py"]
