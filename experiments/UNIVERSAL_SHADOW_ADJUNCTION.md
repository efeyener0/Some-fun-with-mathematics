# Universal Shadow Adjunction

`universal_shadow_adjunction.py`, kaynak cebir

\[
A=\operatorname{span}_{\mathbb R}\{1,h,q\},
\qquad
h^2=q,\quad hq=1,\quad qh=-1,\quad q^2=q
\]

içine yeni bir `s` koyup yalnız

\[
s^2=h
\]

bağıntısını dayatan universal non-associative uzantıyı açıkça kurar.

Bu nesne, `shadow_root_clock.py` içindeki altı-boyutlu cebir değildir. Universal
nesne sonsuz boyutludur; 6B clock onun çok sayıda ek bağıntı taşıyan surjective
bir quotient'ıdır.

## Çalıştırma

```powershell
python experiments/universal_shadow_adjunction.py
python experiments/universal_shadow_adjunction.py report --growth-leaves 12 --json
python experiments/universal_shadow_adjunction.py test
python experiments/universal_shadow_adjunction.py test --deep
```

Harici paket gerekmez. Script exact integer ve `Fraction` hesapları kullanır.
Python runtime sertifikayı rational altalan üzerinde yürütür; universal cebirin
katsayı alanı \(\mathbb R\)'dir.

Doğrulanan mevcut baseline:

```text
default:  15,764 raw trees,  26,229 one-step branches
deep:    187,796 raw trees, 373,877 one-step branches
presentation SHA-256:
4b79988e7d0b47baf108fb17d9a5b72eac74239cb5b397452b0a9579d9971868
```

İki bağımsız default JSON üretimi byte-içeriği düzeyinde aynı çıktı. Ölçülen
canonical JSON SHA-256 değeri:

```text
04578cff4114e33bc06219f86f207553bfdbc7306488f2246357bd9bc198e373
```

Presentation fingerprint bir drift alarmıdır; confluence kanıtının yerine
geçmez.

## 1. Universal sorunun kesin kapsamı

Bir obje şu verilerden oluşur:

1. reel, bilinear çarpımlı, unital ve associativity varsayılmayan bir \(B\);
2. aynı birimi koruyan injective bir cebir homomorfizması
   \(j:A\hookrightarrow B\);
3. \(b\in B\) ve \(b^2=j(h)\).

Bir morfizm \(\phi:(B,j,b)\to(C,k,c)\),

\[
\phi\circ j=k,
\qquad
\phi(b)=c
\]

koşullarını sağlayan unital reel-cebir homomorfizmasıdır. Morfizmin bütün
\(B\) üzerinde injective olması istenmez. Bu son ayrıntı önemlidir: universal
nesnenin sonlu clock'a giden map'i bir quotient map'idir.

Aranan \((U,i,s)\), her \((B,j,b)\) için tam bir tane böyle \(U\to B\) map'i
olan objedir.

Burada yalnız element bağıntısı \(s^2=h\) istenir. Şunlar universal
presentation'ın parçası değildir:

\[
L_s^2=L_h,\qquad R_s^2=R_h,\qquad sh=hs,\qquad sq=qs.
\]

## 2. Bracket-tree construction

\(\mathcal T\), leaf alphabet'i

\[
\{1,h,q,s\}
\]

olan bütün sonlu ordered full binary tree'lerin kümesi olsun. Bir iç node
parenthesized product'tır. Örneğin

\[
((hs)s),\qquad h(ss),\qquad s(sq)
\]

üç farklı tree'dir. Tree construction hiçbir reassociation yapmaz.

Önce \(\mathcal T\)'yi baz alan serbest reel vektör uzayını alıp çarpımı iki
tree'yi yeni bir root altında graft ederek tanımlarız. Sonra aşağıdaki
bağıntıların ürettiği two-sided algebra ideal'iyle quotient alırız:

\[
1x\to x,\qquad x1\to x,
\]

\[
hh\to q,\qquad hq\to1,\qquad qh\to-1,\qquad qq\to q,
\]

\[
ss\to h.
\]

İlk satırdaki \(x\), keyfi bir bracket tree'dir. Yani `1` yalnız generator
leaf'leri üzerinde değil, bütün oluşmuş ifadeler üzerinde ortak two-sided
unit'tir.

Sonuç:

\[
U=\mathbb R\{1,h,q,s\}_{\mathrm{nonassoc}}/I.
\]

## 3. Termination ve confluence

### 3.1 Termination

Her kural toplam leaf sayısını tam bir azaltır. `qh -> -1` kuralındaki eksi
işareti tree ölçüsünü etkilemez. Dolayısıyla sonsuz rewrite zinciri yoktur.

Lineer kombinasyonlar monomial bazında normalize edilir; sonlu bir
polynomial'daki tree ölçülerinin multiset'i de her adımda kesin azalır.

### 3.2 Kritik overlap'lar

Yedi kural left-linear first-order tree rule olarak tarandığında:

- iki ordered root overlap;
- bunların tek bir symmetry-free overlap sınıfı;
- sıfır proper non-variable overlap

çıkar. Tek gerçek root peak:

\[
1\cdot1
\overset{1x\to x}{\longrightarrow}1,
\qquad
1\cdot1
\overset{x1\to x}{\longrightarrow}1.
\]

İki kalan overlap türü de bütün boyutlar için schema düzeyinde kapanır:

1. **Unit-variable overlap.** `1*x` veya `x*1` içindeki `x` önce
   indirgenebilir. Önce unit'i silmek, ardından `x`'i indirgemek ile önce
   `x`'i indirgemek, ardından unit'i silmek aynı tree'yi ve aynı scalar
   katsayıyı verir.
2. **Disjoint overlap.** Ayrı subtreelerdeki iki redex birbirinin context'ine
   dokunmaz. Her iki sıra aynı tree'ye gider; olası \(-1\) katsayıları reel
   scalar oldukları için commute eder.

Diğer beş kuralın iki child'ı da atomiktir; bunların altında nested
non-variable redex bulunamaz. Termination ile bu local joinability birlikte
her tree'nin tek bir signed normal form'u olduğunu verir.

Script bu analitik sınıflandırmayı hard-code etmez: rule pattern'lerini
rename-apart unification ile tarar ve overlap'ı türetir. Bounded exhaustive
test bunun yanında her raw tree için:

- root-first/left-first stratejiyi;
- en son redex'i seçen ters stratejiyi;
- bottom-up normalizer'ı;
- mümkün olan her ilk rewrite dalını

aynı signed irreducible üzerinde karşılaştırır.

### 3.3 Normal-form basis neden gerçekten bazdır?

Bir tree'nin unique signed irreducible sonucunu \(N(t)\), bunu reel-lineer
uzatarak elde edilen map'i de \(N\) ile gösterelim.

Her rewrite relation \(N\) altında sıfıra gider; dolayısıyla presentation
ideal'i \(I\subseteq\ker N\)'dir. Ters yönde, her tree için gerçek reduction
zinciri

\[
t-N(t)\in I
\]

verir. Lineer uzatınca her polynomial \(p\) için

\[
p-N(p)\in I.
\]

Eğer \(N(p)=0\) ise \(p\in I\); yani \(\ker N\subseteq I\). Böylece

\[
I=\ker N
\]

ve irreducible tree'ler \(U\)'nun reel vektör-uzayı bazıdır. Confluence burada
yalnız bir evaluation algoritması değil, quotient'ta gizli lineer bağıntı
kalmadığının sertifikasıdır.

## 4. Kaynak cebir neden injective kalıyor?

`1`, `h` ve `q` üç farklı singleton irreducible'dır. Normal-form basis
teoremine göre

\[
a1+bh+cq=0\quad\text{in }U
\]

yalnız \(a=b=c=0\) iken mümkündür. Dolayısıyla doğal map

\[
i:A\hookrightarrow U
\]

injective'dir. Rewrite table aynı zamanda \(A\)'nın dokuz basis çarpımını ve
ortak unit'i exact korur.

Bu, yalnız clock evaluation'a dayanmaz. Clock quotient enjeksiyon için ek bir
model verir, fakat asıl neden normal-form basis'tir.

## 5. Sonsuz boyut

Her \(n\ge1\) için sol comb

\[
w_n=(((h s)s)\cdots s)
\]

tanımlansın; burada \(n\) tane `s` vardır. İlk cherry `h*s` olduğu için
reducible değildir. Sonraki her root'un sol child'ı bir subtree, sağ child'ı
`s` olduğundan hiçbir yeni rule oluşmaz.

Bu nedenle bütün \(w_n\)'ler irreducible'dır. Leaf sayıları \(n+1\) olduğu
için birbirlerinden farklı baz elemanlarıdır:

\[
\dim_{\mathbb R}U=\infty.
\]

Bu aynı zamanda altı-boyutlu clock ile universal adjunction'ın özdeş
olamayacağının ilk kaba göstergesidir.

## 6. Leaf-size büyümesi

\(b_n\), yalnız `h,q,s` leaf'lerini kullanan, leaf-size \(n\) olan irreducible
tree sayısı olsun. Multi-leaf irreducible içinde `1` bulunamaz; `1` bulunduğu
anda parent node bir unit redex olur.

İki irreducible subtree'yi graft etmek yalnız size 2'de şu beş cherry'yi
üretince yasaktır:

\[
hh,\ hq,\ qh,\ qq,\ ss.
\]

Dolayısıyla

\[
b_1=3,\qquad b_2=4,
\]

ve \(n\ge3\) için

\[
b_n=\sum_{i=1}^{n-1}b_i b_{n-i}.
\]

İlk değerler:

| leaf-size \(n\) | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| \(b_n\) | 3 | 4 | 24 | 160 | 1,152 | 8,768 | 69,504 |
| full \(U\)-basis count | 4 | 4 | 24 | 160 | 1,152 | 8,768 | 69,504 |

Full count'taki tek fark, size 1'de singleton unit `1`'dir.

Generating function

\[
B(z)=\sum_{n\ge1}b_nz^n
\]

için grammar doğrudan

\[
B(z)=3z-5z^2+B(z)^2
\]

verir. Sıfırdaki doğru branch:

\[
B(z)=\frac{1-\sqrt{1-12z+20z^2}}2
=\frac{1-\sqrt{(1-2z)(1-10z)}}2.
\]

Singleton unit dahil normal-form growth series:

\[
U(z)=z+B(z).
\]

Dominant singularity \(\rho=1/10\)'dur ve standart square-root coefficient
asymptotic'i

\[
b_n\sim
\frac{10^n}{\sqrt{20\pi}\,n^{3/2}}
\]

olur. Bu son satır generating function'dan türetilmiş bir katsayı
asymptotic'idir; ek bir runtime doğrulama iddiası değildir.

## 7. Universal map açıkça nasıl oluşuyor?

Her hedef obje \((B,j,b)\) için raw tree evaluation'ı recursive tanımla:

\[
\operatorname{ev}(1)=1_B,
\quad
\operatorname{ev}(h)=j(h),
\quad
\operatorname{ev}(q)=j(q),
\quad
\operatorname{ev}(s)=b,
\]

\[
\operatorname{ev}((xy))
=\operatorname{ev}(x)\operatorname{ev}(y).
\]

Sonra reel-lineer uzat.

Bu map'in yedi relation üzerindeki değerleri sıfırdır:

- iki unit rule, \(1_B\)'nin two-sided unit olmasından;
- dört kaynak rule, \(j\)'nin \(A\)-homomorfizması olmasından;
- `ss -> h`, \(b^2=j(h)\) koşulundan.

Dolayısıyla evaluation quotient üzerinden iyi-tanımlı bir

\[
\overline{\operatorname{ev}}:U\to B
\]

homomorfizmasına iner.

Uniqueness ayrı bir varsayım değildir. `1,h,q,s` görüntüleri koşullar
tarafından zaten sabittir; her product tree'nin görüntüsü homomorfizma
koşuluyla recursively zorlanır; lineer kombinasyonların görüntüsü de
lineerlikle zorlanır. Bu yüzden ikinci bir map seçeneği yoktur.

## 8. Altı-boyutlu clock neden yalnız quotient?

`shadow_root_clock.py` içindeki

\[
C=\operatorname{span}\{1,h,q,s,t,u\}
\]

cebirinde de \(s^2=h\) ve aynı \(A\)-tablosu geçerlidir. Universal property
tek bir evaluation map'i verir:

\[
\pi:U\to C.
\]

Bu map surjective'dir; altı clock basis vektörünün açık preimage'leri:

\[
1\leftarrow1,
\quad h\leftarrow h,
\quad q\leftarrow q,
\quad s\leftarrow s,
\quad t\leftarrow hs,
\quad u\leftarrow qs.
\]

Fakat injective değildir. Universal basis'te `h*s` ile `s*h` farklı
irreducible tree'lerdir; clock'ta ikisi de `t` olur:

\[
0\ne hs-sh\in\ker\pi.
\]

Regular-operator kontratı da clock'un ek kernel bağıntısıdır. Örneğin

\[
s(sq)-hq
\]

\(U\)'da iki farklı irreducible contribution taşıyan nonzero bir elemandır;
clock'ta \(L_s^2(q)=L_h(q)\) nedeniyle sıfıra gider.

Dolayısıyla:

\[
\boxed{
\text{universal }s^2=h\text{ adjunction}
\twoheadrightarrow
\text{6B strong-root clock}
}
\]

ama bu ok bir isomorphism değildir.

Clock initial olsaydı, initial objelerin uniqueness'i gereği \(U\) ile
isomorphic olurdu. Daha somut olarak clock'tan \(U\)'ya `A` ve `s`'yi sabit
tutan bir homomorfizma `hs=sh` clock bağıntısını \(U\)'da da zorlamak zorunda
kalırdı; bu normal-form basis'e aykırıdır.

## 9. Clock evaluation collapse profili

Script, her leaf-size içindeki bütün irreducible basis tree'lerini clock'a
evaluate eder:

| leaf-size | \(U\) basis tree | farklı clock görüntüsü | en büyük fiber | zero var mı? |
|---:|---:|---:|---:|:---:|
| 1 | 4 | 4 | 1 | hayır |
| 2 | 4 | 2 | 2 | hayır |
| 3 | 24 | 7 | 8 | evet |
| 4 | 160 | 13 | 72 | evet |
| 5 | 1,152 | 13 | 608 | evet |
| 6 | 8,768 | 13 | 5,264 | evet |

İlk aynı-degree basis collision leaf-size 2'dedir:

```text
(h*s) -> t
(s*h) -> t
```

İlk irreducible zero-image leaf-size 3'tedir:

```text
((h*s)*q) -> 0
```

Leaf-size 4'ten itibaren görüntü kümesi tam olarak

\[
\{0,\ \pm1,\ \pm h,\ \pm q,\ \pm s,\ \pm t,\ \pm u\}
\]

olur. Bu finite collapse, \(U\)'nun finite-dimensional olduğunu söylemez;
tam tersine, sonsuz normal-form basis'in seçilen finite quotient içinde nasıl
büyük fiber'lara katlandığını ölçer.

## 10. Executable kanıt katmanları

### Default

Default validation:

- yedi rule'un left-linearity ve strict leaf decrease kontrollerini;
- kaynak \(A\)'nın dokuz basis çarpımını;
- `s*s=h` kontratını;
- symbolic critical-overlap derivation'ını;
- exact polynomial multiplication kontratlarını;
- `h*s != s*h` ve explicit nonassociativity witness'ını;
- 6B quotient surjectivity ve iki kernel witness'ını;
- bütün raw tree'leri leaf-size 5'e kadar

çalıştırır.

Raw tree sayısı:

\[
\sum_{n=1}^{5}4^n C_{n-1}=15{,}764.
\]

Bu corpus'ta 26,229 named one-step rewrite dalının tamamı ortak normal form'a
join olur; raw ve normalized tree'nin clock evaluation'ları da eşleşir.

### Deep

`--deep`, exhaustive sınırı leaf-size 6'ya çıkarır:

\[
\sum_{n=1}^{6}4^n C_{n-1}=187{,}796.
\]

373,877 one-step branch join edilir. Ayrıca `ss -> h` kuralını kasıtlı olarak
`ss -> q` yapan deterministic corruption:

- presentation fingerprint tarafından;
- bağımsız 6B clock semantics tarafından

reddedilir.

Bounded enumeration, sonsuz confluence'ın kanıtı değildir. Sonsuz iddia
strict termination + eksiksiz critical-overlap sınıflandırması + schema
joinability argümanından gelir; corpus implementasyonun bu kanıta sadık
olduğunu test eder.

## 11. Kanıtlanan ve iddia edilmeyen

Exact olarak kanıtlanan:

- açık bracket-tree presentation;
- terminating ve confluent signed-monomial rewrite sistemi;
- irreducible tree normal-form basis'i;
- \(A\)'nın common-unit subalgebra olarak injective kalması;
- \(s^2=h\);
- her uygun hedefe unique evaluation homomorfizması;
- \(U\)'nun sonsuz boyutlu olması;
- leaf-size recurrence, generating function ve coefficient asymptotic'i;
- 6B clock'a açık surjective quotient map'i;
- quotient'ın nontrivial kernel'i ve ilk collapse dereceleri.

İddia edilmeyenler:

- \(U\)'nun finite-dimensional olması;
- \(L_s^2=L_h\) veya \(R_s^2=R_h\)'nin \(U\)'da geçerli olması;
- power-associativity;
- 6B clock'un ordinary \(s^2=h\) problemi için universal olması;
- bütün finite quotient'ların sınıflandırılması;
- bütün ideal, automorphism veya representation teorisinin çözülmesi;
- fiziksel bir “shadow time” koordinatının bu algebraic construction'dan tek
  başına çıkması.

Bu construction whitepaper'daki açık adımı dar ama tam anlamıyla kapatır:
“gölge boyut” burada metafor olarak değil, bracket history'yi silmeyen explicit
bir extension objesi olmuştur. Sonlu clock ise bu sonsuz objenin chirality ve
regular-root kontratlarını seçerek kapattığı özel bir finite shadow'dur.
