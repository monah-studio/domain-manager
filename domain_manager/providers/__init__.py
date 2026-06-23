"""Provider base class — all providers inherit from this."""

from ..core import get_provider_creds


class BaseProvider:
    """Base class for all DNS/domain providers.

    Subclasses must set:
        name          — short id (e.g. 'cloudflare')
        label         — human name (e.g. 'Cloudflare')
        config_fields — list of (field_name, prompt_text, secret_bool)
    """

    name = ""
    label = ""
    config_fields = []  # [(field, prompt, is_secret), ...]

    def __init__(self):
        self._creds = get_provider_creds(self.name)

    @property
    def configured(self):
        return all(f[0] in self._creds and self._creds[f[0]] for f in self.config_fields)

    def creds(self):
        return self._creds

    # ── API methods (override these) ────────────────────────────────────

    def list_domains(self, json_mode=False):
        """List all domains. Return list of dicts or print directly."""
        raise NotImplementedError

    def list_records(self, domain, json_mode=False):
        """List DNS records for a domain."""
        raise NotImplementedError

    def update_record(self, domain, record_type, name, value, ttl=600):
        """Update a DNS record. Return True on success."""
        raise NotImplementedError

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        """Dynamic DNS: detect public IP, update if changed.
        Return True if updated, False if no change needed."""
        raise NotImplementedError
