# Metaspace Synchronizer

`metaspace_synchronizer.py`, `chiral_operator_monoids.py` içindeki 192 elemanlı
combined monoid'i dört harfli deterministic finite automaton olarak okur.
Amaç matris uzayını yaklaşık ölçmek değil; bütün finite monoid ürünlerini exact
tarayarak sağ çarpım kelimelerinin state sıkıştırma geometrisini çıkarmaktır.

Harici paket, randomness ve floating point yoktur.
Minimum runtime Python 3.9'dur; hem bu script hem yerel kaynak modülü Python
3.9 grammar ile ayrıca parse edilmiştir.

## Convention: sağ action, sol ideal

Generator sırası:

```text
L_h, L_q, R_h, R_q
```

Kelime sağa eklenir:

\[
p(g_1\ldots g_k)=(((I g_1)g_2)\cdots)g_k.
\]

Automaton geçişi:

\[
\delta(x,g)=xg.
\]

Dolayısıyla product \(p\)'nin 192 başlangıç durumu üzerindeki image'i:

\[
\operatorname{Im}(R_p)=\{xp:x\in M\}=Mp.
\]

Bu, generator'lar sağdan etki etse de **principal left ideal**'dır ve
Green-\(\mathcal L\) sınıflarını ölçer. İstenen principal right ideal ve
Green-\(\mathcal R\) tarafı ayrıca:

\[
pM=\{px:x\in M\}
\]

olarak hesaplanır. Script bu iki convention'ı isim olarak ters çevirmemeye
özellikle dikkat eder.

## Kullanım

```powershell
python .\experiments\metaspace_synchronizer.py
python .\experiments\metaspace_synchronizer.py --deep-check
python .\experiments\metaspace_synchronizer.py --json
python .\experiments\metaspace_synchronizer.py --deep-check --json
```

`--json`, class üyeleri, Hasse cover'ları, shortest witness'lar ve exact
profilleri içeren machine-readable sertifikayı verir.

`--deep-check` ayrıca:

- \(192^3=7{,}077{,}888\) Cayley-table associativity triple'ını;
- kaydedilmiş bütün shortest word'lerin transition replay'ini;
- bütün distinct principal left/right ideal'ların uygun yöndeki closure'ını

denetler.

## Exact image-size spektrumu

192 product elemanının indüklediği 192 right transformation birbirinden
farklıdır. Bunun küçük ama kesin witness'ı identity state'tir:

\[
R_p(I)=p.
\]

Erişilebilen image size'lar yalnız:

\[
\boxed{192,\ 36,\ 6}.
\]

| İlk erişim | Kelime | Matrix rank | Image size |
|---:|---|---:|---:|
| 0 | `epsilon` | 3 | 192 |
| 1 | `L_q` | 2 | 36 |
| 2 | `L_q L_q` | 1 | 6 |

Product profili:

| Matrix rank | Product sayısı | \(|Mp|\) | \(|pM|\) |
|---:|---:|---:|---:|
| 3 | 24 | 192 | 192 |
| 2 | 144 | 36 | 64 |
| 1 | 24 | 6 | 8 |

Bu literal monoid içinde matrix rank hem automaton image size'ı hem principal
right-ideal size'ı tek değerli belirliyor. Bu genel bir matrix semigroup teoremi
değildir; burada exhaustive gözlenen exact ilişkidir.

Minimum image size 6'dır. Bütün 192 product transformation tarandığı ve right
regular action faithful olduğu için:

\[
\boxed{\text{reset word yoktur}.}
\]

### Kernel fiber şekilleri

Image size aynı olan bütün product'lar aynı fiber-cardinality profilini taşır:

- image 192: 192 adet size-1 fiber;
- image 36: 12 adet size-4 ve 24 adet size-6 fiber;
- image 6: 6 adet size-32 fiber.

Bu profil yalnız image cardinality'yi değil, 192 başlangıç state'inin nasıl
katlandığını da gösterir.

## Pair synchronizability

Toplam unordered state pair sayısı:

\[
\binom{192}{2}=18{,}336.
\]

Exact sonuç:

- synchronizable: **7,632**;
- hiçbir kelimeyle birleşmeyen: **10,704**.

Shortest merge depth profili:

| Depth | Pair sayısı |
|---:|---:|
| 1 | 432 |
| 2 | 2,976 |
| 3 | 2,112 |
| 4 | 2,112 |

En uzun shortest pair-merge kelimesi dört generator'dır.

### Sütun kriteri

Her monoid elemanı basis vektörlerini signed basis vektörlerine gönderen bir
action matrix'tir. İki state \(x,y\) için exhaustive olarak doğrulanan kriter:

\[
\boxed{x,y\text{ synchronize olur}\iff
x\text{ ve }y\text{ en az bir basis sütununda aynıdır}.}
\]

Buradaki sütunlar \(1,h,q\) basis vektörlerinin image'leridir. Exact-equal
column subset profili:

24 rank-1 product'un image line'ları da exact denetlendi; üç coordinate line
\(\mathbb R1\), \(\mathbb Rh\), \(\mathbb Rq\) birlikte erişilebilirdir.

| Aynı sütunlar | Pair | Shortest ortak merge depth | Deterministik witness |
|---|---:|---:|---|
| `{1,q}` | 432 | 1 | `L_q` |
| `{1,h}` | 432 | 2 | `L_h L_q` |
| `{h,q}` | 432 | 2 | `L_q L_q` |
| `{q}` | 2,112 | 2 | `L_q L_q` |
| `{1}` | 2,112 | 3 | `L_h L_q L_q` |
| `{h}` | 2,112 | 4 | `L_h L_h L_q L_q` |

Hiç aynı sütunu olmayan 10,704 pair synchronizable değildir. Complete DFA'da
reset word varsa her pair synchronize olmalıdır; burada pair profili de reset
yokluğunu bağımsız biçimde görünür kılar.

## Green geometrisi

### Automaton image: Green-L

\(Mp\) image'leri:

- 11 distinct principal left ideal;
- 1 adet size 192;
- 6 adet size 36;
- 4 adet size 6.

Green-\(\mathcal L\) class cardinality profili:

- 7 class size 24;
- 4 class size 6.

Hasse incidence'i: dört size-6 bottom ideal'in her biri üç size-36 ideal
tarafından cover edilir; altı size-36 ideal'in her biri iki bottom'u cover
eder. Sonra tek size-192 top gelir. Sayısal incidence, tetrahedron'un
vertex-edge incidence düzeniyle aynıdır; bu bir hesaplanabilir benzetmedir,
monoid'in kendisini tetrahedron ilan etmez.

### Principal right ideals: Green-R

\(pM\) ailesi:

- 7 distinct principal right ideal;
- 1 adet size 192;
- 3 adet size 64;
- 3 adet size 8.

Green-\(\mathcal R\) class cardinality profili:

- unit class: size 24;
- üç rank-2 class: size 48;
- üç rank-1 class: size 8.

Üç size-8 bottom ideal'in her biri iki size-64 ideal tarafından cover edilir;
her size-64 ideal iki bottom'u cover eder; sonra tek top gelir. Bu incidence
triangle vertex-edge düzenini taşır.

### J, D ve H

Principal two-sided ideal'lar üçlü bir chain oluşturur:

\[
24 < 168 < 192.
\]

Üç Green-\(\mathcal J\)/\(\mathcal D\) class doğrudan matrix rank 1, 2, 3
katmanlarıdır; finite hesapta \(\mathcal D=\mathcal J\) doğrulandı.

31 Green-\(\mathcal H\) class vardır:

- bir size-24 unit H-class;
- 18 size-8 H-class;
- 12 size-2 H-class.

Bunların 25'i birer idempotent içerir; altı H-class idempotent içermez.

## Epistemik sınır

Verified fact:

- bütün 192 product ve \(192^2\) pairwise product materialize edildi;
- image iddiaları bütün 192 right transformation'ı kapsar;
- pair iddiaları bütün 18,336 unordered pair'i kapsar;
- ideal ve Green profilleri aynı finite Cayley table'dan exact türetildi.

Finite structural inference:

- equal-column criterion hem exhaustive doğrulandı hem rank-1 product'ların üç
  coordinate line'ı da erişebilmesiyle açıklanır;
- triangle/tetrahedron ifadeleri yalnız Hasse incidence desenini anlatır.

İddia edilmeyen:

- bu rank/image formülünün genel finite matrix monoid'lerde geçerli olduğu;
- Green incidence benzetmelerinin fiziksel uzay veya zorunlu ontoloji olduğu;
- başka generator setlerinin aynı synchronization profilini koruyacağı.

Bu oyuncak yalnız kaynak dosyadaki dört literal \(3\times3\) integer generator
ve onların exact 192-state closure'u hakkındadır.
