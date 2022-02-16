if cp -a /shared_space/ontologies/. /usr/local/virtuoso-opensource/share/virtuoso/vad/ontologies/; then
    echo "Ontologies copied to virtuoso successfully."
else
    echo "ERROR: failed to copy ontologies to virtuoso."
fi