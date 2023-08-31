FROM python
RUN mkdir /app
COPY ./requirements.txt ./src/* /app/
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "/app/bot.py"]