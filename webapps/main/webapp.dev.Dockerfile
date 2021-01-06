FROM node:15

WORKDIR /main
COPY package.json .
COPY package-lock.json .
RUN npm install

# Next round might make sense to not include these in the dockerfile for the dev environment, but simply mount them as volumes so in case of changes we don't need to rebuild the image.
COPY vue.config.js babel.config.js .eslintrc.js ./

# These are also mounted as a bind volume to make HMR work
# COPY public public
# COPY src src
