"""Build the standalone stellar map from the dated, packaged catalogue snapshot."""
from pathlib import Path
import json,math,html,re

def build(site=None):
 site=Path(site) if site else Path(__file__).resolve().parents[1]
 path=site/'data/local-universe-2026-10-30.json';data=json.loads(path.read_text(encoding='utf8'))
 matrix=data['frame']['ICRS_to_galactic'];stars=[]
 names={'Alfa Centauri A + B':'Alfa Centauri A/B','Sirius A + B':'Sirius A/B','BL Ceti + UV Ceti':'BL/UV Ceti'}
 for row in data['stars']:
  a=row['catalog_record'];ra0,dec0=map(math.radians,[float(a['RA']),float(a['DEC'])]);dt=2016.-float(a['EPOCH'])
  # Tangent-plane proper motion; sufficient for an educational map over 16 years.
  ra=ra0+math.radians(float(a['PMRA'] or 0)*dt/3600000)/math.cos(dec0)
  dec=dec0+math.radians(float(a['PMDEC'] or 0)*dt/3600000)
  d=row['distance_ly'];v=[d*math.cos(dec)*math.cos(ra),d*math.cos(dec)*math.sin(ra),d*math.sin(dec)]
  xyz=[sum(x*y for x,y in zip(axis,v)) for axis in matrix]
  star=dict(name=row['name'],short_name=names.get(row['name'],row['name']),kind=row['kind'],distance_ly=d,xyz_ly=xyz,
   color='#7dcfff' if row['kind'].startswith('A') else '#ffd287' if row['kind'].startswith('G') else '#ff9d87',
   system='Alfa Centauri' if row['name'] in ['Proxima Centauri','Alfa Centauri A + B'] else row['name'],
   coordinate_epoch=2016.,input_epoch=float(a['EPOCH']),ra_deg=math.degrees(ra),dec_deg=math.degrees(dec),source=row['source'])
  assert abs(math.sqrt(sum(c*c for c in xyz))-d)<1e-8
  stars.append(star)
 data['stellar_map']={'stars':stars,'units':'light years','origin':'Sun; Alpha Centauri A/B in the optional detail','epoch':2016.,
  'method':'ICRS RA/Dec from saved The 10 pc sample v2 records; the two epoch-2000 positions are advanced to 2016 by linear tangent-plane proper motion (mu_alpha*cos_delta, mu_delta). Rounded distances match the approved table; no orbital or radial propagation. Matrix as in frame.ICRS_to_galactic. Close binary pairs represented by the saved primary component direction and common adopted distance. This is a static educational position map, not an ephemeris.'}
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 original=(site/'assets/kosmopedie/galakticke-okoli.html').read_text(encoding='utf8');style=re.search(r'<style>(.*?)</style>',original,re.S)[1]
 rows=[]
 for row in stars:
  label='RECONS' if 'recons' in row['source'] else 'The 10 pc sample'
  rows.append('<tr><td>'+html.escape(row['name'])+'</td><td>'+str(f"{row['distance_ly']:.2f}").replace('.',',')+'</td><td>'+html.escape(row['kind'])+'</td></tr>')
 template=(site/'tools/templates/nearby-star-map.html').read_text(encoding='utf8')
 template=template.replace('__STYLE__',style).replace('__DATA__',json.dumps({'stars':stars},ensure_ascii=False).replace('</','<\\/')).replace('__ROWS__',''.join(rows))
 out=site/'assets/kosmopedie/nejblizsi-hvezdy.html';out.write_text(template,encoding='utf8');return out
if __name__=='__main__':print(build())
