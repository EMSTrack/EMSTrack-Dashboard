# EMSTrack-Dashboard
A web application to keep track of ambulance routes. Remember to get the config.yml file and add it to the root of the directory.

## To Run Locally:
1. Install Python
2. pip install dependencies:
```
pip install -r requirements.txt
```
3. Set the appropriate environment variables (ask team members for .bash_profile)
4. Run the server:
```
python app.py
```
5. Go to http://127.0.0.1:8050

## To Run with Docker:
1. Install Docker
2. Build Image:
```
docker build -t dash .
```
3. Set the approriate environment variables in local.env (ask team members)
4. Run Image:
```
docker run --env-file local.env -p 8000:8000 dash
```
5. Go to http://localhost:8000
