FROM python:3.9-slim
WORKDIR /app
COPY tool_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "tool_server.main:app", "--host", "0.0.0.0", "--port", "8001"]
