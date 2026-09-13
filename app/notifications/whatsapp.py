class WhatsAppProvider:
    """Feature-flagged boundary; delivery is intentionally disabled in this MVP."""

    async def send(self, message):
        raise NotImplementedError("WhatsApp delivery is disabled")
