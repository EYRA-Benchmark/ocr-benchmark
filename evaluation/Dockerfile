FROM ubuntu:18.04

LABEL maintainer "b.weel@esciencecenter.nl"

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
    build-essential \
    git \
    default-jre \
    default-jdk \
    maven \
    python3-dev \
    python3-pip \
    locales \
    && apt-get autoremove \
		&& apt-get clean
WORKDIR /

RUN ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip

#  Set the proper  locale
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN git clone https://github.com/impactcentre/ocrevalUAtion.git && cd ocrevalUAtion
ADD ocrbenchmark/evaluation/ocrevaluation/userProperties.xml /ocrevalUAtion/userProperties.xml
WORKDIR /ocrevalUAtion
RUN mvn package
RUN chmod 644 /ocrevalUAtion/target/ocrevaluation.jar

COPY . /ocrbenchmark
WORKDIR  /ocrbenchmark
RUN pip install .

ENTRYPOINT ["sh", "-c"]
CMD ["./run.sh"]
