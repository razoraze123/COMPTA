# Liste de plusieurs User-Agent pour rotation aléatoire
USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
        "Gecko/20100101 Firefox/117.0"
    ),
]
# Default CSS selector to find product images
IMAGES_DEFAULT_SELECTOR = "img"

COMMON_SELECTORS = [
    "div.woocommerce-product-gallery__image img",
    "figure.woocommerce-product-gallery__wrapper img",
    "img.product-single__photo",
    'img[src*="cdn.shopify.com"]',
    "img.wp-post-image",
]
