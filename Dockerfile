FROM python:3.13-rc-alpine3.17

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
