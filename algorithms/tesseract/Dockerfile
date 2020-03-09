FROM ubuntu:bionic

RUN apt-get update && \
    apt-get install -y python3 python3-pip tesseract-ocr tesseract-ocr-nld libtesseract4 libtesseract-dev libleptonica-dev pkg-config git && \
    pip3 install git+https://github.com/eyra-benchmark/page_xml_gen &&\
    pip3 install tesserocr pyocr

