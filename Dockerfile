FROM python:3.12.6

COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Specify the command to run the bot
CMD ["python3", "bot.py"]
