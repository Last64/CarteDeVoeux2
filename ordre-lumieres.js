// Composant A-Frame « ordre-lumieres »
//
// Presque tous les éléments de la nuit sont des images transparentes posées presque à plat sur la carte.
// three.js trie les objets transparents d'après leur distance à la caméra : selon l'angle du téléphone,
// le voile de nuit pourrait être dessiné APRÈS une fenêtre et l'assombrir.
// On impose donc l'ordre : d'abord le voile, puis le ciel (lune, étoiles), puis les lumières de la ville,
// puis la cigogne et la neige, qui sont devant tout le reste.
AFRAME.registerComponent('ordre-lumieres', {
  init() {
    this.el.addEventListener('model-loaded', () => {
      const ordre = (nom) => {
        if (nom.startsWith('Voile')) return 1;
        if (nom.startsWith('Lune') || nom.startsWith('Etoile') || nom.startsWith('Filante')) return 2;
        if (nom.startsWith('Fenetre')) return 3;
        if (nom.startsWith('Neon')) return 4;
        if (nom.startsWith('Ampoule')) return 5;
        if (nom.startsWith('cigogne') || nom.startsWith('Lanterne')) return 6;
        if (nom.startsWith('Flocon')) return 7;
        return 3;
      };
      this.el.getObject3D('mesh').traverse((o) => {
        if (!o.isMesh) return;
        o.renderOrder = ordre(o.name);
        const m = o.material;
        if (m && m.transparent) m.depthWrite = false;   // une lueur ne doit pas « découper » celle de derrière
        o.frustumCulled = false;                       // les éléments éteints (échelle ~0) restent gérés
      });
    });
  }
});
