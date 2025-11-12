FROM node:20-alpine as build-stage
WORKDIR /app
RUN npm i --location=global @quasar/cli@latest
COPY package.json yarn.lock ./
RUN yarn
COPY . .
RUN yarn quasar build -m spa

FROM nginx:1.18
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html

