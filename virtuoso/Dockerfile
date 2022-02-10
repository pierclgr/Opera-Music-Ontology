# ##### GRAPH CREATION IMAGE ##### FROM python:3.9.7-bullseye as app
#
# WORKDIR /src
# COPY src/ ./
#
# RUN pip install -r requirements.txt
# RUN chmod +x prep_data.sh \
#     && ./prep_data.sh \
#     && python main.py
#
# ##### VIRTUOSO ENDPOINT IMAGE #####
# FROM tenforce/virtuoso:1.3.1-virtuoso7.2.2
#
# # Add Virtuoso bin to the PATH
# ENV PATH /usr/local/virtuoso-opensource/bin/:$PATH
#
# # Copy ontologies
# COPY --from=app src/ontologies/ /usr/local/virtuoso-opensource/share/virtuoso/vad/ontologies/
#
# # Add Virtuoso config
# COPY virtuoso/virtuoso.ini /virtuoso.ini
#
# # Add dump_nquads_procedure
# COPY virtuoso/dump_nquads_procedure.sql /dump_nquads_procedure.sql
#
# # Add Virtuoso log cleaning script
# COPY virtuoso/clean-logs.sh /clean-logs.sh
#
# # Add startup script
# COPY virtuoso/virtuoso.sh /virtuoso.sh
#
# VOLUME /data
# WORKDIR /data
# EXPOSE 8890
# EXPOSE 1111
#
# CMD ["/bin/bash", "/virtuoso.sh"]

##### GRAPH CREATION IMAGE #####
FROM python:3.9.7-bullseye as app

WORKDIR /src
COPY src/ ./

RUN pip install -r requirements.txt
RUN sed -i -e 's/\r$//' prep_data.sh \
    && chmod +x prep_data.sh \
    && ./prep_data.sh \
    && python main.py

##### VIRTUOSO ENDPOINT IMAGE #####
FROM tenforce/virtuoso:1.3.1-virtuoso7.2.2

# Add Virtuoso bin to the PATH
ENV PATH /usr/local/virtuoso-opensource/bin/:$PATH

# Copy ontologies
COPY --from=app src/ontologies/ /usr/local/virtuoso-opensource/share/virtuoso/vad/ontologies/

# Add Virtuoso config
COPY virtuoso/virtuoso.ini /virtuoso.ini

# Add dump_nquads_procedure
COPY virtuoso/dump_nquads_procedure.sql /dump_nquads_procedure.sql

# Add Virtuoso log cleaning script
COPY virtuoso/clean-logs.sh /clean-logs.sh

# Add startup script
COPY virtuoso/virtuoso.sh /virtuoso.sh

RUN sed -i -e 's/\r$//' /virtuoso.sh

VOLUME /data
WORKDIR /data
EXPOSE 8890
EXPOSE 1111

CMD ["/bin/bash", "/virtuoso.sh"]
