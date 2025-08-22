# Use the official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Do NOT copy the credentials; we'll mount them at runtime

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
