FROM node:15 AS builder

WORKDIR /app

COPY package.json .
COPY package-lock.json .

RUN npm install

COPY babel.config.js .
COPY vue.config.js .
COPY src .
COPY public . # This will have to be a volume

RUN npm build

FROM nginx:1.18
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY --from=builder /webapps/main/dist/* /usr/share/nginx/html
