FROM python
RUN mkdir /app
COPY ./requirements.txt ./bot.py /app/
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "/app/bot.py"]