FROM python:3.12-slim

RUN apt update && apt upgrade -y
RUN apt install -y ca-certificates

COPY sso.crt /usr/local/share/ca-certificates/sso.example.org.crt

RUN update-ca-certificates

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
RUN cat /usr/local/share/ca-certificates/sso.example.org.crt | tee -a /usr/local/lib/python3.12/site-packages/certifi/cacert.pem
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]