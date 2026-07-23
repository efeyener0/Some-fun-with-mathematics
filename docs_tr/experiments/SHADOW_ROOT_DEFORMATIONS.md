# Shadow Root Deformations

`shadow_root_deformations.py`, altı-boyutlu shadow clock'un multiplication
table'ını tek bir seyrek nokta olarak değil, exact bir affine completion
family'si olarak okur.

## Önce kapsam: bu bir bütün minimal-root sınıflandırması değildir

Sabitlenen veri şudur:

- chosen basis \((1,h,q,s,t,u)\);
- ortak birimli kaynak altcebir \(A=\operatorname{span}(1,h,q)\);
- `shadow_root_clock.py` içindeki literal \(L_s\) ve \(R_s\) clock'ları.

Özellikle bu gauge'de

\[
s q=q s=u
\]

zaten skeleton'ın parçasıdır. Strong-root aksiyomları tek başına bu eşitliği
zorlamaz. Onlar \(sh=hs=t\)'yi zorlar; `q` kuyruğunda yalnız

\[
s(sq)=1,
\qquad
(qs)s=-1
\]

sonuçlarını verir.

Script bunun için aynı altı-boyutlu uzayda explicit bir scope witness kurar:

\[
sq=u,\qquad qs=u+s,\qquad us=-1-h.
\]

Bu tabloda da \(s^2=h\), \(L_s^2=L_h\) ve \(R_s^2=R_h\) exacttır; fakat
literal clock farklıdır. Dolayısıyla aşağıdaki 48-boyutlu uzay:

> bütün minimal strong-root uzantılarının moduli değil, seçilmiş clock
> skeleton'ının bilinear completion fiber'ıdır.

Daha geniş kanonik altı-boyutlu seam sınıflandırması
[`SHADOW_ROOT_SEAMS.md`](./SHADOW_ROOT_SEAMS.md) ve
`shadow_root_seams.py` içindedir. Orada \(u:=qs\), \(a:=sq\), \(d:=su\)
seçilir; seam ile completion birlikte raw 54D, parity altında 27D table
family'si verir. Bu dosyanın incelediği

\[
a=u,\qquad d=1
\]

simetrik clock kesiti bunun 48D/24D affine slice'ıdır. Geniş family'de
repeated-`s` degree 5 yasası \(\{a:7,u:7\}\)'dir; burada \(a=u\) olduğu için
14 tree tek `u` phenotype'ında çöker.

Universal non-associative root adjunction'dan bu completion'ların her birine
bir quotient map vardır; farklı seam değerleri, universal bracket syntax'ına
farklı ek relations koyar.

## 48 boyut nereden geliyor?

Genel bir bilinear product, 36 ordered basis hücresinin her birinde altı
structure constant taşır: toplam \(6^3=216\) koordinat.

Constraint'leri dependency sırasıyla ekleyelim:

| Aşama | Sabit hücre | Eklenen hücre |
|---|---:|---:|
| ortak birim ve \(A\subset B\) | 15 | 15 |
| literal \(L_s,R_s\) | 24 | 9 |
| \(L_s^2=L_h,\ R_s^2=R_h\) | 28 | 4 |

Son aşamadaki dört yeni hücre

\[
ht=u,\quad hu=s,\quad th=u,\quad uh=-s
\]

olur. Geriye yalnız şu ordered seam kalır:

\[
qt, qu, tq, tt, tu, uq, ut, uu.
\]

Her hücre bağımsız bir \(B\)-vektörü seçebilir. Non-associative bir bilinear
algebra'da bundan başka “table consistency” koşulu yoktur: basis hücrelerini
seçmek product'ı tek biçimde bilinear uzatır. Böylece

\[
216-28\cdot6=48.
\]

Script selector constraint matrix'lerini de gerçekten kurar:

\[
\operatorname{rank}C_{root}=168,
\qquad
\dim\mathcal F_{clock}=216-168=48.
\]

## Shadow parity: 24 boyut

Doğal grading

\[
B_{\bar0}=\operatorname{span}(1,h,q),
\qquad
B_{\bar1}=\operatorname{span}(s,t,u)
\]

olsun. Her serbest ordered hücrenin parity'si output'u üç-boyutlu tek bir
grade'e sınırlar:

- `q*t`, `q*u`, `t*q`, `u*q` odd output taşır;
- `t*t`, `t*u`, `u*t`, `u*u` even output taşır.

Bu, 24 bağımsız “yanlış grade koordinatı sıfırdır” denklemi daha verir:

\[
\operatorname{rank}C_{graded}=192,
\qquad
\dim\mathcal F_{clock}^{\mathbb Z_2}=216-192=24.
\]

Dolayısıyla başlangıç tahmini exacttır: raw family 48D, parity kesiti 24D.

## Bütün fiber boyunca gerçekten sabit olanlar

Serbest sekiz hücrenin hiçbiri `s` veya `h` satır/sütununda değildir. Bu
nedenle her completion'da literal olarak aynı kalanlar:

- \(s^2=h\), \(L_s^2=L_h\), \(R_s^2=R_h\);
- \(L_s,R_s,L_h,R_h\) matrislerinin tamamı;
- operator order'ları \(6,12,3,6\);
- determinant ve nilpotent defect ledger'ı;
- \(\langle L_s,R_s\rangle\cong C_2^6\rtimes C_6\), order 384;
- grup shortlex profili ve element-order histogramı;
- yalnız outer `s` multiplication kullanan iki comb sequence;
- \(s,h,t,q,u,1\) üretim merdiveni.

Buradaki invariance bir finite sample gözlemi değildir: ilgili operatörlerin
her matrix column'u sabit hücrelerden gelir.

## İlk değişken Catalan derece

Birden beşe kadar her repeated-`s` subtree zorunlu olarak sırasıyla

\[
s, h, t, q, u
\]

olur. Altıncı derecede root split'leri exact olarak

\[
1+5, 2+4, 3+3, 4+2, 5+1
\]

verir. Ortadaki dört tree `t*t` hücresine gider; diğerleri clock tarafından
zorlanır. Bütün 48D family için measure identity:

\[
\boxed{\mu_6=19\,\delta_{+1}+19\,\delta_{-1}+4\,\delta_{tt}.}
\]

Seyrek origin'de `t*t=0`:

```text
-1:19, 0:4, +1:19
```

Parity-preserving küçük witness `t*t=1` ise:

```text
-1:19, +1:23
```

yapar. Yani eski rapordaki dört zero tree root skeleton'ın invariants'i değil,
tam olarak sparse seam seçiminin izidir.

İzole elementary seam'lerin ilk göründüğü dereceler:

| Hücre | İlk derece |
|---|---:|
| `t*t` | 6 |
| `q*t`, `t*q` | 7 |
| `t*u`, `u*t` | 8 |
| `q*u`, `u*q` | 9 |
| `u*u` | 10 |

Bu tablo, diğer seam'ler origin'de tutulduğunda exacttır. Birden çok hücre aynı
anda deform edilirse daha erken üretilmiş genel vektörler sonraki hücreleri
başka yollarla besleyebilir.

## Completion-sensitive algebraic structure

Seyrek origin için eski değerler yeniden exact hesaplanır:

\[
(\dim N_\ell,\dim N_m,\dim N_r)=(1,1,1),
\quad
\dim\operatorname{Comm}=2,
\quad
\operatorname{Der}=0.
\]

`q*t=s` dışında her şey origin'de bırakılırsa bütün root/operator invariants
korunurken

\[
\dim\operatorname{Comm}:2\longrightarrow1
\]

olur. Böylece `span(1,t)` commutant'ı açıkça sparse completion'a özeldir.

Nuclei, center, associator-rank ve derivation dimension için daha dikkatli bir
epistemik sınır gerekir. Origin bu constraint matrix'lerinde mümkün olan
maksimum rank'a sahiptir. Polynomial-minor sürekliliği nedeniyle

\[
N_\ell=N_m=N_r=\mathbb R1,\quad Z=\mathbb R1,\quad
\operatorname{rankAssoc}=6,\quad\operatorname{Der}=0
\]

bir nonempty Zariski-open komşulukta sabittir. Yani bunlar yalnız origin
noktasına ait kırılgan tesadüfler değildir. Fakat script bütün 48D family'nin
rank-jump locus'unu sınıflandırmaz ve “her completion'da aynıdır” demez.

Deep test, 48 pozitif coordinate-elementary completion'ın tamamını exact tarar;
bu taramada nuclei/center/associator/Der değişmez, commutant profili ise
22 completion'da 1 ve 26 completion'da 2 olur. Bu finite evidence'dır, global
theorem değildir.

## Çalıştırma

```powershell
python .\experiments\shadow_root_deformations.py
python .\experiments\shadow_root_deformations.py report --json
python .\experiments\shadow_root_deformations.py analyze tt_one
python .\experiments\shadow_root_deformations.py analyze qt_s --max-leaves 10
python .\experiments\shadow_root_deformations.py test
python .\experiments\shadow_root_deformations.py test --deep
```

Normal test constraint rank'larını, named witnesses'ları, operator invariants'i,
scope counterwitness'ı ve bütün seam-visibility derecelerini doğrular.
`--deep`, 48 coordinate-elementary completion'ın structural rank taramasını da
çalıştırır.

## Kanıt sınırı

Kanıtlanan:

- literal fixed-clock fiber'ın 48D affine yapısı;
- parity-graded kesitin 24D oluşu;
- sekiz free ordered cell dışında gizli bilinearity constraint bulunmaması;
- root/operator/384-group invariants'inin bütün fiber boyunca sabitliği;
- degree-six measure identity ve isolated seam visibility ladder;
- commutant ile repeated-`s` ekolojisinin completion-sensitive oluşu;
- strong-root aksiyomlarının `s*q=q*s`'yi zorlamadığı explicit 6D witness.

Kanıtlanmayan:

- bütün minimal strong-root extension'ların classification'ı;
- 48D fiber'da bütün algebraic rank-jump strata'ları;
- sparse completion'ın universal veya canonical olduğu;
- elementary finite scan'in bütün reel parametreleri temsil ettiği.
