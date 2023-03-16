# TO BUILD:
# docker build -t nex/late-tracker:latest .
# And then to run:
# docker run -it --name late-tracker -p 80:80 nex/late-tracker:latest
# Change the first 80 to whichever port you want to expose on the host machine. Leave the second 80 as is.
FROM nginx:1

RUN apt-get update

RUN apt-get install -y python3 python3-fastapi python3-uvicorn python3-multipart curl

# Need to add NodeSource PPA for latest node.js & npm installs
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -

RUN apt-get update

# Now we can install nodejs
RUN apt-get install -y nodejs

COPY web/nginx.conf /etc/nginx/conf.d/default.conf

COPY web /web

WORKDIR /web

RUN npm i

RUN npm run build

RUN npm run export

COPY server /server

COPY start.sh /start.sh

ENTRYPOINT ["/bin/bash"]

CMD ["/start.sh"]
