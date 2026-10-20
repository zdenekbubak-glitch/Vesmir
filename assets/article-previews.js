/* Built from the same persisted assignments and exact slugs as the SEO pages. */
(function () {
  'use strict';
  let entries = {};
  window.ArticlePreviews = {
    ready: fetch('/data/article_image_previews.json').then(function (response) {
      if (!response.ok) throw new Error('Preview manifest: ' + response.status);
      return response.json();
    }).then(function (data) { entries = data; }).catch(function (error) {
      console.warn('Náhledy nejsou dostupné:', error.message);
    }),
    get: function (item) {
      return entries[String(item.id || item.url || item.title || '')] || { href: item.url || '#', html: '' };
    }
  };
}());
