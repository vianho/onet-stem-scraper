FROM python:3.13-rc-slim

COPY . .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
