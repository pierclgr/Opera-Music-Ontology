FROM nginx

RUN apt-get update && \
	apt-get install -y git && \
	git clone https://github.com/LodLive/LodLive.git && \
	mv LodLive/* /usr/share/nginx/html/

# COPY lodlive.profile.js /usr/share/nginx/html/js/
COPY js/* /usr/share/nginx/html/js/
