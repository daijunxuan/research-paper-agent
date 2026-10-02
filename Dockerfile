FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir '.[local]'
EXPOSE 8765
CMD ["uvicorn", "paper_agent.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8765"]

