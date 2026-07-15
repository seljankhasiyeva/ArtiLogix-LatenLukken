# AstroLogix — Data Meanings V3 (Azərbaycan Sintetik Datası)

Bu sənəd `astrologix_data_generator_v3.ipynb`-in yaratdığı **13 dataset**-in tam izahını verir.

**V3 yeniliyi:** Bu versiya **iki müstəqil AI auditinin** tövsiyələri əsasında V2-də müəyyən edilmiş **9 zəif nöqtəni** düzəldir. `weather.csv` və `holidays.csv` bu versiyada **generasiya olunmur** (yalnız `holidays.csv` daxili hesablamalar üçün oxunur, çıxış faylı kimi yazılmır).

**Tarix aralığı:** 2020-01-01 → 2026-06-13
**Regionlar (10):** Absheron, Yevlakh, Ganja, Khachmaz, Lankaran, Sheki, Qazakh, Nakhchivan, Khankendi, Kalbajar
**Mid-mile hub-lar (5):** Absheron, Ganja, Yevlakh, Lankaran, Khachmaz

---

## ✅ Düzəldilən 9 Problem — Tam Xülasə

| # | Problem (V2-də) | Həll (V3-də) | Mənbə |
|---|---|---|---|
| 1 | Tək `azn_per_km` dəyişəni | **Baza Reys Qiyməti (Base Route Price)** lüğəti — marşrut çətinliyinə görə, `pricing_confidence='market_estimate'` şəffaflıq sütunu | AI audit #1 tövsiyəsi |
| 2 | `azn_per_km × random(180,280)` | `fixed_fee + variable_cost × distance` (sürücü/amortizasiya/sığorta sabit, məsafə dəyişkən) | AI audit #1 və #2 |
| 3 | Sabit 15-16% gecikmə | **Ssenari + marşrut çətinliyi + hava** əsaslı: optimistic 5% → normal 10-12% → pessimistic 32% | AI audit #1 və #2 |
| 4 | 82-99% utilization (aşağı hədd əsassız) | **85-95%** sənaye standartı minimum tələbi (TruckX/PCS Software mənbəli) | AI audit #2 + web axtarış |
| 5 | Subyektiv REGION_PROBS | **DSK rəsmi əhali + iqtisadi fəaliyyət** hibrid modeli (`0.35×pop + 0.65×econ`) | İstifadəçinin DSK cədvəli + AI audit #1,#2 |
| 6 | GPS düz xətt (dəniz/dağ üstündən "uçan" TIR) | **Waypoint-based** routing — magistral istiqamətləri üzrə ara nöqtələr | AI audit #1 və #2 |
| 7 | Order↔Shipment əlaqəsi yox | **Tam referensial bütövlük** — bin-packing alqoritmi, FK keys | AI audit #1 və #2 (ən kritik) |
| 8 | Tək `winter_multiplier=1.2` hamıya | **sector_type (B2C/B2B)** ayrı multiplikator | AI audit #1 və #2 |
| 9 | Sabit 8% uğursuz cəhd | **Diapazon əsaslı** (`uniform(0.02, 0.06)`) | AI audit #2 |

---

## 🔑 Ən Kritik Dəyişiklik: Order → Shipment Axını (FIX #7)

V2-də `orders.csv` və `tir_shipments.csv` **tam müstəqil** generasiya olunurdu. V3-də düzgün axın:

```
1. orders.csv yaradılır (hər sifarişin çəkisi + mənşə/məqsəd regionu)
2. Sifarişlər tarix + origin + dest üzrə qruplaşdırılır (groupby)
3. Hər qrup daxilində bin-packing: çəkiyə görə sıralanıb TIR tutumuna
   (capacity_kg × 0.99) qədər ardıcıl doldurulur
4. Hər bin → bir shipment_id, daxilindəki order_id-lər
   associated_order_ids sütununda saxlanır (pipe-ayrılmış)
5. orders.csv-yə shipment_id FK sütunu geri yazılır
   (bağlanmayanlar = 'UNASSIGNED', hələ anbarda gözləyən sifarişləri əks etdirir)
```

**Doğrulama nəticəsi:** `orders.csv`-dəki bağlı sifarişlər (`shipment_id != 'UNASSIGNED'`) və `tir_shipments.csv`-dəki `associated_order_ids`-də olan bütün ID-lər **tam üst-üstə düşür** (24,732 sifariş, 100% uyğunluq).

---

## 📍 Real Məsafə Cədvəli (distances.docx)

İstifadəçi təsdiqlədi: bu məsafələr **real TIR yolu məsafələridir**, haversine deyil. 90 marşrut (Truck/Van ayrı-ayrı).

---

## 💰 FIX #1 — Baza Reys Qiyməti (Base Route Price)

Marşrut çətinliyinə (düzən/dağlıq) və məsafəyə görə hesablanan baza qiymət lüğəti:

```python
base_rate_per_km = 1.40 (düzən) / 1.75 (dağlıq)
# qısa marşrutlarda sabit xərc payı yüksək olduğu üçün multiplikator artır:
dist < 200km  → ×1.35
dist < 300km  → ×1.20
dist < 400km  → ×1.06
```

**Kalibrasiya yoxlaması (AI audit #1 nümunəsi ilə):**
| Marşrut | Məsafə | Hədəf (audit) | Generasiya olunan |
|---|---|---|---|
| Absheron-Ganja | 363km | ~550 AZN | 538.69 AZN ✓ |
| Absheron-Lankaran | 265km | ~450 AZN | 445.20 AZN ✓ |

> ⚠️ **Şəffaflıq:** `pricing_confidence='market_estimate'` sütunu bu qiymətlərin rəsmi dövlət tarifi olmadığını, bazar müşahidəsi əsaslı təxmin olduğunu açıq göstərir.

---

## 💰 FIX #2 — Gündəlik İcarə Formulu

```python
daily_rental_cost_azn = fixed_fee + (avg_distance_km × variable_cost)
```

| Maşın | Fixed (AZN) | Variable (AZN/km) |
|---|---|---|
| Ford Transit 2t | 40 | 0.30 |
| Gazelle 3t | 50 | 0.38 |
| Isuzu NPR 5t | 70 | 0.50 |
| Mercedes Atego 10t | 110 | 0.70 |
| TIR 20t | 150 | 0.95 |

Sabit xərclər (sürücü, amortizasiya, sığorta) məsafədən asılı olmayaraq modelə daxil edilib.

---

## ⏱️ FIX #3 — Ssenari Əsaslı Gecikmə Ehtimalı

```python
get_delay_probability(date, difficulty, weather_bad):
    flat + yay + yaxşı hava       → 5%   (optimistic)
    flat + qış/pis hava           → 12%  (normal)
    mountainous + yay + yaxşı hava → 10%  (normal)
    mountainous + qış/pis hava    → 32%  (pessimistic)
```

`route_difficulty` sütunu (`flat`/`mountainous`) hər `tir_shipments.csv` sətrində saxlanılır ki, modelin bu əlaqəni öyrənə bilsin.

---

## 📦 FIX #4 — Utilization (85-95% sənaye standartı)

Veb axtarışı nəticəsi: sənaye standartı (TruckX, PCS Software) fleet capacity utilization üçün **85-95%** "good/peak efficiency" aralığı kimi qəbul edir. V3-də bu minimum tələb kimi tətbiq olunur:

```python
utilization = max(bin_packing_nəticəsi, np.random.uniform(0.85, 0.95))
```

**Real nəticə:** Orta utilization ~90.1%

---

## 🗺️ FIX #5 — REGION_PROBS (DSK Hibrid Modeli)

İstifadəçinin təqdim etdiyi **rəsmi DSK əhali cədvəli** + iqtisadi fəaliyyət payı:

```python
region_weight = 0.35 × population_share + 0.65 × economic_activity_share
```

| Region | DSK Əhali | Pop Share | Econ Share | Final Weight |
|---|---|---|---|---|
| Absheron | 482,500 | 22.5% | 55% | **43.1%** |
| Ganja | 330,735 | 15.4% | 12% | **13.0%** |
| Lankaran | 224,800 | 10.5% | 8% | **8.8%** |
| Nakhchivan | 472,444 | 22.1% | 1.5% | **8.6%** |
| Yevlakh | 135,400 | 6.3% | 8% | **7.3%** |
| Khachmaz | 176,200 | 8.2% | 6% | **6.7%** |
| Sheki | 182,900 | 8.5% | 5% | **6.2%** |
| Qazakh | 95,100 | 4.4% | 4% | **4.1%** |
| Khankendi | 24,000 | 1.1% | 1.25% | **1.2%** |
| Kalbajar | 17,000 | 0.8% | 1.25% | **1.1%** |

İqtisadi fəaliyyətə daha çox çəki verilib (0.65), çünki Naxçıvan kimi yüksək əhalili amma iqtisadi təcrid olunmuş regionların logistika fəaliyyəti əhali sayı ilə korrelyasiya etmir.

---

## 🛣️ FIX #6 — GPS Waypoint Routing

23 əsas region cütü üçün **real coğrafi waypoint** koordinatları təyin edilib (magistral yol istiqamətlərinə uyğun). Marşrut indi `origin → waypoint1 → waypoint2 → dest` formatında piecewise-linear çəkilir, düz xətt (haversine) əvəzinə.

**Nümunə:** Absheron→Ganja marşrutu indi Şamaxı-Yevlakh istiqamətindən keçir, Xəzər dənizi üstündən "uçmur".

---

## ❄️ FIX #8 — Mövsüm Effekti (sector_type)

```python
demand_multiplier_for_date(date, sector_type='B2C' və ya 'B2B')

B2C (e-ticarət, orders.csv): qış aylarında ×1.25 (Yeni il, bayram alış-verişi)
B2B (TIR, transfer_center.csv, spot_pricing.csv): qış aylarında ×0.88 (tikinti/sənaye azalması)
```

Bu, V2-dəki tək `winter_multiplier=1.2`-ni əvəz edir — fərqli sektorlar fərqli istiqamətdə hərəkət edir.

---

## 🚚 FIX #9 — Last-Mile Diapazon Əsaslı Göstəricilər

| Göstərici | V2 (sabit) | V3 (diapazon) |
|---|---|---|
| Uğursuz çatdırılma faizi | 8% sabit | `uniform(0.02, 0.06)` |
| Bakı daxili gündəlik ünvan | sabit gamma | `uniform(40, 60)` |
| Region gündəlik ünvan | sabit gamma | `uniform(20, 30)` |

---

## 1. stores.csv — 150 sətir

| Sütun | Tip | Məna |
|---|---|---|
| `store_id` | string | Unikal mağaza kodu |
| `store_name` | string | Platforma + nömrə |
| `latitude` / `longitude` | float | Koordinat |
| `region` | string | DSK hibrid modelinə görə seçilmiş region |

---

## 2. vehicles.csv — 60 sətir

| Sütun | Tip | Məna |
|---|---|---|
| `vehicle_id` | string | Unikal NV kodu |
| `vehicle_type` | string | Ford_Transit_2t / Gazelle_3t / Isuzu_NPR_5t / Mercedes_Atego_10t / TIR_20t |
| `capacity_ton` | float | Maksimum yük tutumu |
| `daily_rental_cost_azn` | float | **FIX #2:** fixed+variable formulu ilə |
| `fuel_per_100km` | float | Yanacaq sərfiyyatı |

---

## 3. warehouse.csv — 15 sətir

| Sütun | Tip | Məna |
|---|---|---|
| `warehouse_id` | string | Unikal anbar kodu |
| `region` | string | Yerləşdiyi region (8/15 Absheron-da) |
| `capacity` / `current_load` | float | Tutum / doluluq |
| `inbound_orders` / `outbound_orders` | int | Gündəlik gələn/gedən |

---

## 4. couriers.csv — 200 sətir

| Sütun | Tip | Məna |
|---|---|---|
| `courier_id` | string | Unikal kuriyer kodu |
| `courier_type` | string | pickup / last_mile / hybrid |
| `vehicle_type` | string | moped (70%) / velosiped (20%) / avtomobil (10%) |
| `completed_orders` | int | **FIX #9:** Bakı 40-60, region 20-30 diapazonu |

---

## 5. routes_history.csv — 2000 sətir

| Sütun | Tip | Məna |
|---|---|---|
| `route_id` | string | Unikal marşrut kodu |
| `distance_km` / `duration_minutes` | float | **Real cədvəldən** (±3%/±15% variasiya) |
| `fuel_used` | float | Yanacaq sərfi |

---

## 6. tir_shipments.csv — 8000 sətir ⭐ (FIX #7 məhsulu)

| Sütun | Tip | Məna |
|---|---|---|
| `shipment_id` | string | Unikal sefer kodu |
| `origin_hub` / `destination_hub` | string | Hub kodları |
| `departure_date` / `departure_time` | date/time | Yola çıxış |
| `actual_load_ton` / `capacity_ton` / `utilization_rate` | float | **FIX #4:** 85-95%+ |
| `is_delayed` / `delay_minutes` | 0/1, float | **FIX #3:** ssenari əsaslı |
| `route_difficulty` | string | **YENİ:** flat / mountainous |
| `associated_order_ids` | string | **YENİ (FIX #7):** pipe-ayrılmış order_id siyahısı |
| `pricing_confidence` | string | **YENİ (FIX #1):** "market_estimate" |

**Real nəticələr:** Gecikmə ~9.5%, orta utilization ~90.1%, flat/mountainous nisbəti ~88%/12%

---

## 7. spot_pricing.csv — 2000 sətir ⭐ (FIX #1 tam tətbiqi)

| Sütun | Tip | Məna |
|---|---|---|
| `rental_cost_azn` | float | **Baza Reys Qiyməti** lüğətindən |
| `spot_cost_azn` | float | baza × bayram multiplikatoru × `random(0.9,1.3)` |
| `pricing_confidence` | string | **YENİ:** "market_estimate" |

**Real nəticə:** Rental cost aralığı 33-1325 AZN (vehicle tipinə və məsafəyə görə)

---

## 8. transfer_center.csv — 5000 sətir

B2B sector_type (FIX #8) tətbiq olunur — qış aylarında tələb azalır.

**Real nəticə:** Bottleneck oranı ~14.5%

---

## 9. orders.csv — 50,000 sətir ⭐ (FIX #7 mənbəyi)

| Sütun | Tip | Məna |
|---|---|---|
| `order_id` | string | Unikal sifariş kodu |
| `region` | string | Sifariş mənşə regionu |
| `shipment_id` | string | **YENİ (FIX #7):** FK — bağlı TIR seferi və ya 'UNASSIGNED' |

**Real nəticə:** ~49.5% sifariş konkret shipment-ə bağlanıb (qalanlar hələ TIR-a yüklənməyib — real sistemdə də belə olur)

---

## 10. deliveries.csv — 50,000 sətir

| Sütun | Tip | Məna |
|---|---|---|
| `attempt_number` | int | **FIX #9:** uğursuz cəhd ehtimalı `uniform(0.02,0.06)` |

**Real nəticə:** Uğursuz cəhd faizi ~3.9%

---

## 11. gps_logs.csv — 100,000 sətir (FIX #6 — waypoint-based)

| Sütun | Tip | Məna |
|---|---|---|
| `latitude` / `longitude` | float | **Waypoint-based** piecewise-linear marşrut (düz xətt YOX) |
| `speed` | float | Sürət (km/saat) |

---

## 12. inventory.csv — 3000 sətir

Dəyişməyib (V2 ilə eyni məntiq).

---

## 13. traffic.csv — 15,000 sətir

Dəyişməyib (V2 ilə eyni məntiq) — Bakıda 8:30-9:30 və 17:30-20:00 ən pik saatlar.

---

## ⚠️ Hələ də Qalan Məhdudiyyətlər (Tam Şəffaflıq)

V3 9 zəif nöqtəni düzəltsə də, bunlar hələ də **tam doğrulanmamış** sahələrdir:

1. **AZN baza qiymətləri** — "market_estimate" kimi işarələnsə də, mənbə yenə də iki AI auditinin təxminidir, rəsmi 166 Logistika/Abşeron Logistika tarif sənədi əldə edilməyib
2. **Waypoint koordinatları** — real OSRM/Google Directions API-dən deyil, mənim əl ilə təxmin etdiyim coğrafi nöqtələrdir (OSRM API inteqrasiyası gələcək addım kimi qalır)
3. **Economic activity share** — DSK-da bu adda rəsmi statistika yoxdur, AI audit #2-nin keyfiyyət təxminidir
4. **Sector_type ayrımı** yalnız orders (B2C) və transfer_center/spot_pricing (B2B) səviyyəsində aparılıb — daha incə sənaye təsnifatı (tikinti vs. ərzaq vs. tekstil) yoxdur

---

## Texniki qeydlər

- **Reproducibility:** `SEED=42`
- **Run All** — notebook 13 CSV-ni `/mnt/user-data/outputs/` qovluğuna yazır (weather.csv, holidays.csv XARİC)
- **Doğrulanmış FK bütövlüyü:** orders↔shipments 100% uyğunluq (24,732 sifariş)
- **İcra müddəti:** ~60-90 saniyə (gps_logs.csv ən böyük fayldır)
