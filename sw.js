const CACHE_NAME = "greening-divide-data-v2";

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
});

self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);

  // Only cache files inside the data folder
  if (!url.pathname.includes("/data/")) {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then(async cache => {
      const cachedResponse = await cache.match(event.request);

      if (cachedResponse) {
        return cachedResponse;
      }

      try {
        const networkResponse = await fetch(event.request);

        if (networkResponse.ok) {
          cache.put(event.request, networkResponse.clone());
        }

        return networkResponse;
      } catch (error) {
        console.error("Data fetch failed:", error);
        throw error;
      }
    })
  );
});
