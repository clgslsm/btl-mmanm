FROM node:20 AS fe-builder

WORKDIR /app

RUN apt update && apt upgrade -y
RUN npm install -g npm@latest

COPY ./frontend/package.json ./
COPY ./frontend/package-lock.json ./
RUN npm install --verbose

COPY ./frontend .
RUN npm run build

FROM python:3.12-slim AS runner

RUN apt update && apt upgrade -y
RUN apt install -y nginx ca-certificates

COPY sso.crt /usr/local/share/ca-certificates/sso.example.org.crt

RUN update-ca-certificates

COPY --from=fe-builder /app/build /var/www/first.example.site

COPY ./nginx.conf /etc/nginx/sites-available/default
WORKDIR /opt/backend
COPY ./backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY ./backend .

WORKDIR /
COPY ./entrypoint.sh .
RUN chmod +x entrypoint.sh
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/sso.example.org.pem
ENTRYPOINT ["/entrypoint.sh"]