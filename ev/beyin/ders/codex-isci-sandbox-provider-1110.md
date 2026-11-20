---
tur: ders
aciklama: codex exec isci: varsayilan sandbox read-only oldu (hicbir sey okuyamaz/yazamaz, 30 sn'de FAIL); ninerouter provider tanimi config'te yok
kaynak: testbench/fix_1110
olusturma: 2026-11-10
guncel: 2026-11-10
yazan: claude
onay: 
etiket: 
---
# codex-isci-sandbox-provider-1110

11-10: codex v0.163 exec varsayilan 'sandbox: read-only' ile acildi; isciler PowerShell 'blocked by policy' deyip 30 sn'de STATUS: FAIL verdi. Cozum: run.sh'de 'codex exec -s danger-full-access'. Flash isci 'Model provider ninerouter not found' verdi: config.toml'da [model_providers.ninerouter] yok. Satir ici: -c model_providers.ninerouter.name="9router" -c model_providers.ninerouter.base_url="http://100.104.78.117:20128/v1" -c model_providers.ninerouter.env_key="NINEROUTER_API_KEY" -c model_providers.ninerouter.wire_api="responses" (chat artik desteklenmiyor). Duzeltilmis ornek: testbench/fix_1110/run.sh. Baslatinca 20 sn sonra codex.log'da 'sandbox:' ve 'provider:' satirina bak.
