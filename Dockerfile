FROM python:3.8-slim-buster

# Create a working directory.
RUN mkdir wd
WORKDIR wd

# Install Python dependencies.
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the rest of the codebase into the image
COPY . ./
EXPOSE 8000

# Finally, run gunicorn.
CMD [ "gunicorn", "--workers=4", "--threads=1", "-b 0.0.0.0:8000", "app:server"]
