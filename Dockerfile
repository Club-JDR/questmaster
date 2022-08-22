FROM node:lts-alpine3.15
WORKDIR /app
RUN apk upgrade

COPY package*.json /tmp/
RUN cd /tmp \
  && CI=true npm ci \
  && mv /tmp/node_modules /app \
  && cd /app

COPY . /app

EXPOSE 8080
CMD [ "node", "server.js" ]