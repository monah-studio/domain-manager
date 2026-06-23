# Contributing to Domain Manager

We love contributions! Here's how to get involved.

## 🐛 Reporting Bugs

1. Search [existing issues](https://github.com/Monah-Limited/domain-manager/issues) first
2. Include your OS, Python version, and provider
3. Run with `--json` and paste the output
4. Redact any API keys before sharing

## 💡 Feature Requests

- New registrar? Open an issue with the API docs link
- New DNS feature? Describe the use case

## 🔧 Pull Requests

### Adding a new registrar

1. Study `domain_manager.py` — each provider has 3 functions:
   - `{provider}_list_domains(json_mode)`
   - `{provider}_list_records(domain, json_mode)`
   - `{provider}_update_record(domain, type, name, value, ttl)`
2. Add your functions following the same pattern
3. Register them in `cmd_list()`, `cmd_dns()`, `cmd_ddns()`
4. Update CLI args in `main()` with your provider name
5. Test with a real domain

### Code style

- Pure Python 3 stdlib — no external dependencies
- Max 100 chars per line
- Functions under 60 lines
- Error returns as `{"error": "..."}` dicts

### PR checklist

- [ ] Tested with a real domain (at least dry-run)
- [ ] Updated `--help` text if adding new flags
- [ ] Added yourself to `CONTRIBUTORS.md` (optional)

## 🧪 Testing

```bash
# Unit tests (if you add them)
python3 -m pytest tests/

# Manual test
domain-manager list --all
domain-manager dns list example.com
```

## 📜 License

By contributing, you agree your contributions will be licensed under MIT.
