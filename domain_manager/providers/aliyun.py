"""阿里云 DNS — AccessKey ID + AccessKey Secret"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider
import hashlib
import hmac
import base64
import urllib.parse
import time
import random

API = "https://dns.aliyuncs.com"


class Provider(BaseProvider):
    name = "aliyun"
    label = "阿里云 DNS"
    config_fields = [
        ("access_key", "AccessKey ID", False),
        ("access_secret", "AccessKey Secret", True),
    ]

    def _sign(self, params):
        c = self.creds()
        params["AccessKeyId"] = c["access_key"]
        params["Format"] = "JSON"
        params["Version"] = "2015-01-09"
        params["SignatureMethod"] = "HMAC-SHA1"
        params["Timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        params["SignatureVersion"] = "1.0"
        params["SignatureNonce"] = str(random.randint(1, 10**15))
        sorted_keys = sorted(params.keys())
        can_str = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(params[k]), safe='')}" for k in sorted_keys)
        str_to_sign = f"GET&%2F&{urllib.parse.quote(can_str, safe='')}"
        sig = base64.b64encode(hmac.new(f"{c['access_secret']}&".encode(), str_to_sign.encode(), hashlib.sha1).digest()).decode()
        params["Signature"] = sig
        return params

    def _get(self, params):
        signed = self._sign(params)
        qs = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(signed[k]), safe='')}" for k in sorted(signed.keys()))
        return http_request("GET", f"{API}/?{qs}")

    def list_domains(self, json_mode=False):
        data = self._get({"Action": "DescribeDomains", "PageSize": 100})
        if isinstance(data, dict) and data.get("Domains", {}).get("Domain"):
            doms = [(d["DomainName"], d.get("RegistrationDate","")) for d in data["Domains"]["Domain"]]
            print_table(doms, ["Domain", "Registered"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = self._get({"Action": "DescribeDomainRecords", "DomainName": domain, "PageSize": 500})
        if isinstance(data, dict) and data.get("DomainRecords", {}).get("Record"):
            rows = [(r["Type"], r["RR"], r["Value"], str(r.get("TTL",0))) for r in data["DomainRecords"]["Record"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = self._get({"Action": "DescribeDomainRecords", "DomainName": domain})
        rid = None
        if isinstance(data, dict) and data.get("DomainRecords", {}).get("Record"):
            for r in data["DomainRecords"]["Record"]:
                if r["Type"] == record_type and r["RR"] == name:
                    rid = r["RecordId"]
                    break
        if rid:
            self._get({"Action": "UpdateDomainRecord", "RecordId": rid, "RR": name, "Type": record_type, "Value": value, "TTL": str(ttl)})
        else:
            self._get({"Action": "AddDomainRecord", "DomainName": domain, "RR": name, "Type": record_type, "Value": value, "TTL": str(ttl)})
        print(f"✅ {record_type} {name}.{domain} → {value}")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        data = self._get({"Action": "DescribeDomainRecords", "DomainName": domain})
        if isinstance(data, dict) and data.get("DomainRecords", {}).get("Record"):
            for r in data["DomainRecords"]["Record"]:
                if r["Type"] == record_type and r["RR"] == name:
                    if r["Value"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
