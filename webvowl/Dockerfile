# Use tomcat java 8 alpine as base image
FROM tomcat:9-jre8-alpine

# Build time arguments (WebVOWL version)
ARG version=1.1.7

# Download WebVOWL to tomcat webapps directory as webvowl app
RUN rm -rf /usr/local/tomcat/webapps/* && \
    wget -O /usr/local/tomcat/webapps/webvowl.war http://vowl.visualdataweb.org/downloads/webvowl_1.1.7.war

EXPOSE 8080

# Run default server
# CMD ["catalina.sh", "run"]