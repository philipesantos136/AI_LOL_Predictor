import requests
versions = ["15.5.1", "15.4.1", "14.24.1", "14.19.1"]
for v in versions:
    url = f"https://ddragon.leagueoflegends.com/cdn/{v}/img/champion/Aurora.png"
    try:
        r = requests.head(url, timeout=5)
        print(f"Version {v}: {r.status_code}")
    except:
        print(f"Version {v}: Error")
