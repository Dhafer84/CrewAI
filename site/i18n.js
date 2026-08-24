/* Résolution des clés de traduction côté navigateur.
 *
 * ⚠️ Ce fichier ne charge RIEN lui-même : le catalogue est servi par
 * `/i18n/<langue>.js`, inclus par un <script src> classique **avant** le
 * script de la page. Un script sans `defer` bloque l'analyse du document :
 * `window.I18N` est donc garanti présent quand la page s'exécute.
 *
 * L'alternative — un `fetch()` au chargement — laisserait une fenêtre
 * pendant laquelle un clic rapide afficherait une clé brute au visiteur.
 * Sur un site vitrine, c'est exactement ce qu'on ne veut pas.
 *
 * Le comportement reproduit celui de `src/i18n/t()` : repli sur le
 * français, puis sur la clé, et **jamais d'exception**.
 */
(function () {
  'use strict';

  function pluralSuffix(lang, n) {
    // ⚠️ Zéro est un singulier en français, un pluriel en anglais.
    if (lang === 'fr') { return Math.abs(n) < 2 ? '.one' : '.other'; }
    return n === 1 ? '.one' : '.other';
  }

  // La langue de la page, telle que servie par le catalogue. Les pages s'en
  // servent pour demander leurs contrats JSON dans la bonne langue.
  window.LANG = (window.I18N || {})['@lang'] || 'fr';

  window.T = function (key, params) {
    var cat = window.I18N || {};
    var lang = cat['@lang'] || 'fr';
    var text;

    if (params && typeof params.n === 'number') {
      text = cat[key + pluralSuffix(lang, params.n)];
    }
    if (text === undefined) { text = cat[key]; }
    if (text === undefined) { return key; }

    if (!params) { return text; }
    return text.replace(/\{(\w+)\}/g, function (marque, nom) {
      return Object.prototype.hasOwnProperty.call(params, nom) ? params[nom] : marque;
    });
  };
}());
