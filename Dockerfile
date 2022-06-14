# syntax=docker/dockerfile:1

FROM nvcr.io/nvidia/l4t-base:r34.1.1

WORKDIR /EFIP

RUN apt-get install python3-pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["/bin/bash"]