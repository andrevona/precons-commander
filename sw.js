var V = "precons-v12";
var ARQ = ["./", "index.html", "manifest.json", "icon.svg", "icon-192.png", "icon-512.png", "icon-180.png", "icons/40k.svg", "icons/afc.svg", "icons/blc.svg", "icons/brc.svg", "icons/c13.svg", "icons/c14.svg", "icons/c15.svg", "icons/c16.svg", "icons/c17.svg", "icons/c18.svg", "icons/c19.svg", "icons/c20.svg", "icons/c21.svg", "icons/clb.svg", "icons/cmd.svg", "icons/cmm.svg", "icons/cmr.svg", "icons/dmc.svg", "icons/drc.svg", "icons/dsc.svg", "icons/eoc.svg", "icons/fic.svg", "icons/khc.svg", "icons/lcc.svg", "icons/ltc.svg", "icons/m3c.svg", "icons/mic.svg", "icons/mkc.svg", "icons/moc.svg", "icons/ncc.svg", "icons/nec.svg", "icons/onc.svg", "icons/otc.svg", "icons/pip.svg", "icons/scd.svg", "icons/star.svg", "icons/tdc.svg", "icons/voc.svg", "icons/who.svg", "icons/woc.svg", "icons/znc.svg"];
self.addEventListener("install", function (e) { e.waitUntil(caches.open(V).then(function (c) { return c.addAll(ARQ); })); self.skipWaiting(); });
self.addEventListener("activate", function (e) { e.waitUntil(caches.keys().then(function (ks) { return Promise.all(ks.filter(function (k) { return k !== V; }).map(function (k) { return caches.delete(k); })); })); self.clients.claim(); });
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  e.respondWith(fetch(e.request).then(function (r) { var cp = r.clone(); caches.open(V).then(function (c) { c.put(e.request, cp); }); return r; }).catch(function () { return caches.match(e.request); }));
});
