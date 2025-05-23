import requests

url = "http://127.0.0.1:5000/upload"
files = {"resume": open("PATH_TO_YOUR_RESUME_PDF.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
