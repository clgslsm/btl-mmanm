FROM python:3.10-slim

RUN apt update && apt upgrade -y
RUN apt install ca-certificates

COPY sso.crt /usr/local/share/ca-certificates/sso.example.org.crt

RUN update-ca-certificates

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/sso.example.org.pem
EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]