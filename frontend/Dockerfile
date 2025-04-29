FROM ghcr.io/cirruslabs/flutter:stable AS build
RUN useradd -ms /bin/bash flutteruser
RUN chown -R flutteruser:flutteruser /sdks/flutter

WORKDIR /app
COPY . .

RUN chown -R flutteruser:flutteruser /app

USER flutteruser
RUN git config --global --add safe.directory /sdks/flutter
RUN flutter pub get
RUN flutter build web

FROM node:23-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/build/web ./web
CMD ["serve", "-s", "web", "-l", "80"]
