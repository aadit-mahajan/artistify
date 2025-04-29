FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip

# Install dependencies
RUN pip install --no-cache-dir nltk

# Downloading NLTK data files
RUN python -m nltk.downloader punkt stopwords wordnet
RUN pip install -r requirements.txt

EXPOSE 12000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "12000"]
