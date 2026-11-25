// Composant A-Frame « nuit-boucle » : joue l'animation exportée de Blender (carte.glb)
//
// - La première fois, l'animation se joue depuis le début : la nuit tombe, la cigogne allume la ville.
// - Ensuite la ville RESTE allumée : arrivée à la fin, l'animation repart de l'image 228 (et pas de 0).
//   De 228 à 348, tout ce qui bouge (scintillement, neige, néons, étoiles filantes) a une période
//   qui divise 120 images : on ne voit pas le raccord.
// - Si on perd la carte, l'animation se met en pause. Quand on la retrouve, elle reprend où elle en était.
AFRAME.registerComponent('nuit-boucle', {
  schema: {
    boucle: { type: 'number', default: 228 / 24 }   // début de la boucle, en secondes (image 228 à 24 i/s)
  },

  init() {
    this.temps = 0;
    this.actif = true;

    // Avec MindAR : on ne joue que quand la carte est vue
    const cible = this.el.closest('[mindar-image-target]');
    if (cible) {
      this.actif = false;
      cible.addEventListener('targetFound', () => { this.actif = true; });
      cible.addEventListener('targetLost', () => { this.actif = false; });
    }

    this.el.addEventListener('model-loaded', () => {
      const modele = this.el.getObject3D('mesh');
      const clip = modele.animations && modele.animations[0];
      if (!clip) return;
      this.duree = clip.duration;
      this.mixer = new THREE.AnimationMixer(modele);
      this.mixer.clipAction(clip).play();
      this.mixer.setTime(0);
    });
  },

  tick(t, dt) {
    if (!this.mixer || !this.actif || !dt) return;
    this.temps += Math.min(dt, 100) / 1000;          // (max 0,1 s d'un coup, si l'onglet a été en pause)
    if (this.temps >= this.duree) {
      this.temps = this.data.boucle + (this.temps - this.duree);
    }
    this.mixer.setTime(this.temps);
  }
});
