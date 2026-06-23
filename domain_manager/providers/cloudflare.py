"""Cloudflare — API Token (recommended) or Global Key"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.cloudflare.com/client/v4"


class Provider(BaseProvider):
    name = "cloudflare"
    label = "Cloudflare"
    config_fields = [
        ("token", "API Token (recommended) or Global Key", True),
        ("email", "Account Email (only needed with Global Key)", False),
    ]

    def _headers(self):
        c = self.creds()
        h = {"Authorization": f"Bearer {c['token']}"}
        if c.get("email"):
            h["X-Auth-Email"] = c["email"]
            h["X-Auth-Key"] = c["token"]
            del h["Authorization"]
        return h

    def _paginate(self, path):
        results, page, total_pages = [], 1, 1
        while page <= total_pages:
            data = http_request("GET", f"{API}{path}?page={page}&per_page=100",
                               headers=self._headers())
            if isinstance(data, dict) and data.get("success") and data.get("result"):
                results.extend(data["result"])
                info = data.get("result_info", {})
                total_pages = info.get("total_pages", 1)
            else:
                err = data.get("errors", [{}])[0].get("message", str(data)) if isinstance(data, dict) else str(data)
                return {"error": err}
            page += 1
        return results

    def _zone_id(self, domain):
        zones = self._paginate(f"/zones?name={domain}")
        if isinstance(zones, dict) and "error" in zones:
            return None
        if zones:
            return zones[0]["id"]
        # Try partial match
        zones = self._paginate("/zones")
        if isinstance(zones, list):
            for z in zones:
                if domain.endswith(z["name"]):
                    return z["id"]
        return None

    def list_domains(self, json_mode=False):
        zones = self._paginate("/zones")
        if isinstance(zones, dict) and "error" in zones:
            print(f"Error [{self.label}]: {zones['error']}")
            return
        print_table(
            [(z["name"], z["status"], z.get("plan",{}).get("name","")) for z in zones],
            ["Domain", "Status", "Plan"], json_mode
        )

    def list_records(self, domain, json_mode=False):
        zid = self._zone_id(domain)
        if not zid:
            print(f"Error [{self.label}]: Domain '{domain}' not found")
            return
        records = self._paginate(f"/zones/{zid}/dns_records")
        if isinstance(records, dict) and "error" in records:
            print(f"Error [{self.label}]: {records['error']}")
            return
        print_table(
            [(r["type"], r["name"], r["content"], str(r.get("ttl",1))) for r in records],
            ["Type", "Name", "Value", "TTL"], json_mode
        )

    def update_record(self, domain, record_type, name, value, ttl=600):
        zid = self._zone_id(domain)
        if not zid:
            print(f"Error [{self.label}]: Domain '{domain}' not found")
            return False
        ttl_val = 1 if ttl == 1 else ttl  # 1 = auto
        records = self._paginate(f"/zones/{zid}/dns_records")
        if isinstance(records, list):
            for r in records:
                if r["type"] == record_type and r["name"].rstrip(".") == f"{name}.{domain}".rstrip("."):
                    rid = r["id"]
                    result = http_request("PUT",
                        f"{API}/zones/{zid}/dns_records/{rid}",
                        headers=self._headers(),
                        data={"type": record_type, "name": name, "content": value, "ttl": ttl_val})
                    if isinstance(result, dict) and result.get("success"):
                        print(f"✅ {record_type} {name}.{domain} → {value}")
                        return True
                    print(f"Error [{self.label}]: {result}")
                    return False
        # Create new record
        result = http_request("POST", f"{API}/zones/{zid}/dns_records",
            headers=self._headers(),
            data={"type": record_type, "name": name, "content": value, "ttl": ttl_val})
        if isinstance(result, dict) and result.get("success"):
            print(f"✅ {record_type} {name}.{domain} → {value} (created)")
            return True
        print(f"Error [{self.label}]: {result}")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        zid = self._zone_id(domain)
        if not zid:
            print(f"Error [{self.label}]: Domain '{domain}' not found")
            return False
        records = self._paginate(f"/zones/{zid}/dns_records")
        if isinstance(records, list):
            fqdn = f"{name}.{domain}".rstrip(".")
            for r in records:
                if r["type"] == record_type and r["name"].rstrip(".") == fqdn:
                    if r["content"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
