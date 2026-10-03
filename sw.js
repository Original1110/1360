const CACHE_NAME = "original-ps5-cache-v1";

const FILES_TO_CACHE = [

    "./",
    "./index.html",

    "./icon0.png",
    "./mmhmm-cats-ps5.gif",

    "./src/firmware.js",
    "./src/main.js",
    "./src/rop.js",
    "./src/utils/syscalls.js",
    "./src/site.js"

];


self.addEventListener(
    "install",
    event => {

        event.waitUntil(

            caches
                .open(CACHE_NAME)
                .then(cache => {

                    console.log(
                        "Opening cache:",
                        CACHE_NAME
                    );

                    return cache.addAll(
                        FILES_TO_CACHE
                    );

                })
                .then(() => {

                    console.log(
                        "All files cached."
                    );

                    return self.skipWaiting();

                })

        );

    }
);


self.addEventListener(
    "activate",
    event => {

        event.waitUntil(

            caches.keys()
                .then(cacheNames => {

                    return Promise.all(

                        cacheNames
                            .filter(
                                name =>
                                    name !==
                                    CACHE_NAME
                            )
                            .map(
                                name =>
                                    caches.delete(name)
                            )

                    );

                })
                .then(() =>
                    self.clients.claim()
                )

        );

    }
);


self.addEventListener(
    "fetch",
    event => {

        if (
            event.request.method !==
            "GET"
        ) {
            return;
        }


        event.respondWith(

            caches.match(
                event.request
            )
            .then(cachedResponse => {

                if (cachedResponse) {

                    return cachedResponse;

                }


                return fetch(
                    event.request
                )
                .then(response => {

                    if (
                        !response ||
                        response.status !== 200 ||
                        response.type === "opaque"
                    ) {

                        return response;

                    }


                    const responseClone =
                        response.clone();


                    caches.open(
                        CACHE_NAME
                    )
                    .then(cache => {

                        cache.put(
                            event.request,
                            responseClone
                        );

                    });


                    return response;

                });

            })

        );

    }
);
