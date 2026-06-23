# Domain Manager - Tesla API Integration

## Check Tesla battery from your desk

```bash
# 1. Get Tesla Fleet API token (requires developer account)
# https://developers.tesla.com/

# 2. Set up your credentials
export TESLA_API_KEY="your_key"
export TESLA_VIN="your_vin"

# 3. Check battery
curl -s -H "Authorization: Bearer $TESLA_TOKEN" \
  "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles/$TESLA_VIN/data" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['response']; print(f'🔋 {d[\"battery_level\"]}% | Range: {d[\"battery_range\"]} mi')"

# 4. Combine with domain-manager cron to log battery alongside DDNS updates
```

## Combine with domain-manager

Run both DDNS and Tesla check in one cron:

```bash
#!/bin/bash
# ~/.local/bin/ddns-plus.sh
DOMAIN="example.com"
domain-manager ddns $DOMAIN --type A --name home --quiet
BATTERY=$(curl -s -H "Authorization: Bearer $(cat ~/.tesla/token)" \
  "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles/$(cat ~/.tesla/vehicle_id)/data" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('response',{}).get('battery_level','?'))" 2>/dev/null || echo "?")
echo "$(date '+%Y-%m-%d %H:%M') | DDNS: $DOMAIN | 🔋 Tesla: $BATTERY%" >> /tmp/home-status.log
```
