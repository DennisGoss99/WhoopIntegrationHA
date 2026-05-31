"""OAuth2 config flow for Whoop."""
from __future__ import annotations

import logging

from homeassistant.helpers.config_entry_oauth2_flow import AbstractOAuth2FlowHandler

from .const import DOMAIN, SCOPES


class WhoopFlowHandler(AbstractOAuth2FlowHandler, domain=DOMAIN):
    """OAuth2 flow for Whoop."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict:
        return {"scope": " ".join(SCOPES)}
