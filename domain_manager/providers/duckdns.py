"""DuckDNS — free DDNS, token-based. Super simple."""

from ..core import get_public_ip, http_request
from . import BaseProvider


class Provider(BaseProvider):
    name = "duckdns"
    label = "DuckDNS"
    config_fields = [
        ("token", "API Token", True),
    ]

    def list_domains(self, json_mode=False):
        print(self._("duckdns_subdomain", sub="<your-domain>.duckdns.org"))
        print("Domain: <your-domain>.duckdns.org")

    def list_records(self, domain, json_mode=False):
        subdomain = domain.replace(".duckdns.org", "")
        print(self._("duckdns_subdomain", sub=subdomain))
        print(f"Use: domain-manager ddns {domain} --provider duckdns --type A --name @")

    def update_record(self, domain, record_type, name, value, ttl=600):
        subdomain = domain.replace(".duckdns.org", "")
        token = self.creds()["token"]
        url = f"https://www.duckdns.org/update?domains={subdomain}&token={token}&{record_type.lower()}={value}"
        result = http_request("GET", url)
        if result == "OK":
            print(f"✅ {record_type} {subdomain}.duckdns.org → {value}")
            return True
        print(f"Error [{self.label}]: DuckDNS returned: {result}")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        return self.update_record(domain, record_type, name, ip, ttl)
