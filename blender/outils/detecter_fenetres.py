# Repère les fenêtres du dessin : les petites zones blanches fermées et presque rectangulaires
# dans les maisons. Usage : python detecter_fenetres.py carte-a-imprimer.png fenetres.json
# ATTENTION : la détection trouve aussi les panneaux de mur entre les poutres. La liste fenetres.json
# a été triée à la main : on n a gardé que les vraies fenêtres (celles qui ont un cadre ou des croisillons).
import cv2, numpy as np, json, sys
src = sys.argv[1]; out = sys.argv[2]
img = cv2.imread(src, cv2.IMREAD_UNCHANGED)
if img.shape[2]==4:
    a = img[:,:,3:4]/255.0; img = (img[:,:,:3]*a + 255*(1-a)).astype(np.uint8)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
H,W = g.shape; print(W,H)
lines = (g < 160).astype(np.uint8)
lines = cv2.dilate(lines, np.ones((3,3),np.uint8))
free = 1 - lines
n, lab, st, cen = cv2.connectedComponentsWithStats(free, 4)
zones = {'maisons':(109,486,856,1005),'chateau':(1801,294,2452,710),'pont':(851,648,1897,867)}
res=[]
dbg = img.copy()
for i in range(1,n):
    x,y,w,h,a = st[i]
    if w<12 or h<14 or w>90 or h>110: continue
    fill = a/(w*h)
    if fill < 0.80: continue
    cx,cy = x+w/2, y+h/2
    zone=None
    for k,(x0,y0,x1,y1) in zones.items():
        if x0<=cx<=x1 and y0<=cy<=y1: zone=k
    if not zone: continue
    if zone=='pont': continue
    res.append({'zone':zone,'box':[int(x),int(y),int(x+w),int(y+h)]})
    cv2.rectangle(dbg,(x,y),(x+w,y+h),(0,0,255),3)
print(len(res)); json.dump(res, open(out,'w'), indent=1)
cv2.imwrite(out.replace('.json','_dbg.png'), dbg)
