##### GRAPH CREATION IMAGE #####
FROM python:3.9.7-bullseye as app

# create needed folders
RUN mkdir -p ontologies
RUN mkdir -p src
RUN mkdir -p alignment
RUN mkdir -p data

# copy ontologies files from host ontologies folder to container ontologies folder
COPY ontologies/ ./ontologies

# copy alignment files from host alignment folder to container alignment folder
COPY alignment/ ./alignment

# copy files from host src folder to container src folder
COPY src/ ./src

# copy files from host data folder to container data folder
COPY data/ ./data

# copy requirements file from knowledge_graph folder to container knowledge_graph folder
COPY requirements.txt ./

# run copied scripts
RUN pip install -r requirements.txt
RUN python -u src/main.py 

# copy ontology to shared space
RUN mkdir -p ./shared_space/ontologies
RUN cp -a ./ontologies/. ./shared_space/ontologies

# ENTRYPOINT ["tail"]
# CMD ["-f","/dev/null"]