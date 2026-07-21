# ShieldNet Admin Frontend v0.1

Angular SPA для адміністраторів ShieldNet.

## Функції

- вхід через Discord OAuth;
- callback через popup + `postMessage`;
- збереження access/refresh token у `sessionStorage`;
- список доступних Discord-серверів;
- dashboard сервера;
- адаптивний sidebar;
- темна тема;
- базова структура для майбутніх модулів.

## Встановлення

```bash
unzip shieldnet-admin-frontend-v0.1.zip
cd shieldnet-admin-frontend-v0.1
chmod +x scripts/*.sh
sudo ./scripts/install.sh
```

Потім застосуй Backend OAuth callback patch:

```bash
sudo ./scripts/install_backend_patch.sh
```

Перевір:

```bash
sudo ./scripts/check.sh
```

Відкрий:

```text
https://shieldnet.discord.lrm-it.com
```

## Важливо

У Discord Developer Portal Redirect URI має бути:

```text
https://shieldnet.discord.lrm-it.com/api/v1/auth/discord/callback
```
