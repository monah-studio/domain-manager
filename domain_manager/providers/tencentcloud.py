"""腾讯云 DNS — SecretId + SecretKey"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider
import hashlib
import hmac
import json
import time

API = "https://dnspod.tencentcloudapi.com"


class Provider(BaseProvider):
    name = "tencentcloud"
    label = "腾讯云 DNS"
    config_fields = [
        ("secret_id", "SecretId", False),
        ("secret_key", "SecretKey", True),
    ]

    def _post(self, action, params=None):
        c = self.creds()
        ts = str(int(time.time()))
        payload = params or {}
        body = json.dumps(payload)
        msg = f"POST{API}/?Action={action}&Timestamp={ts}&Nonce=1&SecretId={c['secret_id']}&SignatureMethod=HmacSHA256&SignatureVersion=2&Version=2021-03-23"
        msg += body
        sig = hmac.new(c["secret_key"].encode(), msg.encode(), hashlib.sha256).digest().hex()
        headers = {
            "Content-Type": "application/json",
            "X-TC-Action": action,
            "X-TC-Timestamp": ts,
            "X-TC-Version": "2021-03-23",
            "Authorization": f"TC3-HMAC-SHA256 Credential={c['secret_id']}/SignedHeaders=content-type;host;x-tc-action/TC3-HMAC-SHA256 SignedHeaders=content-type;host;x-tc-action Signature={sig}",
        }
        url = f"{API}/?Action={action}"
        return http_request("POST", url, headers=headers, data=payload)

    def list_domains(self, json_mode=False):
        data = self._post("DescribeDomainList", {"Limit": 100})
        if isinstance(data, dict) and data.get("Response", {}).get("DomainList"):
            doms = [(d["Name"], d.get("CreatedOn","")) for d in data["Response"]["DomainList"]]
            print_table(doms, ["Domain", "Created"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = self._post("DescribeRecordList", {"Domain": domain, "Limit": 100})
        if isinstance(data, dict) and data.get("Response", {}).get("RecordList"):
            rows = [(r["Type"], r["Name"], r["Value"], str(r.get("TTL",0))) for r in data["Response"]["RecordList"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = self._post("DescribeRecordList", {"Domain": domain})
        rid = None
        if isinstance(data, dict) and data.get("Response", {}).get("RecordList"):
            for r in data["Response"]["RecordList"]:
                if r["Type"] == record_type and r["Name"] == name:
                    rid = r["RecordId"]
                    break
        if rid:
            self._post("ModifyRecord", {"Domain": domain, "RecordId": rid, "RecordType": record_type, "RecordLine": "默认", "Value": value, "SubDomain": name, "TTL": ttl})
        else:
            self._post("CreateRecord", {"Domain": domain, "RecordType": record_type, "RecordLine": "默认", "Value": value, "SubDomain": name, "TTL": ttl})
        print(f"✅ {record_type} {name}.{domain} → {value}")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        data = self._post("DescribeRecordList", {"Domain": domain})
        if isinstance(data, dict) and data.get("Response", {}).get("RecordList"):
            for r in data["Response"]["RecordList"]:
                if r["Type"] == record_type and r["Name"] == name:
                    if r["Value"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
