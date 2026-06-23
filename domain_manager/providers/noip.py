"""No-IP — DDNS service. Username + Password."""

from ..core import get_public_ip, http_request
from . import BaseProvider
import base64


class Provider(BaseProvider):
    name = "noip"
    label = "No-IP"
    config_fields = [
        ("user", "Username", False),
        ("pass", "Password", True),
    ]

    def _update(self, domain, record_type, value):
        c = self.creds()
        auth = base64.b64encode(f"{c['user']}:{c['pass']}".encode()).decode()
        url = f"https://dynupdate.no-ip.com/nic/update?hostname={domain}&{record_type.lower()}={value}"
        result = http_request("GET", url, headers={"Authorization": f"Basic {auth}"})
        if isinstance(result, str):
            if result.startswith("good") or result.startswith("nochg"):
                return True, result
        return False, str(result)

    def list_domains(self, json_mode=False):
        print(self._("noip_dashboard", label=self.label))

    def list_records(self, domain, json_mode=False):
        print(self._("noip_ddns_only", label=self.label))

    def update_record(self, domain, record_type, name, value, ttl=600):
        ok, msg = self._update(domain, record_type, value)
        if ok:
            print(f"✅ {record_type} {domain} → {value}")
            return True
        print(f"Error [{self.label}]: {msg}")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        # No-IP doesn't support read-before-write, always sends
        ok, msg = self._update(domain, record_type, ip)
        if ok:
            if "nochg" in msg and quiet:
                return False
            if "nochg" in msg:
                print(f"✓ {record_type} {domain} already {ip}")
                return False
            print(f"✅ {record_type} {domain} → {ip}")
            return True
        print(f"Error [{self.label}]: {msg}")
        return False
