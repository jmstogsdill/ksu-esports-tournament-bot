FROM python:3.12.6

COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY . .
# Specify the command to run your bot
CMD ["python3", "bot.py"]


COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Specify the command to run your bot
CMD ["python3", "bot.py"]
