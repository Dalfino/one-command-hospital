FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
ARG WITH_SBERT=false
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$WITH_SBERT" = "true" ]; then pip install --no-cache-dir sentence-transformers; fi
COPY app ./app
EXPOSE 8000
# Enable with: docker compose build --build-arg WITH_SBERT=true guideline-rag
# and VECTOR_BACKEND=sbert in the service environment.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
