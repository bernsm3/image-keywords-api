import requests
import json

# print(requests.get('http://localhost:5000/images/').json())
print(json.dumps(
    requests.get('http://localhost:5000/history/images/00000000bbbbbbbb').json(),
    sort_keys=True, indent=4
))
print(requests.post('http://localhost:5000/images/00000000bbbbbbbb',
    data={
        'category':'Mood',
        'keyword' :'Thrilling'
    }
))
print(requests.delete('http://localhost:5000/images/00000000bbbbbbbb',
    data={
        'category':'Mood'
    }
))
print(json.dumps(
    requests.get('http://localhost:5000/images/00000000bbbbbbbb').json(),
    sort_keys=True, indent=4
))
print(requests.put('http://localhost:5000/images/new',
    data={
        'Mood':'Melancholy'
    }
))
print(json.dumps(
    requests.get('http://localhost:5000/history/images/new').json(),
    sort_keys=True, indent=4
))
requests.get('http://localhost:5000/history/keywords/Mood')
requests.delete('http://localhost:5000/history/keywords/Mood/Melancholy')
requests.put('http://localhost:5000/history/keywords/NewCat/NewKW')
requests.delete('http://localhost:5000/history/keywords/NewCat')
