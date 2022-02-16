##### VIRTUOSO ENDPOINT #####
FROM tenforce/virtuoso:1.3.1-virtuoso7.2.2

# Add Virtuoso bin to the PATH
ENV PATH /usr/local/virtuoso-opensource/bin/:$PATH

# Add Virtuoso config
COPY virtuoso/virtuoso.ini /virtuoso.ini

# Add dump_nquads_procedure
COPY virtuoso/dump_nquads_procedure.sql /dump_nquads_procedure.sql

# Add Virtuoso log cleaning script
COPY virtuoso/clean-logs.sh /clean-logs.sh

# Add startup script
COPY virtuoso/virtuoso.sh /virtuoso.sh

# Add ontology copying script
COPY knowledge_graph/src/virtuoso-ontologies.sh /virtuoso-ontologies.sh

VOLUME /data
WORKDIR /data

EXPOSE 8890
EXPOSE 1111

# CMD ["/bin/bash", "/virtuoso.sh"]