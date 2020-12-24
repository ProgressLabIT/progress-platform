FROM node:15

WORKDIR /main
COPY package.json .
COPY package-lock.json .
RUN npm install

COPY vue.config.js babel.config.js .eslintrc.js ./
COPY public public
COPY src src
