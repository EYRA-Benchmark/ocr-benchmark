FROM python:3-slim
WORKDIR /app
ADD . .
RUN pip install -r requirements.txt
ENTRYPOINT ["sh", "-c"]
CMD ["./run.sh"]