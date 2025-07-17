"""Universal image scraper package."""

import logging


def configure_logging(verbose: bool = False) -> None:
    """Configure root logging level and format."""

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )


configure_logging(False)
