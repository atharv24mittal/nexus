FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal on purpose: z3-solver ships prebuilt wheels,
# scikit-learn ships prebuilt wheels too — no compiler toolchain needed,
# which keeps the image small and the Render free-tier build fast.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

# Render injects $PORT at runtime; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
