# Shadow Root Clock

`shadow_root_clock.py`, kaynak cebirde bulunmayan

\[
s^2=h
\]

karekökünü yalnız element düzeyinde eklemekle yetinmeyen bir uzantı kurar. Yeni
elementin sol ve sağ regular operatörleri de gerçekten karekök olsun ister:

\[
L_s^2=L_h,\qquad R_s^2=R_h.
\]

Bu üç koşul birlikte ele alındığında en küçük sonlu boyut **6** olur. Script,
altı boyutlu açık bir çarpım tablosunu, alt-boyut imkânsızlık sertifikasını,
operator grubunu ve tekrar eden `s` ağaçlarının tam Catalan ekolojisini birlikte
taşır.

## Çalıştırma

```powershell
python experiments/shadow_root_clock.py
python experiments/shadow_root_clock.py table
python experiments/shadow_root_clock.py report --max-leaves 12 --json
python experiments/shadow_root_clock.py ecology --max-leaves 18
python experiments/shadow_root_clock.py test
python experiments/shadow_root_clock.py test --deep
```

`--deep`, üretilen 384 operator state'inin bütün

\[
384^2=147456
\]

ikili çarpımını ayrıca denetler.

## Başlangıç cebiri ve kolay karekök engeli

Kaynak cebir

\[
A=\operatorname{span}_{\mathbb R}\{1,h,q\}
\]

üzerinde

\[
h^2=q,\qquad q^2=q,\qquad hq=1,\qquad qh=-1
\]

kuralları geçerlidir. Eğer $s=a+bh+cq\in A$ olsaydı,

\[
s^2=a^2+2ab\,h+(2ac+b^2+c^2)q
\]

olurdu. $s^2=h$, aynı anda $a^2=0$ ve $2ab=1$ ister; reel sayılarda
bu mümkün değildir.

Sadece `s*s=h` isteyen dört boyutlu bir uzantı yazmak kolaydır: yeni `s` ile
diğer bütün tanımsız çarpımları sıfır seçmek yeterlidir. Buradaki mesele bu
değil. Güçlü root kontratı, **bütün uzantı üzerinde**

\[
s(sx)=hx,\qquad (xs)s=xh
\]

olmasını ister.

## Neden 4 veya 5 boyut yetmiyor?

Sonlu boyutlu reel, unital bir $B\supset A$ uzantısında, $A$ ve $B$ aynı
birimi paylaşırken güçlü kontratı sağlayan bir $s\in B$ bulunduğunu varsayalım.

Önce $L_s^2(s)=L_h(s)$ eşitliği

\[
s\,(ss)=hs
\]

verir. $s^2=h$ olduğundan bu doğrudan

\[
sh=hs
\]

olur. Ortak değere $x$ diyelim. Sol ve sağ kare eşitliklerini sırayla
$h$'ye uygularsak

\[
sx=q,\qquad xs=q
\]

elde edilir. Böylece iki regular operator de aynı zincirin ilk dört okunu
izler:

\[
1\longmapsto s\longmapsto h\longmapsto x\longmapsto q.
\]

Fakat zincirin `q` kuyruğu kiraldir:

\[
L_s^2(q)=h q=1,
\qquad
R_s^2(q)=q h=-1.
\]

### Bağımsızlık adımı

$1,s,h,q$ bağımsızdır; aksi halde $s\in A$ olurdu. Şimdi

\[
x=a1+bs+ch+dq
\]

varsayalım. `L_s(x)=R_s(x)=q` eşitliklerini çıkarınca iki durum doğar:

- $d\ne0$ ise $y:=L_s(q)=R_s(q)$ ve yukarıdaki denklemden

  \[
  y=\frac{q-as-bh-cx}{d}\in W:=\operatorname{span}\{1,s,h,q\}.
  \]

  İki operator $W$ basis'i üzerinde aynı okları taşır:
  $1\mapsto s$, $s\mapsto h$, $h\mapsto x$, $q\mapsto y$. Dolayısıyla
  $W$ üzerinde aynı lineer map'tir ve özellikle $L_s(y)=R_s(y)$ olmalıdır.
  Oysa $L_s(y)=L_s^2(q)=1$ ve $R_s(y)=R_s^2(q)=-1$.
- $d=0$ ise $x=a1+bs+ch$ ve `L_s(x)=q` eşitliği $q$'yu
  \(\operatorname{span}\{1,s,h\}\) içine zorlar.

Dolayısıyla

\[
1,s,h,x,q
\]

beşlisi lineer bağımsızdır. Boyut en az 5'tir.

### Beşinci boyuttaki işaret polinomu

Boyut tam 5 olsaydı bu zincir bir basis olurdu:

\[
v_0=1,\ v_1=s,\ v_2=h,\ v_3=x,\ v_4=q.
\]

$U=R_s$ için

\[
Uv_i=v_{i+1}\quad(0\le i<4)
\]

ve $U^2v_4=-v_0$ gerekir. Son kolu

\[
Uv_4=\sum_{i=0}^4 a_i v_i
\]

yazıp bir kez daha $U$ uygulamak katsayı zincirini verir:

\[
a_4a_0=-1,
\quad a_0+a_4a_1=0,
\quad a_1+a_4a_2=0,
\quad a_2+a_4a_3=0,
\quad a_3+a_4^2=0.
\]

Eliminasyonun son izi

\[
\boxed{a_4^6=-1}
\]

olur. Reel $a_4$ için sol taraf negatif olamaz. Böylece boyut 5 de
imkânsızdır ve

\[
\boxed{\dim_{\mathbb R}B\ge6}
\]

kanıtlanır.

Bu alt sınır yalnız script'in küçük katsayılı aramasına dayanmaz; tüm reel
sonlu-boyutlu unital non-associative uzantılar için lineer-cebirsel bir
sertifikadır.

## Altı boyutlu witness

Basis'i

\[
(1,h,q\mid s,t,u)
\]

seçelim. İlk üç vektör kaynak cebirdir; son üçü shadow kanalıdır. Script'in
kullandığı seyrek tablo:

| \(\cdot\) | 1 | h | q | s | t | u |
|---|---:|---:|---:|---:|---:|---:|
| **1** | 1 | h | q | s | t | u |
| **h** | h | q | 1 | t | u | s |
| **q** | q | -1 | q | u | 0 | 0 |
| **s** | s | t | u | h | q | 1 |
| **t** | t | u | 0 | q | 0 | 0 |
| **u** | u | -s | 0 | -1 | 0 | 0 |

Tanımsız bırakılmış yeni-yeni çarpımlar sıfır seçilmiştir. Bu seçim bir
**seyrek completion witness**'ıdır; bütün minimal uzantıların sınıflandırması
veya tekliği değildir.

Sol `s` hareketi pozitif bir altılı saattir:

\[
1\to s\to h\to t\to q\to u\to1.
\]

Sağ hareket aynı saati son dikişte ters çevirir:

\[
1\to s\to h\to t\to q\to u\to-1.
\]

Bundan exact olarak

\[
L_s^6=I,\qquad R_s^6=-I,\qquad R_s^{12}=I
\]

ve

\[
L_s^2=L_h,\qquad R_s^2=R_h
\]

çıkar. Ayrıca bütün basis $s$'den bracket'lı ifadelerle üretilir:

\[
h=s^2,\quad q=h^2,\quad t=sh,\quad u=sq,\quad 1=hq.
\]

## Determinant engeli nasıl dengelendi?

Kaynak üç-boyutlu core üzerinde

\[
\det(R_h|_A)=-1
\]

olduğu için reel bir operator karesi olamazdı. Shadow kanalı üzerinde de

\[
s\mapsto t\mapsto u\mapsto-s
\]

ve dolayısıyla

\[
\det(R_h|_{\mathrm{shadow}})=-1
\]

olur. İki orientation reversal çarpışınca tam uzayda

\[
\det(R_h)=(-1)(-1)=+1=\det(R_s)^2
\]

elde edilir. Sol tarafta core ve shadow determinantlarının ikisi de $+1$'dir.

Bu, “ek boyut determinantı sihirle düzeltir” demekten daha keskin bir resimdir:
sağ-kiralitenin tek eksi işareti, ikinci bir eksi işaret taşıyan üç-boyutlu
shadow çevrimiyle çiftlenmiştir.

## Nilpotent kiralite izleri

Sol ve sağ root operatorleri yalnız `u` girdisinde ayrılır:

\[
(L_s-R_s)u=2\cdot1.
\]

Bu nedenle

\[
\operatorname{rank}(L_s-R_s)=1,
\qquad
(L_s-R_s)^2=0.
\]

Karesi alınmış $h$-seviyesinde iki kanal görünür:

\[
(L_h-R_h)q=2\cdot1,
\qquad
(L_h-R_h)u=2s,
\]

dolayısıyla rank 2'dir; bu defect de karesi sıfırdır. Karekök, eski kiraliteyi
yok etmez; onu bir root kanalı ve onun shadow eşine ayırır.

## Cebirsel rijitlik profili

Altı-boyutlu table üzerinde bütün basis üçlülerinden kurulan exact lineer
constraint sistemleri şu profili verir:

\[
N_\ell(B)=N_m(B)=N_r(B)=\mathbb R1,
\]

\[
\operatorname{Comm}(B)=\operatorname{span}\{1,t\},
\qquad
Z(B)=\mathbb R1.
\]

`t`, bütün basis elemanlarıyla commute eder fakat nucleus'ta değildir; yani
commutativity ile associativity defect'i yine ayrışır.

Associator flattening

\[
B^{\otimes3}\longrightarrow B
\]

tam image'e sahiptir:

\[
\operatorname{rank}=6,
\qquad
\dim\ker=6^3-6=210.
\]

Leibniz denklemlerinin 36 bilinmeyenli exact sistemi full ranktır:

\[
\operatorname{Der}(B)=0.
\]

Son olarak script, birim vektörünü sabit tutan bütün 3840 signed-basis
permütasyonunu tüketir. Bunlardan yalnız ikisi automorphism'dir:

\[
\mathrm{id},
\qquad
(s,t,u)\mapsto(-s,-t,-u).
\]

Bu son cümle yalnız **signed-basis automorphism** sınıfı içinde exacttır; bütün
reel lineer automorphism grubunun sınıflandırıldığı iddia edilmez.

## 384 durumlu clock group

$P=L_s$ ve $Q=R_s$ signed-permutation operatorleridir. `Q`, `P`'den yalnız
bir coordinate sign flip ile ayrılır:

\[
P^{-1}Q=D_u.
\]

$D_u$'yu altılı çevrimle conjugate etmek altı bağımsız coordinate flip'ini
üretir. Bu yüzden

\[
\langle L_s,R_s\rangle
\cong C_2^6\rtimes C_6
\cong C_2\wr C_6
\]

ve grup mertebesi

\[
2^6\cdot6=384
\]

olur. Deterministic `L<R` shortlex BFS profili:

```text
1, 2, 4, 8, 16, 32, 63, 62, 60, 56, 48, 32
```

Maksimum minimal kelime derinliği 11'dir. Element order histogramı:

| Order | State |
|---:|---:|
| 1 | 1 |
| 2 | 71 |
| 3 | 32 |
| 4 | 56 |
| 6 | 160 |
| 12 | 64 |

## Tekrarlanan `s` ağaçları

İlk beş derecede bütün Catalan ağaçları aynı sonucu verir:

| Yaprak | Catalan ağaç | Tek sonuç |
|---:|---:|---:|
| 1 | 1 | s |
| 2 | 1 | h |
| 3 | 2 | t |
| 4 | 5 | q |
| 5 | 14 | u |

İlk bracket shock altıncı derecede gelir:

\[
42=19+4+19
\]

ve histogram

```text
-1:19  0:4  +1:19
```

olur. İki uç comb, shadow saatinin kiralitesini doğrudan gösterir:

```text
left  comb: s -> h -> t -> q -> u -> -1 -> -s -> ...
right comb: s -> h -> t -> q -> u -> +1 -> +s -> ...
```

Yani $s^2=h$ ilk beş derece boyunca beklenmedik biçimde bracket-kör görünür;
altıncı contraction'da sol ve sağ saatlerin dikişi açılır.

## Kanıtlanan ve açık kalan

Exact olarak kanıtlanan/doğrulanan:

- güçlü iki-taraflı root uzantısının reel minimal boyutu 6;
- açık altı-boyutlu multiplication table;
- kaynak $A$'nın unital subalgebra olarak korunması;
- $s^2=h$, $L_s^2=L_h$, $R_s^2=R_h$;
- operator periyotları, determinant ledger'ı ve nilpotent defect rankları;
- üç nucleus, commutant, center, associator image ve derivation space;
- unit-fixing signed-basis permutationları içindeki iki automorphism;
- 384-state clock group ve shortlex profili;
- seçilen table için tekrarlanan `s` Catalan histogramları.

İddia edilmeyenler:

- bu sparse table'ın tek veya universal minimal uzantı olduğu;
- bütün 6B completion'ların sınıflandırıldığı;
- ordinary square-root adjunction'ın sonlu-boyutlu universal nesnesi olduğu;
- power-associativity veya fiziksel “shadow dimension” yorumu.

Universal non-associative $s^2=h$ adjunction çok daha büyük bir sorudur:
serbest bracket ağaçlarını da taşır ve bu sonlu clock witness'ıyla
özdeşleştirilmemelidir.
