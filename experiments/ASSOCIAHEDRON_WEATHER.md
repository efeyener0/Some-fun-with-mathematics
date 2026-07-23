# Associahedron Weather

`associahedron_weather.py`, Bracket Garden'ın explicit Catalan ağaçlarını tek
rotasyon geometrisine yerleştirir. Her vertex bir bracket history'dir; her edge
yalnız şu lokal hamledir:

\[
((A B)C)\longleftrightarrow A(B C).
\]

Araç `bracket_garden.py` dosyasını aynı klasörden import eder. İki oyuncak aynı
`Leaf(index)`, `Branch(left,right)`, tree ID ve exact \(1,h,q\) çarpımını
paylaşır. Harici paket yoktur.

## Associahedron 1-skeleton

\(n\) sıralı yaprak için vertex sayısı:

\[
V_n=C_{n-1}.
\]

\(n\ge 3\) için her full binary tree'nin \(n-2\) internal rotation edge'i
vardır. Dolayısıyla undirected edge sayısı:

\[
E_n=\frac{C_{n-1}(n-2)}{2}.
\]

Kod yalnız `((AB)C) -> (A(BC))` yönünü üretir; bu yön edge'e delta işareti
vermek içindir. Adjacency undirected tutulur. Ters rotasyon ayrıca ikinci bir
edge olarak sayılmaz.

```powershell
python .\experiments\associahedron_weather.py topology --max-leaves 8
```

Beklenen exact ledger:

| Yaprak | Vertex | Edge | Derece |
|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 |
| 2 | 1 | 0 | 0 |
| 3 | 2 | 1 | 1 |
| 4 | 5 | 5 | 2 |
| 5 | 14 | 21 | 3 |
| 6 | 42 | 84 | 4 |
| 7 | 132 | 330 | 5 |
| 8 | 429 | 1287 | 6 |

Generator bu sayıları, regular degree'i ve graph connectivity'sini sekiz
yaprağa kadar gerçekten kontrol eder.

## Kenardaki iki residual

Canonical source'taki rotation site'ı `((A*B)*C)` olsun. Lokal associator:

\[
\Delta_{local}=((ab)c)-a(bc).
\]

Aynı replacement bütün ağacın içinde yapıldığında root phenotype deltası:

\[
\Delta_{root}
=\operatorname{eval}(T_{source})-\operatorname{eval}(T_{target}).
\]

Bu ikisi aynı nesne değildir. Rotation root'taysa eşittir; rotation daha derin
bir context içindeyse lokal residual dış çarpımların indüklediği lineer context
map'inden geçer. Non-zero lokal associator root'ta sıfırlanabilir.

Weather sınıfları:

- **ACTIVE:** `root_delta != 0`; komşu vertex'lerin phenotype'ı farklıdır.
- **DAMPED:** `local_associator != 0`, fakat `root_delta == 0`; context lokal
  residual'ı söndürmüştür.
- **CALM:** Lokal associator zaten sıfırdır; rotation phenotype-silent'tır.

`local_associator == 0` iken root'un değişememesi implementation assertion'ıdır.

## Bir kelimenin forecast'u

```powershell
python .\experiments\associahedron_weather.py forecast hhqqhq
python .\experiments\associahedron_weather.py forecast hhqqhq --edges damped --limit 0
```

Forecast şunları birlikte verir:

- her phenotype'ın explicit `Tn:index` vertex ID'leri;
- exact vertex expression ve lossless shape code;
- active, damped ve calm edge sayıları;
- her `En:index` rotation için lokal associator ve root delta;
- aynı phenotype vertex'lerinin indüklediği subgraph component'leri.

`--edges` filtresi `all`, `active`, `silent`, `damped`, `calm` değerlerini
alır. `--limit 0`, filtrelenmiş bütün edge ve vertex etiketlerini gösterir.

Tek bir edge'i büyüteç altına almak için:

```powershell
python .\experiments\associahedron_weather.py rotation hhqqhq --edge 17
```

Edge ID, canonical source/target tree ID'leri, rotation path'i, tam iki
parantezli ifade, \([a,b,c]\), lokal associator ve root delta birlikte yazılır.

## Phenotype adaları

Bir phenotype \(p\) için yalnız phenotype'ı \(p\) olan vertex'ler ve aralarında
kalan rotation edge'leri alınır. Araç bu induced subgraph'ın component'lerini
exact çıkarır.

Aynı phenotype'a sahip iki tree'nin aynı induced component'te olması, silent
rotasyonlardan oluşan bir yol bulunduğu anlamına gelir. Ayrı component'lerde
olmaları, aynı element sonucuna rağmen associahedron üzerinde phenotype'ı
değiştirmeden birbirlerine yürüyemediklerini gösterir.

Bu, multilinear-map equality değildir. Yalnız seçilmiş leaf word ve onun
rotation graph'ına ait bir gözlemdir.

## Deterministik expedition

```powershell
python .\experiments\associahedron_weather.py expedition --max-leaves 7
```

Altkomutsuz çalıştırma da aynı expedition'ı başlatır. Her \(n\le7\) için bütün
\(2^n\) pozitif `h/q` kelimeleri exhaustive taranır. Üç farklı ve açıkça ilan
edilmiş objective vardır:

1. **Storm champion:** active edge sayısını maksimize eder.
2. **Damping champion:** non-zero lokal associator'ı root'ta sönen edge
   sayısını maksimize eder.
3. **Fracture champion:** phenotype başına bir component'in ötesindeki toplam
   component sayısını maksimize eder.

Score tie'ları ikincil metriklerden sonra `h < q` lexical sırasıyla çözülür;
randomness yoktur. “Interesting” tek ve evrensel bir matematiksel büyüklükmüş
gibi sunulmaz.

Expedition iki named front'u ayrıca raporlar:

- Bracket Garden'ın altı-mask witness'ı `hhqqhq`;
- saf `h^7 = hhhhhhh`.

## Test

```powershell
python .\experiments\associahedron_weather.py test
python .\experiments\associahedron_weather.py test --deep
```

Normal test topology ledger'ını, connectivity/regularity'yi, edge-state
partition'ını ve iki named front'un exact metriklerini denetler. `--deep`, tüm
`h/q` kelimelerini yeniden tarayıp champion'ları \(n=7\)'ye kadar yeniden
üretir.

## Epistemik sınır

Şunlar birbirinden ayrıdır:

- Catalan vertex/edge formülü ve rotation connectivity, bilinen kombinatoryal
  yapıdır; script bunun \(n\le8\) örneklerini exact yeniden üretir.
- Belirli bir kelimenin weather raporu, o sonlu graph üzerinde exact
  hesaplamadır.
- Expedition sonuçları \(n\le7\) içindeki exhaustive gözlemlerdir; bütün
  dereceler için theorem değildir.
- `DAMPED`, dış context'in bu cebirsel residual'ı yok ettiğini söyler; fiziksel
  enerji sönümü veya zaman dinamiği iddiası değildir.
- Phenotype component'i, tree identity veya multilinear-map identity'nin
  yerine geçmez.

Graph üretimi etkileşimli ve recoverable kalsın diye weather dokuz, topology
doğrulaması sekiz, exhaustive word search yedi yaprakta sınırlıdır. Sınır
aşılırsa tree'leri quotient'lamak ya da örneklemek yerine açık hata verilir.
