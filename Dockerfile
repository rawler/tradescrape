FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME /data

ENTRYPOINT ["python", "./ts.py", "--db=/data/tradescrape.db"]
CMD ["run"]

