# Use the official Streamlit image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
# This tells Google Cloud client libraries where to find your service account key.
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/eternal-bongo-435614-b9-0127167e0d20.json"

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8081", "--server.address=0.0.0.0"]