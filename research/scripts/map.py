# Assign quarters (Stadtteile) to survey areas (Umfragebezirke) by overlap of their WFS geometries.
# Call: python map.py <Umfragebezirke.gml> <Stadtteile.gml>
import re, sys
from shapely.geometry import Polygon
from shapely.ops import unary_union
def load(path, name_field):
    text=open(path).read(); out={}
    for member in re.split(r'<wfs:member>', text)[1:]:
        name=re.search(rf'<[^>]*:{name_field}>([^<]*)<', member).group(1)
        polys=[]
        for polygon in re.findall(r'<gml:Polygon.*?</gml:Polygon>', member, re.S):
            rings=re.findall(r'<gml:posList[^>]*>(.*?)</gml:posList>', polygon, re.S)
            def points(t): v=list(map(float,t.split())); return list(zip(v[0::2], v[1::2]))
            if rings: polys.append(Polygon(points(rings[0]), [points(r) for r in rings[1:]]).buffer(0))
        out[name]=unary_union(polys)
    return out
survey_areas=load(sys.argv[1],'UMFBZ_NAME')
text=open(sys.argv[2]).read(); first_member=re.split(r'<wfs:member>', text)[1]
fields=re.findall(r'<Stadtgebietsgliederung:([A-Za-z_]+)>[^<]', first_member); print(fields)
name_field=[f for f in fields if 'NAME' in f.upper()][0]
quarters=load(sys.argv[2], name_field)
for area, geometry in survey_areas.items():
    parts=[]
    for name, quarter in quarters.items():
        overlap=geometry.intersection(quarter).area
        if overlap>0.05*quarter.area: parts.append(f"{name} ({100*overlap/quarter.area:.0f}%)" if overlap<0.95*quarter.area else name)
    print(f"{area}: {', '.join(sorted(parts))}")
