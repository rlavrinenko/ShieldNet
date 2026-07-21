# ShieldNet Backend v0.3

Додано Discord OAuth2, реєстрацію Discord-серверів, автоматичне призначення власника серверу як Admin та внутрішній API для Bot Worker.

## Оновлення

```bash
unzip shieldnet-backend-v0.3.zip
cd shieldnet-backend-v0.3
chmod +x scripts/*.sh
sudo ./scripts/install.sh
sudo ./scripts/upgrade_db.sh
sudo ./scripts/check.sh
```

Потім заповни `/etc/shieldnet/backend/discord.env` і перезапусти backend.
