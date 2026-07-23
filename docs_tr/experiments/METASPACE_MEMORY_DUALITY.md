# Metaspace Memory Duality

Bu oyuncak, [Metaspace Observability](./METASPACE_OBSERVABILITY.md) ile
[Metaspace Synchronizer](./METASPACE_SYNCHRONIZER.md) sonuçlarının aynı üç
equivalence kernel'inin iki yönü olduğunu gösterir:

- **okuma:** üç root probe birlikte 192 state'i tamamen ayırır;
- **silme:** üç rank-1 suffix'in her biri yalnız bir sütunu koruyup 192 state'i
  altı sonuca katlar.

Buradaki “duality”, exact kernel eşitliği demektir. Hilbert-space adjoint'i,
termodinamik yasa veya fiziksel ölçüm iddiası değildir.

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py -B .\experiments\metaspace_memory_duality.py
& $py -B .\experiments\metaspace_memory_duality.py --deep-check --json
```

## Aynı state'in üç sütunu

[Certified Signed Metaspace](./CERTIFIED_SIGNED_METASPACE.md) normal formunda
bir state

\[
a=(a_1,a_2,a_3)
\]

ve her $a_j$, ilgili basis sütununun imzalı hedef eksenidir. Root yalnız ilk
sütunu okur:

\[
o(M)=M e_1=a_1.
\]

Fakat sağdan generator eklemek probe eksenini değiştirir:

\[
o(ML_h)=M e_2=a_2,
\qquad
o(ML_q)=M e_3=a_3.
\]

Dolayısıyla

\[
\boxed{\bigl(o(M),o(ML_h),o(ML_q)\bigr)=(a_1,a_2,a_3)}
\]

ve bu üç deney 192 state için 192 ayrı signature üretir.

## Üç coordinate silgisi

Rank-1 suffix $p_k$, bütün basis vektörlerini aynı coordinate line'a gönderir.
Bu durumda

\[
M p_k=N p_k
\iff
M e_k=N e_k.
\]

Yani right action'ın kernel'i, tam olarak $k$. sütun equality'sidir. Dört
generatorlı shortlex sözleşmesindeki en kısa üç silgi:

| Korunan sütun | En kısa suffix | Derinlik | Image | Fiber |
|---|---|---:|---:|---:|
| $1$ | `Lh Lq Lq` | 3 | 6 | $6\times32$ |
| $h$ | `Lh Lh Lq Lq` | 4 | 6 | $6\times32$ |
| $q$ | `Lq Lq` | 2 | 6 | $6\times32$ |

Her silgi 192 state'i altı signed-column değerine indirir. Zero matrix monoid'de
yoktur; minimum rank 1'dir. Bu nedenle tam reset yerine altı-state'lik silinemez
bir taban kalır.

Daha genel olarak $I(p)=\{|p_1|,|p_2|,|p_3|\}$ suffix'in retained coordinate
kümesi ise signed composition formülü doğrudan

\[
\boxed{Mp=Np\iff M_i=N_i\text{ bütün }i\in I(p)\text{ için}}
\]

ve dolayısıyla

\[
\boxed{\ker R_p=\bigcap_{i\in I(p)}E_i}
\]

verir. Erişilen yedi kernel, üç elemanlı Boolean lattice'in boş olmayan bütün
altkümeleridir: rank 1'de üç singleton, rank 2'de üç pair, rank 3'te full
üçlü. Universal kernel'i verecek boş retained-set yoktur; bu, reset yokluğunu
yalnız exhaustive aramadan değil rank-0'ın yokluğundan da açıklar. Script bu
projection/product bijection'ını 192 suffix'in hepsinde doğrular.

## Kernel lattice'i

$E_1,E_h,E_q$, ilgili sütunu eşit olan unordered state pair'leri olsun.
Her biri altı adet 32-state sınıfından oluşur:

\[
|E_k|=6\binom{32}{2}=2{,}976.
\]

İki sütunu birden aynı olan pair sayısı her seçim için 432; üç sütunu aynı olan
distinct pair yoktur:

\[
|E_1\cap E_h|=|E_1\cap E_q|=|E_h\cap E_q|=432,
\]

\[
|E_1\cap E_h\cap E_q|=0.
\]

Buradan inclusion–exclusion:

\[
|E_1\cup E_h\cup E_q|
=3(2{,}976)-3(432)
=7{,}632.
\]

Bu sayı synchronizer'ın “en az bir suffix ile birleşebilir” pair sayısıyla tam
aynıdır. Kalan

\[
18{,}336-7{,}632=10{,}704
\]

pair hiçbir coordinate sütununu paylaşmadığı için hiçbir word ile birleşmez.

Dolayısıyla aynı kernel ailesi iki farklı mantıksal bağla okunuyor:

\[
\boxed{E_1\cap E_h\cap E_q=\Delta}
\]

üç probe birlikte complete tomography verirken,

\[
\boxed{E_1\cup E_h\cup E_q}
\]

en az bir rank-1 silgiyle synchronize olabilen pair grafını verir. Kesişim
“bütün deneylerden saklanabilme”, birleşim “en az bir silmeyle bir olabilme”dir.

Exact eşit-sütun profili:

| Aynı sütun kümesi | Pair |
|---|---:|
| hiçbiri | 10.704 |
| yalnız $1$ | 2.112 |
| yalnız $h$ | 2.112 |
| yalnız $q$ | 2.112 |
| $1,h$ | 432 |
| $1,q$ | 432 |
| $h,q$ | 432 |

## Sol ve sağ information geometry

Bir rank-$r$ suffix $p$ için iki image farklı sorular sorar:

\[
Mp=\{xp:x\in M\}
\]

başlangıç state'lerini suffix'in **range sütunlarında** ne kadar ayırt
edebildiğimizi;

\[
pM=\{px:x\in M\}
\]

ise suffix'in signed image alphabet'inden üç output sütunu ne kadar serbest
kurabildiğini ölçer.

| Matrix rank | $|Mp|$ | $|pM|$ | $M\to Mp$ fiber profili |
|---:|---:|---:|---|
| 1 | 6 | 8 | $6\times32$ |
| 2 | 36 | 64 | $12\times4 + 24\times6$ |
| 3 | 192 | 192 | $192\times1$ |

Singular tabakalarda formüller doğrudan tuple geometrisinden gelir:

\[
|Mp|=6^r,
\qquad
|pM|=(2r)^3,
\qquad r\in\{1,2\}.
\]

- $Mp$: $p$'nin range'indeki $r$ source sütununun her biri altı signed
  eksenden birine gidebilir.
- $pM$: üç output sütununun her biri $p$'nin $2r$ signed image değerinden
  birini seçebilir.

Rank 3'te $p$ unit olduğu için her iki multiplication da $M$ üzerinde
bijection'dır ve ambient 216 yerine monoid'in 192 state'ini korur.

### Rank-2 parity izi

Rank-2 right action 36 retained column-pair'i üretir. Eksik üçüncü sütun için:

- daha önce kullanılmış iki absolute target'tan birine giden dört signed seçim
  state'i singular tutar ve daima içeridedir;
- kalan absolute target'a giden iki signed seçim bir unit oluşturur ve yalnız
  absolute permutation even ise içeridedir.

Bu nedenle 36 output'un 12'sinin fiber'ı 4, 24'ünün fiber'ı 6'dır. Önceki
oyuncakta bulunan “parite yalnız unit tabakasında yaşar” karakteri burada bir
information-fiber asimetrisi olarak tekrar görünür.

## Doğrulama

Script gerçekten şunları denetler:

- 192 tomography signature'ının hepsinin farklı olduğunu;
- $3\times18{,}336=55{,}008$ eraser-kernel pair eşitliğini;
- bütün 192 suffix için toplam 73.728 sol/sağ product'u;
- rank/image ve fiber profillerini;
- `--deep-check` altında bağımsız observability ve synchronizer raporlarının
  horizon, pair-union, complement, minimum-image ve reset sonuçlarıyla parity'yi.

**Exact scope:** literal dört generator, 192-state finite monoid ve signed-code
normal formu.

**İddia edilmeyen:** fiziksel ölçülebilirlik, termodinamik information loss,
quantum duality veya bu sayıların genel matrix semigroup'lara otomatik uzanması.
