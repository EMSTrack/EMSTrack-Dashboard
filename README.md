# EMSTrack-Dashboard
A web application to keep track of ambulance routes.

## To Run Locally:
1. Install Python
2. pip install dependencies:
```
pip install -r requirements.txt
```
3. Run the server:
```
python index.py
```
4. Go to http://localhost:8050

## To Run with Docker:
1. Install Docker
2. Build Image:
```
docker build -t dash .
```
4. Run Image:
```
docker run -p 8000:8000 dash
```
