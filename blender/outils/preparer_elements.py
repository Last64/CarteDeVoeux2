# Fabrique les images de la version nuit (néons, ampoules, fenêtre, lune, lanterne, voile...)
# et calcule la position des fenêtres et des ampoules des guirlandes (elements.json).
# Usage : python preparer_elements.py <dossier CarteDeVoeux> blender/elements fenetres.json
import cv2, numpy as np, json, os, sys, random
from PIL import Image, ImageDraw, ImageFilter
SRC = sys.argv[1]   # CarteDeVoeux
DST = sys.argv[2]   # CarteDeVoeux2/blender/elements
os.makedirs(DST, exist_ok=True)
CAL = os.path.join(SRC, 'blender', 'calques')
INFO = json.load(open(os.path.join(CAL, 'calques.json')))
out = {}
random.seed(2027)

def hexc(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16) for i in (0,2,4)],np.float32)

def save_rgba(name, rgb, a):
    a = np.clip(a,0,1)
    im = np.dstack([np.clip(rgb,0,255), a*255]).astype(np.uint8)
    Image.fromarray(im,'RGBA').save(os.path.join(DST,name+'.png'), optimize=True)

def blur(a, s): return cv2.GaussianBlur(a, (0,0), s)

# ---------- néons
def neon(nom, coeur_hex, halo_hex, mode, pad=44, largeur=5, sigma=13, force=1.0, dil=5):
    if mode == 'plein':   # le texte : on reprend les lettres fines du dessin imprimé
        x0,y0,x1,y1 = INFO[nom]['box']
        g = np.array(Image.open(os.path.join(SRC,'impression','carte-a-imprimer.png')).convert('L'))[y0:y1, x0:x1]
        al = (g < 110).astype(np.uint8)
    else:
        im = np.array(Image.open(os.path.join(CAL, nom+'.png')).convert('RGBA'))
        al = (im[:,:,3] > 128).astype(np.uint8)
    al = np.pad(al, pad)
    if mode == 'contour':
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(largeur,largeur))
        coeur = cv2.morphologyEx(al, cv2.MORPH_GRADIENT, k).astype(np.float32)
    else:
        coeur = al.astype(np.float32)
    coeur = blur(coeur, 0.8)
    halo = blur(cv2.dilate(coeur,np.ones((dil,dil),np.uint8)), sigma)
    halo = halo / max(halo.max(),1e-6) * 0.85 * force
    a = np.maximum(coeur, halo)
    w = (coeur / np.maximum(a,1e-6))[...,None]
    rgb = hexc(coeur_hex)*w + hexc(halo_hex)*(1-w)
    save_rgba('neon_'+nom, rgb, a)
    x0,y0,x1,y1 = INFO[nom]['box']
    out['neon_'+nom] = [x0-pad, y0-pad, x1+pad, y1+pad]

for c in ('chiffre_2a','chiffre_0','chiffre_2b','chiffre_7'):
    neon(c, '#fff6d6', '#ffae2b', 'contour', largeur=7, sigma=14)
neon('texte', '#f2fbff', '#4fc3ff', 'plein', pad=30, sigma=7, force=0.55, dil=1)

# ---------- texture radiale générique
def radial(name, size, core_hex, halo_hex, r_core, r_glow, core_white=0.0):
    yy,xx = np.mgrid[0:size,0:size]; c=(size-1)/2
    d = np.hypot(xx-c, yy-c)
    core = np.clip((r_core - d)/1.5+1,0,1)
    glow = np.exp(-(d/r_glow)**2*2.2)*0.9
    a = np.maximum(core, glow); a[d>size/2-1]=0
    w = (core/np.maximum(a,1e-6))[...,None]
    rgb = hexc(core_hex)*w + hexc(halo_hex)*(1-w)
    if core_white:
        wc = np.clip((r_core*0.5-d)/1.5+1,0,1)[...,None]*core_white
        rgb = rgb*(1-wc)+255*wc
    save_rgba(name, rgb, a)

AMPOULES = {'chaud':('#ffe3a0','#ffb02e'), 'rouge':('#ffb0a8','#ff3b2f'), 'vert':('#c8ffc0','#36d65a'),
            'bleu':('#c9e8ff','#3f9dff'), 'or':('#fff2b8','#ffcc33')}
for k,(c,h) in AMPOULES.items(): radial('ampoule_'+k, 64, c, h, 6, 22, core_white=0.8)
radial('flocon', 32, '#ffffff', '#dfefff', 4, 9)

# ---------- fenêtre allumée (rectangle intérieur = 50 % centraux)
S=96; yy,xx=np.mgrid[0:S,0:S]
dx = np.maximum(np.abs(xx-(S-1)/2)-S/4, 0); dy=np.maximum(np.abs(yy-(S-1)/2)-S/4, 0)
d = np.hypot(dx,dy)
core = np.clip(1-d/1.2,0,1)
glow = np.exp(-(d/14)**2*2)*0.75
a = np.maximum(core,glow)
cy = np.clip(1-np.hypot(xx-S/2,yy-S/2)/(S/3),0,1)[...,None]
rgb = hexc('#ffb84a')*(1-cy) + hexc('#fff0b8')*cy
save_rgba('fenetre', rgb, a)

# ---------- étoile scintillante (4 branches)
S=64; yy,xx=np.mgrid[0:S,0:S]; c=(S-1)/2; X=np.abs(xx-c); Y=np.abs(yy-c)
branche = np.maximum(np.exp(-X/1.6)*np.clip(1-Y/30,0,1), np.exp(-Y/1.6)*np.clip(1-X/30,0,1))
a = np.clip(branche*1.3 + np.exp(-(np.hypot(X,Y)/7)**2)*0.9,0,1)
save_rgba('etoile', np.dstack([np.full((S,S),255.)]*2+[np.full((S,S),225.)]), a)

# ---------- lune (croissant + halo)
S=320; yy,xx=np.mgrid[0:S,0:S]; c=S/2
d1=np.hypot(xx-c,yy-c); d2=np.hypot(xx-c-34,yy-c+22)
disque=np.clip((78-d1)/1.5,0,1); creux=np.clip((70-d2)/1.5,0,1)
crois = disque*(1-creux)
halo = np.exp(-(d1/105)**2*2.5)*0.55
a=np.maximum(crois,halo)
w=(crois/np.maximum(a,1e-6))[...,None]
rgb=hexc('#fff4cc')*w+hexc('#b9c9ff')*(1-w)
save_rgba('lune', rgb, a)

# ---------- lanterne tenue par la cigogne (point d'accroche = haut, au milieu)
W2,H2=240,300; im=Image.new('RGBA',(W2,H2),(0,0,0,0))
gl=np.zeros((H2,W2),np.float32); cx=W2//2
yy,xx=np.mgrid[0:H2,0:W2]
gl=np.exp(-(np.hypot(xx-cx,yy-150)/80)**2*2)*0.8
g=np.dstack([np.full((H2,W2),255.),np.full((H2,W2),190.),np.full((H2,W2),80.),gl*255]).astype(np.uint8)
im=Image.alpha_composite(im,Image.fromarray(g,'RGBA'))
dr=ImageDraw.Draw(im)
dr.line([(cx,0),(cx,108)],fill=(60,45,40,255),width=4)
dr.polygon([(cx-26,120),(cx+26,120),(cx+14,106),(cx-14,106)],fill=(70,50,40,255))
dr.ellipse([cx-8,96,cx+8,112],outline=(70,50,40,255),width=4)
dr.rectangle([cx-22,120,cx+22,178],fill=(255,214,120,255),outline=(70,50,40,255),width=5)
dr.rectangle([cx-10,130,cx+10,168],fill=(255,248,215,255))
dr.line([(cx,120),(cx,178)],fill=(70,50,40,255),width=3)
dr.polygon([(cx-26,178),(cx+26,178),(cx+18,190),(cx-18,190)],fill=(70,50,40,255))
im.save(os.path.join(DST,'lanterne.png'),optimize=True)

# ---------- étoile filante (tête à droite)
W3,H3=480,48; yy,xx=np.mgrid[0:H3,0:W3]
t=xx/W3; dy=np.abs(yy-H3/2)
a=np.clip((t**2.2)*np.exp(-(dy/(1+4*t))**2),0,1)
tete=np.exp(-(np.hypot(xx-(W3-24),yy-H3/2)/9)**2)
a=np.maximum(a,tete)
save_rgba('filante', np.dstack([np.full((H3,W3),255.)]*2+[np.full((H3,W3),235.)]), a)

# ---------- voile de nuit (bas fondu, pour qu'il « tombe » en douceur)
W4,H4=635,310; yy,xx=np.mgrid[0:H4,0:W4]; t=yy/(H4-1)
a=0.86-0.14*t
a=a*np.clip((1-t)/0.015,0,1)
rgb=np.dstack([np.full((H4,W4),c) for c in (10,20,52)]).astype(np.float32)
rgb=rgb*(1-t[...,None]*0.25)+np.array([28,40,86])*t[...,None]*0.25
save_rgba('voile_nuit', rgb, a)

# ---------- positions : fenêtres, guirlandes, sapins
fen = json.load(open(sys.argv[3]))
win=[f['box'] for f in fen]
win += [[2290,354,2313,392],[2127,425,2147,452]]   # fenêtres du château (dessinées à la main)
out['fenetres']=win

def contour_haut(nom, x_pas=4, decal=6):
    im=np.array(Image.open(os.path.join(CAL,nom+'.png')).convert('RGBA'))[:,:,3]>128
    x0,y0,_,_=INFO[nom]['box']; pts=[]
    for x in range(0,im.shape[1],x_pas):
        col=np.where(im[:,x])[0]
        if len(col): pts.append((x0+x, y0+col[0]-decal))
    return pts

def le_long(pts, pas):
    pts=np.array(pts,np.float32)
    # lissage léger
    k=5; ps=np.array([pts[max(0,i-k):i+k+1].mean(0) for i in range(len(pts))])
    seg=np.hypot(*np.diff(ps,axis=0).T); L=np.concatenate([[0],np.cumsum(seg)])
    res=[]
    for s in np.arange(pas/2, L[-1], pas):
        i=np.searchsorted(L,s)-1; i=max(0,min(i,len(ps)-2)); f=(s-L[i])/max(seg[i],1e-6)
        res.append((ps[i]+(ps[i+1]-ps[i])*f).tolist())
    return res

COUL=['rouge','vert','bleu','or']
amp=[]
for p in le_long(contour_haut('maisons'), 34): amp.append({'p':p,'c':'chaud','g':'maisons'})
for p in le_long(contour_haut('chateau', decal=4), 40): amp.append({'p':p,'c':'chaud','g':'chateau'})
# pont : guirlandes qui pendent entre des piquets posés sur le parapet
pont=contour_haut('pont', decal=2); pont=np.array(pont,np.float32)
xs=np.linspace(pont[0,0]+10, pont[-1,0]-10, 8)
def y_pont(x): return float(np.interp(x,pont[:,0],pont[:,1]))
for a_,b_ in zip(xs[:-1],xs[1:]):
    for j in range(0,6):
        t=j/6; x=a_+(b_-a_)*t
        y=y_pont(x)-14+ 26*np.sin(np.pi*t)
        amp.append({'p':[float(x),float(y)],'c':COUL[j%4] if j else 'or','g':'pont'})
# sapins : ampoules de couleurs posées au hasard dans la silhouette
for nom,n in (('sapin_1',8),('sapins_2',18)):
    im=np.array(Image.open(os.path.join(CAL,nom+'.png')).convert('RGBA'))[:,:,3]>128
    im=cv2.erode(im.astype(np.uint8),np.ones((9,9),np.uint8))
    ys,xs_=np.where(im); x0,y0,_,_=INFO[nom]['box']; pris=[]
    for _ in range(4000):
        if len(pris)>=n: break
        i=random.randrange(len(xs_)); q=(x0+xs_[i],y0+ys[i])
        if all(np.hypot(q[0]-r[0],q[1]-r[1])>22 for r in pris): pris.append(q)
    for k,q in enumerate(pris): amp.append({'p':[float(q[0]),float(q[1])],'c':COUL[k%4],'g':'sapins'})
out['ampoules']=amp
json.dump(out, default=float, fp=open(os.path.join(DST,'elements.json'),'w'), indent=1)
print(len(win),'fenêtres', len(amp),'ampoules')
