FROM ocrd/all:maximum

# creates /models/calamari_models-1.0
RUN mkdir /models &&\
    curl -L https://github.com/Calamari-OCR/calamari_models/archive/1.0.tar.gz | \
      tar zxvf /dev/stdin -C /models

COPY run.sh /run.sh
CMD /run.sh
