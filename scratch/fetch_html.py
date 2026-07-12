import urllib.request

try:
    url = "http://localhost:8005/"
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')
    with open("scratch/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Successfully fetched HTML and wrote to scratch/index.html")
except Exception as e:
    print("Error fetching page:", e)
