FROM  maven:3.6.3-jdk-8

ARG LODE_EXTERNAL_URL
# ARG WEBVOWL_EXTERNAL_URL
ARG USE_HTTPS

RUN cd /opt && \
	git clone https://github.com/essepuntato/LODE.git

# RUN echo "externalURL=${LODE_EXTERNAL_URL}\nwebvowl=${WEBVOWL_EXTERNAL_URL}\nuseHTTPs=${USE_HTTPS}" > /opt/LODE/src/main/webapp/config.properties
# RUN echo "externalURL=${LODE_EXTERNAL_URL}\nuseHTTPs=${USE_HTTPS}" > /opt/LODE/src/main/webapp/config.properties
# RUN echo "externalURL=${LODE_EXTERNAL_URL}" > /opt/LODE/src/main/webapp/config.properties
#RUN cat /opt/LODE/src/main/webapp/config.properties
COPY config.properties /opt/LODE/src/main/webapp/config.properties

WORKDIR /opt/LODE

EXPOSE 8080
EXPOSE 9090

ENTRYPOINT ["mvn", "clean", "jetty:run"]
