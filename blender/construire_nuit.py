"""
Carte de voeux 2027 — VERSION « NUIT D'HIVER » (scène Blender pour la RA).

Même carte que la version pop-up, mais une histoire complètement différente :
rien ne sort de la carte, c'est la LUMIÈRE qui raconte.

  1. La nuit tombe sur la carte (un voile bleu nuit descend comme un store), la lune se lève,
     les étoiles s'allument une à une et la neige commence à tomber.
  2. La cigogne traverse la carte de droite à gauche en portant une lanterne.
     Partout où elle passe, la ville s'allume : guirlandes sur le château et les sapins,
     néons du « 2027 » qui grésillent avant de s'allumer, guirlandes du pont,
     fenêtres et guirlandes des maisons.
  3. Une fois la cigogne partie, « Meilleurs Voeux » s'allume en néon bleu.
     Deux étoiles filantes traversent le ciel.
  4. Tout s'éteint, le jour revient (le voile remonte) et l'animation recommence.

Repères (les mêmes que la version pop-up, pour réutiliser la même cible MindAR) :
- La carte fait 1 m de large dans Blender (1 unité = largeur de la carte dans MindAR).
- La carte est posée au sol : +X = droite de la carte, +Y = haut de la carte, +Z = vers la personne.
- Tout est « sans ombre » (unlit) : ce sont des lumières, elles ne doivent pas dépendre d'un éclairage.
- Les éléments s'allument et s'éteignent avec l'ÉCHELLE (0 = éteint, 1 = allumé) :
  le glTF ne peut pas animer l'opacité d'un matériau, mais il sait animer l'échelle.
- L'animation dure 14 s (336 images à 24 i/s) et boucle : l'image 336 est identique à l'image 0.

Pour reconstruire la scène : onglet Scripting > ouvrir ce fichier > Run Script.
Export : exporter_glb() en bas du script, ou Fichier > Exporter > glTF 2.0 (réglages dans le README).
"""
import bpy, json, math, os, random
from mathutils import Vector
from bpy_extras import anim_utils

# ------------------------------------------------------------------ chemins
BLEND_DIR = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else r"C:\Users\mhdme\Documents\GitHub\CarteDeVoeux2\blender"
ELEM = os.path.join(BLEND_DIR, "elements")
CALQUES = os.path.join(BLEND_DIR, "calques")
CARTE_PNG = os.path.join(BLEND_DIR, "..", "impression", "carte-a-imprimer.png")

# ------------------------------------------------------------------ réglages
W_PX, H_PX = 2540, 1241          # taille du dessin en pixels
K = 1.0 / W_PX                   # 1 pixel = 1/2540 m  ->  la carte fait 1 m de large
H_CARTE = H_PX * K               # 0,4886 m
FPS, FIN = 24, 336               # 14 secondes
INFO = json.load(open(os.path.join(CALQUES, "calques.json"), encoding="utf-8"))
EL = json.load(open(os.path.join(ELEM, "elements.json"), encoding="utf-8"))
R = math.radians
random.seed(2027)                # toujours le même « hasard » : la scène est identique à chaque fois

# Le déroulé (en images)
NUIT_DEBUT, NUIT_FIN = 0, 40         # le voile descend
VOL_DEBUT, VOL_FIN = 44, 196         # la cigogne traverse la carte
TEXTE_ON = 204                       # « Meilleurs Voeux » s'allume
EXTINCTION = 290                     # les lumières s'éteignent (de 290 à ~306)
JOUR_DEBUT, JOUR_FIN = 300, 330      # le voile remonte


def px(x, y):
    """Pixel du dessin -> coordonnées Blender (centre de la carte = origine)."""
    return ((x - W_PX / 2) * K, (H_PX / 2 - y) * K)


# ================================================================== 1. SCÈNE
def preparer_scene():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    for d in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.actions,
              bpy.data.cameras, bpy.data.lights, bpy.data.curves):
        for x in list(d): d.remove(x)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end, sc.frame_current = 0, FIN, 0
    sc.unit_settings.system = 'METRIC'
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720


def collection(nom, parent=None):
    c = bpy.data.collections.new(nom)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


# ================================================================== 2. MATÉRIAUX
_MATS = {}

def materiau_image(nom_image, fondu=True):
    """Matériau sans ombre (KHR_materials_unlit) + transparence du PNG.
    fondu=True : bords doux (alphaMode BLEND) pour les lueurs ; False : découpe nette (MASK).
    Un seul matériau par image : toutes les ampoules d'une couleur le partagent."""
    cle_mat = (nom_image, fondu)
    if cle_mat in _MATS: return _MATS[cle_mat]
    chemin = os.path.join(ELEM, nom_image + ".png")
    if not os.path.exists(chemin): chemin = os.path.join(CALQUES, nom_image + ".png")
    mat = bpy.data.materials.new("M_" + nom_image)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear(); N = nt.nodes.new; Lk = nt.links.new
    sortie = N('ShaderNodeOutputMaterial'); sortie.location = (650, 0)
    decoupe = N('ShaderNodeMixShader'); decoupe.location = (450, 0); decoupe.label = "Transparence (alpha)"
    transp = N('ShaderNodeBsdfTransparent'); transp.location = (250, 160)
    sans_ombre = N('ShaderNodeMixShader'); sans_ombre.location = (250, -60); sans_ombre.label = "Sans ombre"
    chemin_l = N('ShaderNodeLightPath'); chemin_l.location = (0, 300)
    transp2 = N('ShaderNodeBsdfTransparent'); transp2.location = (40, 0)
    emission = N('ShaderNodeEmission'); emission.location = (40, -160)
    image = N('ShaderNodeTexImage'); image.location = (-420, -120)
    image.image = bpy.data.images.load(chemin, check_existing=True)
    image.interpolation = 'Linear'; image.extension = 'CLIP'
    Lk(image.outputs['Color'], emission.inputs['Color'])
    if fondu:
        Lk(image.outputs['Alpha'], decoupe.inputs[0])
        try: mat.surface_render_method = 'BLENDED'
        except AttributeError: pass
    else:
        arrondi = N('ShaderNodeMath'); arrondi.operation = 'ROUND'; arrondi.location = (-100, 180)
        Lk(image.outputs['Alpha'], arrondi.inputs[0]); Lk(arrondi.outputs[0], decoupe.inputs[0])
    Lk(transp.outputs[0], decoupe.inputs[1])
    Lk(chemin_l.outputs['Is Camera Ray'], sans_ombre.inputs[0])
    Lk(transp2.outputs[0], sans_ombre.inputs[1])
    Lk(emission.outputs[0], sans_ombre.inputs[2])
    Lk(sans_ombre.outputs[0], decoupe.inputs[2])
    Lk(decoupe.outputs[0], sortie.inputs['Surface'])
    mat.use_backface_culling = False
    _MATS[cle_mat] = mat
    return mat


# ================================================================== 3. PLANS
_MAILLAGES = {}

def plan(nom, image, box_px, coll, z=0.0, pivot_px=None, parent=None, fondu=True):
    """Plan qui couvre box_px (x0, y0, x1, y1 en pixels du dessin), texturé par image.
    L'origine est au pivot (le centre par défaut) : c'est autour de lui que l'élément grandit."""
    x0, y0, x1, y1 = box_px
    pxv, pyv = pivot_px or ((x0 + x1) / 2, (y0 + y1) / 2)
    cle_m = (image, round(x0 - pxv, 2), round(y0 - pyv, 2), round(x1 - pxv, 2), round(y1 - pyv, 2))
    me = _MAILLAGES.get(cle_m)
    if me is None:                     # les ampoules identiques partagent le même maillage
        me = bpy.data.meshes.new(nom + "_plan")
        me.from_pydata([((x0 - pxv) * K, (pyv - y1) * K, 0), ((x1 - pxv) * K, (pyv - y1) * K, 0),
                        ((x1 - pxv) * K, (pyv - y0) * K, 0), ((x0 - pxv) * K, (pyv - y0) * K, 0)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name="UVMap")
        for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
        me.materials.append(materiau_image(image, fondu))
        _MAILLAGES[cle_m] = me
    ob = bpy.data.objects.new(nom, me)
    coll.objects.link(ob)
    wx, wy = px(pxv, pyv)
    if parent is None:
        ob.location = (wx, wy, z)
    else:
        ob.parent = parent
        ob.location = (wx - parent.location.x, wy - parent.location.y, z)
    return ob


def vide(nom, coll, loc=(0, 0, 0), parent=None, taille=0.03, forme='PLAIN_AXES'):
    ob = bpy.data.objects.new(nom, None)
    ob.empty_display_type = forme; ob.empty_display_size = taille
    ob.location = loc
    if parent: ob.parent = parent
    coll.objects.link(ob)
    return ob


# ================================================================== 4. IMAGES CLÉS
def fcourbe(ob, chemin, index):
    ad = ob.animation_data
    sac = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return sac.fcurves.find(chemin, index=index)


def cle(ob, chemin, index, frame, valeur, interp='BEZIER', easing='AUTO', back=None):
    """Pose une image clé et règle l'interpolation du segment qui suit."""
    getattr(ob, chemin)[index] = valeur
    ob.keyframe_insert(chemin, index=index, frame=frame)
    fc = fcourbe(ob, chemin, index)
    for k in fc.keyframe_points:
        if abs(k.co.x - frame) < 1e-3:
            k.interpolation = interp; k.easing = easing
            if back is not None: k.back = back
    return fc


def cle_taille(ob, frame, s, interp='BEZIER', easing='AUTO', back=None, axes=(0, 1, 2)):
    for i in axes: cle(ob, 'scale', i, frame, s, interp, easing, back)


def sinus(ob, chemin, index, amplitude, periode, decalage, debut, fin, fondu=12):
    """Modificateur de courbe « Built-in Function » (sinus), ajouté aux images clés (Additive)."""
    fc = fcourbe(ob, chemin, index)
    m = fc.modifiers.new('FNGENERATOR')
    m.function_type, m.use_additive = 'SIN', True
    m.amplitude = amplitude
    m.phase_multiplier = 2 * math.pi / periode
    m.phase_offset = -2 * math.pi * decalage / periode
    m.use_restricted_range = True
    m.frame_start, m.frame_end = debut, fin
    m.blend_in = m.blend_out = fondu
    return m


ETEINT = 0.001   # échelle « éteinte » (0 pile pose problème à certains lecteurs glTF)

def allumer(ob, f_on, f_off, taille=1.0, gresille=False, duree_off=6):
    """L'élément est éteint (échelle ~0), s'allume à f_on et s'éteint à f_off.
    gresille=True : il clignote 2 fois avant de rester allumé, comme un vrai néon."""
    cle_taille(ob, 0, ETEINT, 'CONSTANT')
    if gresille:
        # paliers constants : allumé / éteint / allumé / éteint / allumé
        for f, s in ((f_on, taille), (f_on + 2, ETEINT), (f_on + 5, taille), (f_on + 7, ETEINT), (f_on + 12, taille)):
            cle_taille(ob, f, s, 'CONSTANT')
        cle_taille(ob, f_off, taille, 'SINE', 'EASE_IN')
    else:
        cle_taille(ob, f_on, ETEINT, 'BACK', 'EASE_OUT', back=2.2)
        cle_taille(ob, f_on + 6, taille)
        cle_taille(ob, f_off, taille, 'SINE', 'EASE_IN')
    cle_taille(ob, f_off + duree_off, ETEINT, 'CONSTANT')
    cle_taille(ob, FIN, ETEINT, 'CONSTANT')


# ================================================================== 5. LA NUIT TOMBE
def construire_voile(coll):
    """Un store bleu nuit : son origine est en haut de la carte, il descend en s'étirant (échelle Y)."""
    haut = H_PX / 2
    ob = plan("Voile_nuit", "voile_nuit", (0, 0, W_PX, H_PX), coll, z=0.002, pivot_px=(W_PX / 2, 0))
    ob.scale = (1, ETEINT, 1)
    cle(ob, 'scale', 1, NUIT_DEBUT, ETEINT, 'SINE', 'EASE_OUT')
    cle(ob, 'scale', 1, NUIT_FIN, 1.0)
    cle(ob, 'scale', 1, JOUR_DEBUT, 1.0, 'SINE', 'EASE_IN')
    cle(ob, 'scale', 1, JOUR_FIN, ETEINT, 'CONSTANT')
    cle(ob, 'scale', 1, FIN, ETEINT, 'CONSTANT')
    return ob


def construire_lune(coll):
    ob = plan("Lune", "lune", (300, 40, 560, 300), coll, z=0.003)
    x, y = ob.location.x, ob.location.y
    allumer(ob, 18, 298, duree_off=18)
    cle(ob, 'location', 1, 0, y - 0.05, 'SINE', 'EASE_OUT')       # elle se lève…
    cle(ob, 'location', 1, 18, y - 0.05, 'SINE', 'EASE_OUT')
    cle(ob, 'location', 1, 64, y)
    cle(ob, 'location', 1, 298, y, 'SINE', 'EASE_IN')
    cle(ob, 'location', 1, 318, y - 0.03, 'CONSTANT')                # …et se couche
    cle(ob, 'location', 1, FIN, y - 0.05, 'CONSTANT')
    cle(ob, 'rotation_euler', 2, 0, 0.0)
    sinus(ob, 'rotation_euler', 2, R(4), 120, 0, 64, 298, 20)       # elle se balance doucement
    return ob


def dans_une_boite(x, y, marge=20):
    """Vrai si le point tombe sur la lune, le logo, la cigogne imprimée ou le château."""
    boites = [(280, 20, 580, 320), (0, 0, 300, 250), (1980, 110, 2230, 290), (1980, 290, 2540, 760)]
    return any(b[0] - marge < x < b[2] + marge and b[1] - marge < y < b[3] + marge for b in boites)


def construire_etoiles(coll, n=26):
    etoiles = []
    for _ in range(20000):                # nombre d'essais limité : on ne boucle jamais à l'infini
        if len(etoiles) >= n: break
        x, y = random.uniform(260, 2500), random.uniform(25, 330)
        if dans_une_boite(x, y) or any(math.hypot(x - a, y - b) < 120 for a, b, _ in etoiles): continue
        etoiles.append((x, y, random.uniform(22, 44)))
    for i, (x, y, t) in enumerate(etoiles):
        ob = plan(f"Etoile_{i:02d}", "etoile", (x - t / 2, y - t / 2, x + t / 2, y + t / 2), coll, z=0.003)
        f_on = random.randint(26, 80)
        allumer(ob, f_on, random.randint(EXTINCTION, EXTINCTION + 10))
        periode = random.choice((30, 36, 44, 52))
        for ax in (0, 1):                                            # elle scintille
            sinus(ob, 'scale', ax, 0.45, periode, random.uniform(0, periode), f_on + 8, EXTINCTION, 8)
        ob.rotation_euler.z = R(random.uniform(-15, 15))


def construire_neige(coll, n=64):
    """Flocons blancs (on les voit sur la nuit) : chacun descend en boucle (modificateur Cycles)."""
    for i in range(n):
        t = random.uniform(10, 22)
        x = random.uniform(-0.52, 0.52)
        z = random.uniform(0.015, 0.14)
        ob = plan(f"Flocon_{i:02d}", "flocon", (0, 0, t, t), coll, z=z)
        ob.location.x = x
        periode = random.choice((96, 120, 144, 168))                  # 4 à 7 s pour traverser la carte
        depart = random.uniform(0, periode)
        haut, bas = H_CARTE / 2 + 0.04, -H_CARTE / 2 - 0.04
        # une chute = 2 images clés linéaires, répétées par le modificateur Cycles
        cle(ob, 'location', 1, -depart, haut, 'LINEAR')
        fc = cle(ob, 'location', 1, -depart + periode, bas, 'LINEAR')
        fc.modifiers.new('CYCLES')
        cle(ob, 'location', 0, 0, x)
        sinus(ob, 'location', 0, random.uniform(0.006, 0.016), random.choice((48, 60, 72)), random.uniform(0, 60), 0, FIN, 0)
        cle_taille(ob, 0, ETEINT, 'CONSTANT')                          # la neige ne tombe que la nuit
        cle_taille(ob, 30 + i % 20, ETEINT)
        cle_taille(ob, 42 + i % 20, 1.0)
        cle_taille(ob, 300 + i % 16, 1.0)
        cle_taille(ob, 312 + i % 16, ETEINT, 'CONSTANT')
        cle_taille(ob, FIN, ETEINT, 'CONSTANT')


# ================================================================== 6. LA CIGOGNE ET SA LANTERNE
# trajectoire (image, x, y, z) : de droite à gauche, au-dessus de la carte
VOL = [(VOL_DEBUT, 0.64, 0.15, 0.070), (70, 0.33, 0.12, 0.080), (98, 0.13, 0.215, 0.090),
       (124, -0.08, 0.205, 0.090), (150, -0.22, 0.02, 0.080), (172, -0.36, 0.075, 0.080),
       (VOL_FIN, -0.66, 0.13, 0.070)]


def x_cigogne(frame):
    """Position X de la cigogne à une image donnée (interpolation linéaire de VOL)."""
    for (f0, x0, *_), (f1, x1, *_) in zip(VOL, VOL[1:]):
        if f0 <= frame <= f1: return x0 + (x1 - x0) * (frame - f0) / (f1 - f0)
    return VOL[-1][1]


def passage(x_px, delai=6):
    """Image où la cigogne passe au-dessus du pixel x_px (+ un petit délai) : c'est là qu'il s'allume."""
    xw = (x_px - W_PX / 2) * K
    for f in range(VOL_DEBUT, VOL_FIN + 1):
        if x_cigogne(f) <= xw: return f + delai
    return VOL_FIN


def construire_cigogne(coll):
    maison = (2098, 222)                                # pivot du corps (pixels du dessin)
    cig = vide("Cigogne", coll, (VOL[0][1], VOL[0][2], VOL[0][3]), taille=0.04, forme='SPHERE')
    def calque(nom, pivot, z):
        b = INFO[nom]['box']
        ob = plan(nom, nom, b, coll, z=z, pivot_px=pivot, fondu=False)
        ob.parent = cig
        ox, oy = px(*pivot); hx, hy = px(*maison)
        ob.location = (ox - hx, oy - hy, z)
        return ob
    corps = calque('cigogne_corps', maison, 0.0)
    aile_av = calque('cigogne_aile_avant', (2100, 222), 0.0008)
    aile_ar = calque('cigogne_aile_arriere', (2128, 232), -0.0008)
    # la lanterne pend au bec (accroche en haut de l'image, au milieu)
    bec = (2012, 244)
    lw, lh = 240 * 0.36, 300 * 0.36
    lan = plan("Lanterne", "lanterne", (bec[0] - lw / 2, bec[1], bec[0] + lw / 2, bec[1] + lh), coll,
               z=0.001, pivot_px=bec)
    lan.parent = cig
    bx, by = px(*bec); hx, hy = px(*maison)
    lan.location = (bx - hx, by - hy, 0.001)
    cle(lan, 'rotation_euler', 2, 0, 0.0)
    sinus(lan, 'rotation_euler', 2, R(14), 22, 0, VOL_DEBUT, VOL_FIN, 6)   # elle se balance

    # le vol : cachée avant et après (échelle ~0), visible pendant la traversée
    taille = 1.7
    cle_taille(cig, 0, ETEINT, 'CONSTANT')
    cle_taille(cig, VOL_DEBUT, taille, 'CONSTANT')
    cle_taille(cig, VOL_FIN, ETEINT, 'CONSTANT')
    cle_taille(cig, FIN, ETEINT, 'CONSTANT')
    for (f, x, y, z) in VOL:
        for i, v in enumerate((x, y, z)): cle(cig, 'location', i, f, v)
    for i, v in enumerate(VOL[0][1:]): cle(cig, 'location', i, 0, v, 'CONSTANT')
    for i, v in enumerate(VOL[-1][1:]): cle(cig, 'location', i, FIN, v, 'CONSTANT')
    cle(cig, 'rotation_euler', 2, 0, 0.0)
    sinus(cig, 'rotation_euler', 2, R(5), 30, 0, VOL_DEBUT, VOL_FIN, 6)      # elle tangue un peu
    # battements d'ailes (autour de l'axe du corps : elles sortent du plan de la carte)
    for aile, signe in ((aile_av, 1), (aile_ar, -1)):
        cle(aile, 'rotation_euler', 0, 0, 0.0, 'CONSTANT')
        f, haut = VOL_DEBUT, True
        while f <= VOL_FIN:
            cle(aile, 'rotation_euler', 0, f, R(signe * (12 if haut else 95)))
            haut = not haut; f += 6
        cle(aile, 'rotation_euler', 0, FIN, 0.0, 'CONSTANT')
    return cig


# ================================================================== 7. LA VILLE S'ALLUME
def extinction(x_px):
    """Les lumières s'éteignent de gauche à droite, en ~16 images."""
    return EXTINCTION + int(16 * x_px / W_PX)


def construire_neons(coll):
    for nom in ('chiffre_7', 'chiffre_2b', 'chiffre_0', 'chiffre_2a'):
        b = EL['neon_' + nom]
        ob = plan("Neon_" + nom, "neon_" + nom, b, coll, z=0.005)
        f_on = passage((b[0] + b[2]) / 2)
        allumer(ob, f_on, extinction((b[0] + b[2]) / 2), gresille=True)
        for ax in (0, 1):                                              # le néon « respire »
            sinus(ob, 'scale', ax, 0.015, 48, 0, f_on + 14, EXTINCTION, 10)
    b = EL['neon_texte']
    ob = plan("Neon_texte", "neon_texte", b, coll, z=0.005)
    allumer(ob, TEXTE_ON, extinction((b[0] + b[2]) / 2), gresille=True)


def construire_fenetres(coll):
    for i, (x0, y0, x1, y1) in enumerate(EL['fenetres']):
        cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
        # la texture « fenetre » a la vitre sur la moitié centrale : le plan est 2 fois plus grand
        ob = plan(f"Fenetre_{i:02d}", "fenetre", (cx - w, cy - h, cx + w, cy + h), coll, z=0.004)
        allumer(ob, passage(cx, delai=random.randint(4, 18)), extinction(cx))


def construire_guirlandes(coll):
    groupes = {}
    for i, a in enumerate(EL['ampoules']):
        x, y = a['p']
        t = 30 if a['g'] != 'sapins' else 26
        g = groupes.setdefault(a['g'], collection("Guirlande " + a['g'], coll))
        ob = plan(f"Ampoule_{a['g']}_{i:03d}", "ampoule_" + a['c'], (x - t / 2, y - t / 2, x + t / 2, y + t / 2), g, z=0.007)
        f_on = passage(x, delai=4 + i % 3)
        allumer(ob, f_on, extinction(x))
        if a['g'] == 'sapins' or i % 3 == 0:                          # certaines ampoules clignotent
            periode = random.choice((16, 20, 24, 32))
            for ax in (0, 1):
                sinus(ob, 'scale', ax, 0.35, periode, random.uniform(0, periode), f_on + 8, EXTINCTION, 6)


def construire_filantes(coll):
    """Deux étoiles filantes : une traînée qui traverse le haut du ciel (tête à droite de l'image)."""
    for nom, f0, f1, a, b in (("Filante_1", 228, 246, (-0.30, 0.236), (0.06, 0.214)),
                              ("Filante_2", 262, 278, (0.28, 0.238), (0.47, 0.150))):
        ob = plan(nom, "filante", (0, 0, 300, 30), coll, z=0.006, pivot_px=(300, 15))
        ob.rotation_euler.z = math.atan2(b[1] - a[1], b[0] - a[0])
        cle_taille(ob, 0, ETEINT, 'CONSTANT')
        cle_taille(ob, f0, ETEINT); cle_taille(ob, f0 + 4, 1.0)
        cle_taille(ob, f1 - 5, 1.0); cle_taille(ob, f1, ETEINT, 'CONSTANT')
        cle_taille(ob, FIN, ETEINT, 'CONSTANT')
        for i in (0, 1):
            cle(ob, 'location', i, 0, a[i], 'CONSTANT')
            cle(ob, 'location', i, f0, a[i], 'SINE', 'EASE_IN')
            cle(ob, 'location', i, f1, b[i], 'CONSTANT')
            cle(ob, 'location', i, FIN, b[i], 'CONSTANT')


# ================================================================== 8. CARTE DE RÉFÉRENCE + CAMÉRA
def carte_reference(coll):
    me = bpy.data.meshes.new("carte_plan")
    w, h = 1.0, H_CARTE
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
    mat = bpy.data.materials.new("M_carte_imprimee")
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(os.path.abspath(CARTE_PNG), check_existing=True)
    nt.links.new(im.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])
    me.materials.append(mat)
    ob = bpy.data.objects.new("Carte_imprimee", me)
    coll.objects.link(ob)
    ob.location.z = -0.0005
    ob.hide_render = True          # sert de repère dans Blender, n'est pas exportée
    ob.hide_select = True
    return ob


def camera_apercu(coll):
    cam = bpy.data.objects.new("Camera_telephone", bpy.data.cameras.new("Camera_telephone"))
    coll.objects.link(cam)
    cam.location = (0.0, -0.30, 1.05)
    direction = Vector((0.0, 0.0, 0.03)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 30
    bpy.context.scene.camera = cam
    return cam


# ================================================================== 9. TOUT CONSTRUIRE
def construire():
    preparer_scene()
    c_ref = collection("Carte imprimée (repère, non exportée)")
    c_nuit = collection("1 - La nuit tombe")
    c_cig = collection("2 - La cigogne et sa lanterne")
    c_ville = collection("3 - La ville s'allume")
    c_ciel = collection("4 - Le ciel (étoiles filantes)")
    c_nei = collection("5 - La neige")
    c_cam = collection("Caméra (aperçu)")
    carte_reference(c_ref)
    construire_voile(c_nuit)
    construire_lune(c_nuit)
    construire_etoiles(c_nuit)
    construire_cigogne(c_cig)
    construire_neons(c_ville)
    construire_fenetres(collection("Fenêtres", c_ville))
    construire_guirlandes(c_ville)
    construire_filantes(c_ciel)
    construire_neige(c_nei)
    camera_apercu(c_cam)
    c_cam.hide_render = True        # la caméra n'est pas exportée
    bpy.context.scene.frame_set(220)


def exporter_glb(chemin=None):
    """Comme Fichier > Exporter > glTF 2.0, avec les réglages expliqués dans le README."""
    chemin = chemin or os.path.normpath(os.path.join(BLEND_DIR, "..", "assets", "carte.glb"))
    bpy.ops.export_scene.gltf(
        filepath=chemin, export_format='GLB',
        use_renderable=True,                 # seulement ce qui est "rendu" (pas la carte repère)
        export_yup=True,                     # +Y vers le haut (convention glTF / A-Frame)
        export_animations=True,
        export_animation_mode='SCENE',       # toute la timeline = une seule animation
        export_anim_scene_split_object=False,
        export_frame_range=True,
        export_force_sampling=True,          # les sinus, les cycles et les paliers sont "cuits" image par image
        export_cameras=False, export_lights=False,
        export_image_format='AUTO')
    return chemin


if __name__ == "__main__":
    construire()
