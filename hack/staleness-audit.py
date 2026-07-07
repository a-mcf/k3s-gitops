#!/usr/bin/env python3
"""Chart staleness audit — for every HelmRelease, compare the pinned chart
version against its HelmRepository index: versions behind, pin age, and
upstream's most recent release. Flags unreferenced HelmRepositories.
Needs: kubectl access, python3-yaml. Usage: ./hack/staleness-audit.py
"""
import json, subprocess, urllib.request, datetime, gzip, yaml
try: from yaml import CSafeLoader as Loader
except ImportError: from yaml import SafeLoader as Loader

def kubectl(args):
    return json.loads(subprocess.run(["kubectl"]+args+["-o","json"],capture_output=True,text=True).stdout)

def fetch_index(url):
    req=urllib.request.Request(url.rstrip('/')+"/index.yaml",headers={'User-Agent':'staleness-audit','Accept-Encoding':'gzip'})
    r=urllib.request.urlopen(req,timeout=60); raw=r.read()
    if raw[:2]==b'\x1f\x8b': raw=gzip.decompress(raw)
    return yaml.load(raw.decode('utf-8','replace'),Loader=Loader)

def dt(iso):
    try: return datetime.datetime.fromisoformat(iso.replace('Z','+00:00'))
    except Exception: return None

NOW=datetime.datetime.now(datetime.timezone.utc)
def age(d): return (NOW-d).days if d else None

repos={i['metadata']['name']:i['spec']['url'] for i in kubectl(["get","helmrepositories","-A"])['items']}
hrs={}
for i in kubectl(["get","helmreleases","-A"])['items']:
    spec=i['spec'].get('chart',{}).get('spec')
    if not spec: continue
    key=(spec['chart'],spec.get('version','?'),spec['sourceRef']['name'])
    hrs.setdefault(key,[]).append(i['metadata']['namespace'])

used=set(); cache={}; rows=[]
for (chart,ver,repo),nss in sorted(hrs.items()):
    used.add(repo); url=repos.get(repo)
    if not url or url.startswith('oci://'):
        rows.append((chart,ver,nss,'?',None,None,'OCI or unknown repo')); continue
    if repo not in cache:
        try: cache[repo]=fetch_index(url)
        except Exception as e: cache[repo]=f"ERR:{type(e).__name__}"
    idx=cache[repo]
    if isinstance(idx,str):
        rows.append((chart,ver,nss,'?',None,None,idx)); continue
    entries=(idx or {}).get('entries',{}).get(chart) or []
    if not entries:
        rows.append((chart,ver,nss,'?',None,None,'chart not in index')); continue
    dated=[(e.get('version'),dt(e.get('created',''))) for e in entries]
    latest_v,latest_d=max(dated,key=lambda x:(x[1] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)))
    ours_d=next((d for v,d in dated if v==ver),None)
    rows.append((chart,ver,nss,latest_v,age(ours_d),age(latest_d),''))

print(f"{'CHART':26}{'PINNED':16}{'LATEST':16}{'PIN AGE':10}{'UPSTREAM LAST':15}{'USED BY':20}NOTE")
for chart,ver,nss,latest,ourage,latage,note in sorted(rows,key=lambda r:-(r[4] if r[4] is not None else -1)):
    flag='' if ver==latest else ' *'
    print(f"{chart:26}{ver:16}{str(latest):16}{str(ourage)+'d' if ourage is not None else '?':10}{str(latage)+'d ago' if latage is not None else '?':15}{','.join(sorted(set(nss)))[:19]:20}{note}{flag}")
unused=set(repos)-used
if unused: print("\nUNREFERENCED HelmRepositories: "+", ".join(sorted(unused)))
