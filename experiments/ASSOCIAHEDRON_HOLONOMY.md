# Associahedron Holonomy

`associahedron_holonomy.py`, Associahedron Weather'ın rotation edge'lerini bir
discrete connection olarak yeniden okur. Root phenotype farkının cycle boyunca
sıfır olduğunu söylemek başlangıçtır; oyuncak bunun altında hangi residual'ın
taşındığını ve hangi bilginin yalnız root projection'da düzleştiğini çıkarır.

Yerel bağımlılıklar:

- `bracket_garden.py`: exact (1,h,q) cebiri ve explicit binary tree'ler;
- `associahedron_weather.py`: exact single-rotation graph ve edge weather.

Harici paket, randomness veya floating point yoktur. Bu iki dependency Python
3.10 sözdizimi kullandığı için minimum runtime Python 3.10'dur.

## Edge connection

Bir edge'de rotation site'ı:

\[
((A B)C)\longrightarrow A(B C)
\]

olsun. Lokal associator:

\[
r_e=[a,b,c]=(ab)c-a(bc).
\]

Rotated subtree'nin dışında kalan bütün tree, tek-delikli lineer bir context
map'i tanımlar:

\[
C_e:A\to A.
\]

Script \(C_e\)'yi \((1,h,q)\) basis elemanlarını deliğe ayrı ayrı koyarak exact
\(3\times3\) integer matrix olarak kurar. Her edge için doğrulanan temel
faktorizasyon:

\[
\boxed{\Delta_e^{root}=C_e(r_e).}
\]

Weather'daki `DAMPED` edge artık daha keskin okunabilir:

\[
r_e\ne0,\qquad r_e\in\ker C_e.
\]

Dolayısıyla full-rank context nonzero associator'ı söndüremez. Script bunu her
edge'de assertion olarak tutar.

Buradaki “connection” sözcüğü operasyoneldir: \(C_e\), local rotation
residual'ından ortak root algebra'sına giden bir transport operatörüdür. Rank'ı
düşebilir; dolayısıyla vertex fiber'ları arasında invertible bir gauge parallel
transport olduğu iddia edilmez. Singular oluşu zaten `DAMPED` olgusunun
matematiksel içeriğidir.

## Üç farklı “düzlük” seviyesi

### 1. Root 1-form

Vertex potential'ı \(F(T)=\operatorname{eval}_T(w)\) olsun. Oriented edge:

\[
\omega_e=F(source)-F(target)=\Delta_e^{root}.
\]

Bu exact gradient'tır. Her cycle için:

\[
\oint\omega=0.
\]

Bu sonuç doğrudur ama tek başına ilginç residual'ı göstermez.

### 2. Ham lokal-frame holonomy

Bütün local copies of (A), seçilmiş (1,h,q) basis'iyle naif biçimde aynı
frame kabul edilirse:

\[
H_F^{raw}=\sum_{e\in\partial F}\operatorname{sign}(e)r_e.
\]

Bu toplam sıfır olmak zorunda değildir. Her edge için context correction:

\[
k_e=(C_e-I)r_e
\]

tanımlandığında her square ve pentagon yüzünde exact closure:

\[
\boxed{H_F^{raw}+\sum_{e\in\partial F}\operatorname{sign}(e)k_e=0.}
\]

Yani root connection düzdür; ham associator frame'i genellikle değildir.
`raw holonomy` basis ile yapılan canonical identification'a bağlıdır. Script
bunu intrinsic fiziksel curvature diye sunmaz.

### 3. Square mixed curvature

Square face iki commuting rotation'ı taşır. Canonical cycle vertex'leri
(T_0,T_1,T_2,T_3) ise:

\[
K_\square=F(T_0)-F(T_1)+F(T_2)-F(T_3).
\]

Bu root circulation değildir; discrete mixed finite difference/Hessian'dır.
Bir rotation'ın diğerinden önce ve sonra oluşturduğu effect değişimini ölçer.
İki yönden hesaplanan cross-effect exact aynıdır:

\[
\Delta_A^{after}-\Delta_A^{before}
=\Delta_B^{after}-\Delta_B^{before}
=-K_\square.
\]

\(K_\square\ne0\), syntactically commuting iki reassociation'ın phenotype
etkilerinin additive-independent olmadığını gösterir.

## Pentagon coherence

Dört macro-element (a,b,c,d) için iki reassociation yolu vardır: biri üç,
diğeri iki rotation kullanır. Associator tanımından çıkan exact identity:

\[
[a,b,c]d+[a,bc,d]+a[b,c,d]
=[ab,c,d]+[a,b,cd].
\]

Script bu polynomial identity'yi \(3^4=81\) tensor-basis quadruple'ında exact
doğrular. İfade dört girdide multilinear olduğundan basis doğrulaması bütün
\(A^4\) için yeterlidir.

Bir pentagon daha büyük tree context'ine gömüldüğünde iki yolun root toplamı
yine aynıdır. Fakat yalnız çıplak local associator'ları toplamak iki yolda
farklı sonuç verebilir; fark tam olarak `raw holonomy`, context correction ise
onun negatifidir.

## 2-cell ledger

```powershell
python .\experiments\associahedron_holonomy.py topology --max-leaves 8
```

Associahedron'un induced square/pentagon yüz sayıları:

| Yaprak | Square | Pentagon |
|---:|---:|---:|
| 3 | 0 | 0 |
| 4 | 0 | 1 |
| 5 | 3 | 6 |
| 6 | 28 | 28 |
| 7 | 180 | 120 |
| 8 | 990 | 495 |

Kullanılan exact formüller:

\[
P_n=\binom{2n-4}{n-4},
\qquad
Q_n=\frac{n-4}{2}P_n.
\]

Her square'ın rotation signature'ı `A,B,A,B` biçiminde; her pentagonunki beş
farklı rotation biçiminde ayrıca doğrulanır.

## CLI

Tek kelimeyi bütün context ve yüzleriyle incelemek:

```powershell
python .\experiments\associahedron_holonomy.py analyze hhqqhq
python .\experiments\associahedron_holonomy.py analyze hhhhhhh --face-limit 0
```

`--face-limit`, her türden kaç exact face record yazılacağını belirler; `0`
hepsini gösterir. Her kayıtta explicit tree ID cycle'ı, root circulation, raw
holonomy, context compensation, iki path'in root/raw toplamları ve square ise
mixed curvature bulunur.

Deterministik named-front ve exhaustive champion raporu:

```powershell
python .\experiments\associahedron_holonomy.py expedition
```

Altkomutsuz çalıştırma da expedition'dır. \(n=4\ldots7\) aralığında bütün
\(2^n\) pozitif `h/q` kelimeleri taranır. Ayrı objective'ler:

- nonzero square raw holonomy sayısı;
- nonzero pentagon raw holonomy sayısı;
- nonzero square mixed curvature sayısı;
- damped edge sayısı.

Bir objective eşitse diğer metrikler, tam eşitlikte `h < q` shortlex düzeni
tie-break olur. “Holonomy en ilginçtir” gibi tek, gizli bir estetik objective
uydurulmaz.

## Self-test

```powershell
python .\experiments\associahedron_holonomy.py test
python .\experiments\associahedron_holonomy.py test --deep
```

Normal test:

- 2-cell ledger'ını (n=7)'ye kadar;
- bütün edge context faktorizasyonlarını named front'larda;
- 81 basis pentagon identity'sini;
- `hhqqhq` ve saf `h^7` holonomy sayılarını

doğrular.

`--deep`, \(n=8\) face ledger'ını, \(n\le7\) içindeki 254 pozitif `h/q`
kelimesinin bütün connection/face assertion'larını ve aynı aralıktaki exhaustive
word champion'larını yeniden üretir.

## Exact gözlemler

`hhqqhq`:

- context rank profile: rank-3 `47`, rank-2 `34`, rank-1 `3`;
- 28 square'ın 14'ünde raw holonomy nonzero;
- 28 square'ın 15'inde mixed curvature nonzero;
- 28 pentagonun 17'sinde raw holonomy nonzero.

Saf `h^7`:

- context rank profile: rank-3 `258`, rank-2 `68`, rank-1 `4`;
- 180 square'ın 105'inde raw holonomy nonzero;
- 180 square'ın 117'sinde mixed curvature nonzero;
- 120 pentagonun 90'ında raw holonomy nonzero.

Bu sayılar finite exhaustive observation'dır; bütün (n) için theorem değildir.

## Epistemik sınır

Kanıtlanan/identity düzeyi:

- root delta'nın gradient olması;
- edge factorization \(\Delta^{root}=C_e(r_e)\);
- context-compensated face closure;
- square cross-effect eşitliği;
- associator pentagon identity'si.

Finite exact doğrulama:

- square/pentagon ledger \(n\le8\);
- named word context/holonomy profilleri;
- bütün pozitif `h/q` kelimelerinde full connection/face raporu \(n\le7\),
  toplam 254 kelime;
- champion search \(n\le7\).

Gauge-dependent okuma:

- raw local holonomy, farklı local copies of (A)'yı aynı basis frame'inde
  özdeşleştirme seçimine bağlıdır;
- square mixed curvature root phenotype potential'ından gelir ve canonical
  cycle orientation değişirse işaret değiştirebilir; zero/nonzero oluşu
  orientation-independent'tır.

İddia edilmeyen:

- bu discrete curvature'ların fiziksel gauge field veya enerji olduğu;
- finite sayı profillerinin bütün derecelere genellendiği;
- context rank'ın tek başına edge activity'yi belirlediği.
