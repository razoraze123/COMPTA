USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0 Safari/537.36"
)
# Default CSS selector to find product images
IMAGES_DEFAULT_SELECTOR = "img"

COMMON_SELECTORS = [
    "div.woocommerce-product-gallery__image img",
    "figure.woocommerce-product-gallery__wrapper img",
    "img.product-single__photo",
    'img[src*="cdn.shopify.com"]',
    "img.wp-post-image",
]
