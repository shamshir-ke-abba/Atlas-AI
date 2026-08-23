FROM python:3.11-slim

WORKDIR /app

# Copy all files first (before pip install)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (informational, Railway uses this)
EXPOSE 8000

# Start the web server
# Use python -m uvicorn to match your RUN_WEB.sh approach
CMD ["python", "-m", "uvicorn", "interfaces.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
