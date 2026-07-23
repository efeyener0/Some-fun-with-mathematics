# Signed Metaspace Family

192-state yapının hangi kısmı gerçekten üç boyuta özgü, hangi kısmı daha genel
bir signed-transformation geometrisi? Bu oyuncak ikinci kısmı soyut bir aileye
ayırır.

Önemli sınır: burada tanımlanan $M_n$, abstract finite monoid ailesidir. Kaynak
non-associative cebirin $n$-boyutlu extension'ı olduğu iddia edilmez. Literal
chiral operator monoid'iyle yalnız $n=3$ üyesi özdeşleştirilmiştir.

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py -B .\experiments\signed_metaspace_family.py
& $py -B .\experiments\signed_metaspace_family.py --deep-check --max-n 8 --json
```

## Tanım

Bir signed transformation

\[
a=(a_1,\ldots,a_n)\in\{\pm1,\ldots,\pm n\}^n
\]

ile kodlansın ve

\[
a(e_j)=\operatorname{sgn}(a_j)e_{|a_j|}
\]

olsun. Ambient signed full transformation monoid'i

\[
\Sigma_n=C_2\wr T_n,
\qquad
|\Sigma_n|=(2n)^n.
\]

Karakter:

\[
\chi_n(a)=
\begin{cases}
0, & |a|\text{ singular ise},\\
+1, & |a|\in A_n,\\
-1, & |a|\in S_n\setminus A_n.
\end{cases}
\]

Signed composition aynı tuple yasasını korur:

\[
(a\star b)_j=\operatorname{sgn}(b_j)a_{|b_j|},
\]

ve dolayısıyla

\[
\chi_n(a\star b)=\chi_n(a)\chi_n(b).
\]

$n\ge2$ için parity-cut aile:

\[
\boxed{M_n=\chi_n^{-1}(\{0,+1\})}.
\]

Yani bütün singular signed map'ler ve yalnız absolute permutation'ı even olan
signed unit'ler içeride. Singular set two-sided ideal; even unit'ler subgroup
olduğu için kapanış doğrudan karakterden gelir.

Unit group:

\[
U(M_n)=C_2^n\rtimes A_n.
\]

Bu yine determinant-positive kesit değildir; bağımsız sütun sign'ları
determinant işaretini ayrıca değiştirebilir.

Ambient'ten atılanlar yalnız signed odd-permutation unit'lerdir. Dışarıdaki
herhangi bir tanesini geri eklemek index-two unit subgroup'unu bütün ambient
unit group'a tamamlar; singular ideal zaten tamdır. Böylece $M_n$, $n\ge2$
için ambient içinde maximal proper submonoid'dir.

## Cardinality ve rank katmanları

$1\le r<n$ ranklı unsigned transformation sayısı

\[
\binom nr r!\,S(n,r)
\]

olur; burada $S(n,r)$ ikinci tür Stirling sayısıdır. Her domain sütununun
bağımsız sign'ı olduğundan

\[
\boxed{|M_{n,r}|=2^n\binom nr r!\,S(n,r)},
\qquad 1\le r<n.
\]

Unit katmanında yalnız even permutation'lar kalır:

\[
\boxed{|M_{n,n}|=2^{n-1}n!}.
\]

Toplam:

\[
\boxed{|M_n|=(2n)^n-2^{n-1}n!}.
\]

Exact küçük-boyut tablosu:

| $n$ | Ambient | $|M_n|$ | Atılan odd unit | Rank katmanları | Min. right-action image |
|---:|---:|---:|---:|---|---:|
| 2 | 16 | 12 | 4 | 8, 4 | 4 |
| 3 | 216 | 192 | 24 | 24, 144, 24 | 6 |
| 4 | 4.096 | 3.904 | 192 | 64, 1.344, 2.304, 192 | 8 |
| 5 | 100.000 | 98.080 | 1.920 | 160, 9.600, 48.000, 38.400, 1.920 | 10 |
| 6 | 2.985.984 | 2.962.944 | 23.040 | 384, 59.520, 691.200, 1.497.600, 691.200, 23.040 | 12 |

$n=3$ satırı, source matris oracle'ından bağımsız tuple enumeration ile literal
192-state set'e birebir eşit çıktı.

## General action formülleri

$p\in M_n$ ve $\operatorname{rank}(p)=r<n$ olsun.

Sağ-regular action image'i

\[
M_n p=\{xp:x\in M_n\}
\]

$x$'in yalnız $p$ range'indeki $r$ sütununu korur. Her signed $r$-column
assignment singular bir full state'e tamamlanabildiği için

\[
\boxed{|M_n p|=(2n)^r}.
\]

Ters yönde

\[
pM_n=\{px:x\in M_n\}
\]

sonucunun her sütunu $p$'nin $2r$ signed image değerinden birini seçer. Rankı
$r<n$ olan bir section iç state'i singular tuttuğu için bütün seçimler
erişilebilir:

\[
\boxed{|pM_n|=(2r)^n}.
\]

Bu iki image'in kendi rank katmanları da kapalı formdadır. $1\le s\le r<n$
için

\[
\boxed{
|\{z\in M_np:\operatorname{rank}(z)=s\}|
=2^r(n)_sS(r,s)
}
\]

ve

\[
\boxed{
|\{z\in pM_n:\operatorname{rank}(z)=s\}|
=2^n(r)_sS(n,s)
}.
\]

Burada $(m)_s=m!/(m-s)!$ falling factorial'dır. İlk formül retained $r$
sütunun $n$ target içinden $s$ tanesine onto gitmesini; ikincisi $n$ output
sütununun $p$ image'indeki $r$ target'tan $s$ tanesini kullanmasını sayar.
Katmanları toplamak sırasıyla $(2n)^r$ ve $(2r)^n$ total'larını geri verir.

Rank $n$'de $p$ unit'tir; iki multiplication da $M_n$ üzerinde permutation ve
iki image de $|M_n|$ boyutundadır.

Tuple product ayrıca tam kernel'i verir. $I(p)$, $p$'nin unsigned image sütun
kümesi ise

\[
\boxed{xp=yp\iff x_i=y_i\text{ bütün }i\in I(p)\text{ için}}.
\]

Minimum rank 1 olduğundan minimum image

\[
\boxed{2n}
\]

ve rank-0/universal kernel yoktur. Bu nedenle hiçbir $M_n$ right-regular
automaton'ında reset word yoktur.

Sol translation tarafındaki minimum ise rank-1 formülünden

\[
\min_p|pM_n|=2^n.
\]

$n=2$ için iki floor da 4'tür; $n\ge3$ için $2n<2^n$, yani right action daha
fazla sıkıştırır ama yine tek state'e inemez.

## Projection fiber'larında parity scar

Sabit $r<n$ sütunu gözlediğimizi düşünelim. Toplam $(2n)^r$ signed partial
output vardır.

### Partial absolute map collision içeriyorsa

State zaten singular'dır; kalan sütunlar serbesttir:

\[
F_{\mathrm{collision}}=(2n)^{n-r}.
\]

### Partial absolute map injective ve en az iki sütun eksikse

Ambient completion'ların yarısı even, yarısı odd permutation unit completion
olur. Odd olanlar çıkarılır:

\[
F_{\mathrm{injective}}
=(2n)^{n-r}-2^{n-r-1}(n-r)!,
\qquad n-r\ge2.
\]

### Yalnız bir sütun eksikse

Unique absolute completion'ın parity'si partial pattern tarafından belirlenir:

- even completion: fiber $2n$;
- odd completion: fiber $2n-2$.

$n=3,r=2$ özel durumu tam önceki parity scar'dır:

\[
24\text{ output}\times6
+12\text{ output}\times4
=192.
\]

$n=4$ exact enumeration yeni katmanları doğrular:

| Retained rank | Projection fiber profili | $|M_4p|$ | $|pM_4|$ |
|---:|---|---:|---:|
| 1 | $8\times488$ | 8 | 16 |
| 2 | $48\times60+16\times64$ | 64 | 256 |
| 3 | $96\times6+416\times8$ | 512 | 1.296 |
| 4 | $3.904\times1$ | 3.904 | 3.904 |

## $n=2$ edge case

$n=2$'de tek bir retained sütun aynı zamanda $n-1$ sütundur. A fixed-column
partial injection'ın unique completion'ı bazen even, bazen odd olduğu için root
fibers uniform değildir:

\[
2\text{ output}\times4
+2\text{ output}\times2
=12.
\]

Bu nedenle $n=3$'teki “her root value tam 32 state'te görünür” simetrisini
$n=2$'ye körlemesine taşımak yanlış olur.

$n\ge3$ için tek retained sütunun arkasında en az iki gizli sütun kalır ve
bütün $2n$ root fiber'ı yeniden uniform olur:

\[
\boxed{
F_{\mathrm{root}}
=(2n)^{n-1}-2^{n-2}(n-1)!
=\frac{|M_n|}{2n}
}.
\]

## Doğrulama

Default çalışma:

- $n=2,3,4$ state set'lerini gerçekten materialize eder;
- cardinality ve bütün rank-layer formüllerini karşılaştırır;
- her retained rank için projection fiber'larını sayar;
- birer witness $p$ üzerinden $|M_n p|$, $|pM_n|$, bunların rank katmanları ve kernel/projection
  bijection'ını exhaustive doğrular;
- abstract $M_3$ set'ini certified chiral state set ile karşılaştırır.

`--deep-check` ayrıca ambient $n=2$ ve $n=3$ üzerinde toplam
$256+46{,}656$ product için $\chi(xy)=\chi(x)\chi(y)$ eşitliğini denetler.

**Algebraically proved:** karakter kapanışı, cardinality/rank formülleri,
projection fiber sayımları, left/right image formülleri ve no-reset sonucu.

**Computationally enumerated:** $n\le4$ profilleri ile literal $n=3$ chiral
bridge.

**Açıkça iddia edilmeyen:** $n\ne3$ için source non-associative multiplication,
uygun generator seti, fiziksel metaspace veya aynı rank-weather dinamiği.
