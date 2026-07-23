# Shadow Root Seams

`shadow_root_seams.py`, güçlü kök kontratının altı boyutlu minimal uzantılarda
hangi çarpımları gerçekten zorladığını ve hangi **dikişi** serbest bıraktığını
inceler.

Kaynak cebir yine

\[
A=\operatorname{span}_{\mathbb R}\{1,h,q\},\qquad
h^2=q,\quad hq=1,\quad qh=-1,\quad q^2=q
\]

ve kök kontratı

\[
s^2=h,\qquad L_s^2=L_h,\qquad R_s^2=R_h
\]

olsun. `shadow_root_clock.py` içindeki seyrek witness ayrıca

\[
sq=qs
\]

seçiyordu. Bu son eşitlik güçlü kök aksiyomlarının sonucu değildir; kök
uzantıları uzayında özel bir **simetrik dikiş** seçimidir.

## Çalıştırma

```powershell
python experiments/shadow_root_seams.py report --example clock --max-leaves 10
python experiments/shadow_root_seams.py report --example parity --max-leaves 10
python experiments/shadow_root_seams.py report --example exceptional-plus --max-leaves 10
python experiments/shadow_root_seams.py report --example clock-tt-one --max-leaves 10
python experiments/shadow_root_seams.py test
python experiments/shadow_root_seams.py test --deep
```

Hazır örnekler:

- `clock`: eski seyrek saatin simetrik dikişi;
- `parity`: \(\mathbb Z_2\)-grading'i koruyan fakat `sq != qs` olan rasyonel dikiş;
- `generic`: grading zorunluluğu taşımayan açık-dal örneği;
- `exceptional-plus`, `exceptional-minus`: açık dalın dışında kalan iki reel dikiş;
- `clock-tt-one`: aynı clock dikişinde ilk serbest completion hücresi `t*t=1`.

## Kanonik altı zincir

Minimal-boyut kanıtındaki

\[
t:=sh=hs
\]

ile

\[
W=\operatorname{span}\{1,s,h,t,q\}
\]

beş boyutludur. Şimdi

\[
u:=qs
\]

seçelim. Eğer \(u\in W\) olsaydı, \(R_s\) bu beş boyutlu uzay üzerinde

\[
1\mapsto s\mapsto h\mapsto t\mapsto q\mapsto u,
\qquad R_su=-1
\]

zincirini kapatırdı. Beş-boyut engelindeki aynı katsayı eliminasyonu reel bir
sayı için \(a_4^6=-1\) üretir. Dolayısıyla \(u\notin W\) ve her minimal 6B
uzantıda

\[
(1,s,h,t,q,u)
\]

kanonik bir basis'tir. Bu basis'te sağ kök operatörü tamamen sabittir:

\[
R_s:1\to s\to h\to t\to q\to u\to-1.
\]

## Sol dikiş denklemi

Serbest kalan iki kök çarpımını

\[
a:=sq=\sum_{j=0}^{5}c_j e_j,\qquad d:=su
\]

yazalım; burada \((e_0,\ldots,e_5)=(1,s,h,t,q,u)\). Sol kök operatörü

\[
L_s:(1,s,h,t,q,u)\mapsto(s,h,t,q,a,d)
\]

olur. Kontratın `q` üzerindeki tek yeni koşulu

\[
L_s^2q=hq=1
\]

yani

\[
L_s(a)=1
\]

denklemidir.

### Açık dal: \(c_5\ne0\)

Bu durumda \(a\) tamamen serbesttir ve `d` tek olarak zorlanır:

\[
d=\frac{1-c_0s-c_1h-c_2t-c_3q-c_4a}{c_5}.
\]

Dolayısıyla kök-operator iskeletinin bu dalı altı parametrelidir. Eski clock

\[
a=u,\qquad d=1
\]

noktasıdır.

### İstisnai dal: \(c_5=0\)

Bu kez `d` denklemden tamamen düşer. Kalan katsayı denklemleri

\[
c_4^6=1
\]

verir. Reel sayılar üzerinde yalnız iki `a` mümkündür:

\[
a_+=1-s+h-t+q,
\]

\[
a_-=-(1+s+h+t+q).
\]

Her iki noktada da \(d\in B\) keyfîdir. Yani istisnai kısım iki ayrı altı
boyutlu daldan oluşur.

Bu ayrışım yalnız küçük katsayılı arama sonucu değildir; `L_s(a)=1`
denklemindeki altı koordinatın doğrudan eliminasyonudur.

## Completion uzayının boyutu

Kök iskeleti, birim, kaynak \(A\) tablosu, `s` satır/sütunu ve bunların
kareleri olan `h` satır/sütununu belirler. Geriye

\[
qt,\ qu,\ tq,\ uq,\ tt,\ tu,\ ut,\ uu
\]

olmak üzere sekiz adet serbest \(B\)-değerli hücre kalır. Bu yüzden:

| Uzay | Kök dikişi | Completion | Toplam |
|---|---:|---:|---:|
| Grading'siz | 6 | \(8\cdot6=48\) | 54 |
| \(\mathbb Z_2\)-graded | 3 | \(8\cdot3=24\) | 27 |

Graded durumda `a=sq` odd olmalıdır. Açık dal

\[
a=c_1s+c_3t+c_5u,\qquad c_5\ne0
\]

şeklinde üç parametre taşır ve zorlanan `d=su` otomatik olarak even'dır.
İki istisnai `a` hem even hem odd koordinatlar içerdiği için grading'i korumaz.

Buradaki boyutlar, seçilen kanonik basis içindeki **table parameter space**
boyutlarıdır. İzomorfizma sınıflarının quotient boyutu veya bütün automorphism
orbitlerinin sınıflandırması oldukları iddia edilmez.

## Beşinci yaprak dikişi okur

Tekrarlanan `s` Catalan ağaçları ilk dört derecede bütün güçlü kök
uzantılarında zorunlu olarak birleşir:

\[
s,\quad h,\quad t,\quad q.
\]

Beş yaprakta 14 ağacın top-level parçalanmaları exact olarak

\[
5+2=7
\]

sol dikiş sonucu `a=sq` ve

\[
2+5=7
\]

sağ dikiş sonucu `u=qs` üretir:

\[
\boxed{\operatorname{Hist}_5=\{a:7,\ u:7\}}.
\]

Bu nedenle:

- `sq != qs` ise ilk bracket shock **beşinci** derecededir;
- yalnız simetrik dikişte `a=u`, 14 ağacın tamamı `u` olur;
- eski clock'un ilk shock'ı altıncı dereceye ertelemesi güçlü kök kontratının
  genel sonucu değil, simetrik dikişin ek bir rijitliğidir.

`clock` örneği yeniden

```text
n=5  u:14
n=6  -1:19  0:4  +1:19
```

verir. Parity-preserving fakat asimetrik örnek

\[
sq=s-t+2u,\qquad su=\tfrac12(1-h+q)
\]

için ise

```text
n=5  (s-t+2u):7  u:7
```

olur. Bu beşinci-derece histogramı serbest completion hücrelerinin hiçbirine
dokunmadan kök dikişini doğrudan tomografi eder.

## Script'in doğruladığı sınır

Default test:

- bütün hazır örneklerde kaynak `A` tablosunu;
- `s*s=h`, `L_s^2=L_h`, `R_s^2=R_h` eşitliklerini;
- beşinci-derece `7+7` dikiş yasasını;
- `clock` tablosunun `shadow_root_clock.py` ile basis permütasyonu altında
  hücre-hücre aynı olduğunu;
- clock'un altıncı-derece `19+4+19` histogramını

exact rasyonel aritmetik ile denetler.

`--deep` ayrıca 972 küçük tam-katsayılı açık-dal dikişini, iki istisnai dalda
26 farklı `d` seçimini ve bütün hazır örneklerin 12 yaprağa kadar Catalan
ledger'ını sınar.

İddia edilmeyenler:

- 54-parametreli tabloların izomorfizma sınıflandırması;
- her completion'ın birbirinden izomorfik olmadığı;
- full automorphism gruplarının hesabı;
- bu familyanın ordinary `s^2=h` universal adjunction ile aynı nesne olduğu.
