# Parantezin İçinde Kalan Zaman — Oyuncak Kutusu

[English version](../docs_eng/README.md)

## Kaynak cebir

Bu oyuncak kutusunun çekirdeği, Misteria tarafından sağlanan üç boyutlu
reel, birimli ve non-associative cebirdir:

\[
A=\operatorname{span}_{\mathbb R}\{1,h,q\}.
\]

\(1\) iki-taraflı birimdir; cebiri belirleyen temel çarpımlar

\[
h^2=q,\qquad hq=1,\qquad qh=-1,\qquad q^2=q
\]

şeklindedir. Dolayısıyla çarpım ne commutative ne de associative'dir.
En küçük çıplak associativity witness'ı:

\[
(hh)h=qh=-1,\qquad h(hh)=hq=1,
\]

\[
[h,h,h]=(hh)h-h(hh)=-2.
\]

Aynı tablo belirgin bir sol/sağ kiralite de taşır: \(q\), \(h\)'nin sağ
inverse'i iken \(-q\) sol inverse'idir. Deneylerin parantez ağacı, associator,
operator metaspace, gölge kök ve scheduler katmanları bu küçük fakat
asimetrik çekirdeğin farklı bilgi yüzlerini inceler.

## Kaynak ve araştırma katkısı

Kaynak cebir, başlangıç whitepaper'ı, özgün probe ve interrupt-pet dosyaları ile
projenin temel sezgisi **Misteria tarafından sağlandı**. Bu workspace'teki
`experiments/` araştırma hattı ise, Misteria'nın yaratıcı keşif için verdiği
açık yetki kapsamında **Codex GPT-5.6-Sol tarafından otonom olarak tasarlandı,
uygulandı, çalıştırıldı ve belgelendi**.

Buradaki “otonom” ifadesi katkı kökenini açıklar: araştırma sorularının
türetilmesi, karşı-örneklerin kurulması, exact taramalar, sertifika kontrolleri
ve deney raporları ajan tarafından üretildi. Cebirin ve projenin fikrî
sahipliğini ajana devretmez; kaynak mimari ve araştırma yönünün sahibi
Misteria'dır. Teorem düzeyi sonuçlar, finite exact gözlemler ve açık hipotezler
belgelerde ayrıca ayrıştırılır.

## Oyuncak ve oyun dili

Bu belgelerdeki “oyuncak”, “oyun”, “bahçe”, “hava”, “saat” ve benzeri adlar
çalışmayı hafife alan etiketler değildir. Bunlar araştırmanın bilinçli çalışma
metaforudur. **Oyuncak**, sınırları görülebilen, elde çevrilebilen,
parçalanabilen ve yeniden birleştirilebilen executable bir matematiksel
nesneyi; **oyun** ise kuralları, hamleleri, karşı-örnekleri ve sürpriz
durumları olan yapılandırılmış keşfi anlatır.

Bu yoğun oyuncaklaştırma matematiksel ciddiyeti azaltmak için değil, soyut
yapıları kurcalanabilir hâle getirmek için kullanılır. “Bahçe” Catalan
çoğalmasını, “hava” yerel durum değişimlerini, “sismograf” projection
dikişlerindeki kırılmaları, “saat” ise kiral operator çevrimlerini görünür
kılar. Metafor keşif özgürlüğünü taşır; exact hesap, kanıt ve epistemik sınır
ise çalışmanın doğruluk disiplinini taşır.

Bu workspace, verilen üç kaynağı değiştirmeden onların etrafında büyütülmüş exact deneyler koleksiyonudur. Amaç tek bir “doğru ürün” çıkarmak değil; non-associative cebirin farklı bilgi katmanlarını birbirine karıştırmadan zorlamak, kırmak ve yeni davranışlar bulmaktır.

17 Temmuz pause snapshot'ı, kanıt/evidence sınırları ve yeniden başlama noktası:
[Keşif Defteri](./DISCOVERY_LEDGER_2026-07-17.md).

## En kısa giriş

Windows'taki bu Codex GPT-5.6-Sol çalışma ortamıyla:

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py -B .\experiments\bracket_garden.py plant hhhh --audit-maps
& $py -B .\experiments\bracket_tomography.py self-test --deep
& $py -B .\experiments\associahedron_weather.py forecast hhqqhq --edges damped
& $py -B .\experiments\associahedron_holonomy.py test --deep
& $py -B .\experiments\algebra_ecology.py
& $py -B .\experiments\shadow_root_clock.py test --deep
& $py -B .\experiments\universal_shadow_adjunction.py test --deep
& $py -B .\experiments\shadow_root_seams.py test --deep
& $py -B .\experiments\shadow_root_deformations.py test --deep
& $py -B .\experiments\metaspace_seismograph.py --word QHQQHHH --max-length 7
& $py -B .\experiments\chiral_operator_monoids.py
& $py -B .\experiments\certified_signed_metaspace.py --deep-check
& $py -B .\experiments\metaspace_observability.py
& $py -B .\experiments\metaspace_synchronizer.py
& $py -B .\experiments\metaspace_memory_duality.py
& $py -B .\experiments\metaspace_rank_weather.py
& $py -B .\experiments\signed_metaspace_family.py
& $py -B .\experiments\metaspace_word_normalizer.py --deep-check
```

Scheduler hattı ayrıca verilen read-only pet dosyasını kullanır:

```powershell
& $py -B .\experiments\interrupt_adversary.py --compact
& $py -B .\experiments\interrupt_guarded_executor.py --compact
```

## Oyuncaklar

| Oyuncak | Ne kurcalar? | Güçlü giriş noktası |
|---|---|---|
| [Algebra Ecology](./experiments/ALGEBRA_ECOLOGY.md) | Nucleus, center, associator kernel, unit'ler, zero divisor'lar, automorphism/derivation ve repeated-\(h\) ormanı | `algebra_ecology.py` |
| [Bracket Garden](./experiments/BRACKET_GARDEN.md) | Bütün Catalan tree'leri, phenotype collision, exact multilinear-map kimliği ve contraction trace | `bracket_garden.py plant hhhh --audit-maps` |
| [Bracket Tomography](./experiments/BRACKET_TOMOGRAPHY.md) | Bütün tree çiftlerini ayıran minimum static probe portföyü ve exact adaptive karar ağacı | `bracket_tomography.py atlas --deep` |
| [Associahedron Weather](./experiments/ASSOCIAHEDRON_WEATHER.md) | Tree'ler arasındaki tek rotation grafiği, active/damped/calm associator kenarları ve phenotype adaları | `associahedron_weather.py forecast hhqqhq` |
| [Associahedron Holonomy](./experiments/ASSOCIAHEDRON_HOLONOMY.md) | One-hole context transport, square/pentagon closure ve mixed reassociation curvature | `associahedron_holonomy.py test --deep` |
| [Shadow Root Clock](./experiments/SHADOW_ROOT_CLOCK.md) | $s^2=h$ için minimal 6B iki-taraflı regular-root extension, clock group ve repeated-$s$ ekolojisi | `shadow_root_clock.py test --deep` |
| [Universal Shadow Adjunction](./experiments/UNIVERSAL_SHADOW_ADJUNCTION.md) | Yalnız $s^2=h$ dayatan sonsuz-boyutlu initial bracket-tree cebiri, normal-form basis ve 6B clock quotient'ı | `universal_shadow_adjunction.py test --deep` |
| [Shadow Root Seams](./experiments/SHADOW_ROOT_SEAMS.md) | Bütün minimal 6B güçlü köklerde canonical $sq/qs$ dikişi, 54D/27D table familyası ve degree-5 tomography | `shadow_root_seams.py test --deep` |
| [Shadow Root Deformations](./experiments/SHADOW_ROOT_DEFORMATIONS.md) | Sabit simetrik clock'un 48D/24D completion fiber'ı, Catalan visibility ladder ve rank strata | `shadow_root_deformations.py test --deep` |
| [Metaspace Seismograph](./experiments/METASPACE_SEISMOGRAPH.md) | Delayed projection, projection-seam ledger, root/ledger çakışmaları ve effect/algebra ayrımı | `metaspace_seismograph.py --word QHQQHHH` |
| [Chiral Operator Monoids](./experiments/CHIRAL_OPERATOR_MONOIDS.md) | Sol, sağ ve combined operator product uzaylarının exact sonlu closure'ı | `chiral_operator_monoids.py` |
| [Certified Signed Metaspace](./experiments/CERTIFIED_SIGNED_METASPACE.md) | 192 state'in üç signed-axis koordinatlı normal formu, parite karakteri ve exact-oracle sertifikalı transition VM'i | `certified_signed_metaspace.py --deep-check` |
| [Metaspace Observability](./experiments/METASPACE_OBSERVABILITY.md) | Root kanalının future suffix'lerle Moore minimization'ı ve tek-adımlık full-state tomography | `metaspace_observability.py --deep-check` |
| [Metaspace Synchronizer](./experiments/METASPACE_SYNCHRONIZER.md) | Suffix'lerin 192 başlangıç state'ini sıkıştırması, reset yokluğu ve Green ideal geometrisi | `metaspace_synchronizer.py --deep-check` |
| [Metaspace Memory Duality](./experiments/METASPACE_MEMORY_DUALITY.md) | Üç column probe ile üç rank-1 silginin ortak equivalence-kernel lattice'i | `metaspace_memory_duality.py --deep-check` |
| [Metaspace Rank Weather](./experiments/METASPACE_RANK_WEATHER.md) | Uniform random word altında beş-state exact rank havası, absorption zamanı ve üç recurrent ada | `metaspace_rank_weather.py --deep-check` |
| [Signed Metaspace Family](./experiments/SIGNED_METASPACE_FAMILY.md) | 192-state yapının abstract parity-cut $M_n\subset C_2\wr T_n$ ailesine kontrollü genellemesi | `signed_metaspace_family.py --deep-check` |
| [Metaspace Word Normalizer](./experiments/METASPACE_WORD_NORMALIZER.md) | 192-state monoid için exact shortlex transducer ve 385-rule finite complete rewriting presentation | `metaspace_word_normalizer.py --deep-check` |
| [Interrupt Contract Probe](./experiments/INTERRUPT_ADVERSARY.md) | Scheduler'ın conditional serializability kontratı ve küçük karşı-örnekleri | `interrupt_adversary.py` |
| [Guarded Executor](./experiments/INTERRUPT_GUARDED_EXECUTOR.md) | Gerçek read tracking, wave preflight ve ambiguous-order rejection ile fail-closed pet yürütme | `interrupt_guarded_executor.py` |

Tüm matematik oyuncakları standard library ve exact integer/Fraction arithmetic kullanır. NumPy yalnız verilen özgün probe'un yeniden çalıştırılmasında kullanıldı.

## Ortaya çıkan mimari ayrım

Başlangıçtaki “path/history” sezgisi tek bir şey değilmiş. Deneyler onu üç ayrı authoritative contract'a böldü:

| Katman | Sakladığı şey | Kaybedebildiği şey | Doğruluk rolü |
|---|---|---|---|
| Effect graph + serial oracle | Payload causality ve izin verilen ordering | Cebirsel/bracket estetiği | Scheduler safety / serializability |
| Operator word | Sıralı left/right action'ın sonlu metaspace quotient'ı | Aynı word içindeki bracket; uzun word kimliği | Control state / composition observable |
| Tree + projection-seam ledger | Projection'ın nerede yapıldığı, local associator residual'ları | Effect bildirimi yoksa payload safety | Path ve contraction audit'i |

Bu ayrım iki ters karşı-örnekle executable hâle geldi:

- Ayrık üç payload operation bütün sıralarda aynı state'i üretirken `HHH` iki bracket'ta iki farklı root üretir. Non-zero associator zorunlu hazard değildir.
- Aynı register üzerinde `set/mul/add` beş farklı sıralama sonucu üretirken `QQQ` bütün bracket'larda yalnız \(q\)'ya çöker. Zero associator güvenlilik sertifikası değildir.

Dolayısıyla algebra effect semantics'in yerine geçmiyor; effect semantics de path geometry'yi gereksiz kılmıyor. Product type olarak birlikte anlamlılar.

## En güçlü exact bulgular

### Cebirin iç anatomisi

- Sol, middle ve sağ nucleus ile center: yalnız \(\mathbb R1\).
- Associator tensorü surjective: image rank 3, kernel dimension 24; bunun 19 boyutu unit-factor, 5 boyutu genuine pure-plane relation.
- \(\operatorname{Der}(A)=0\), unital automorphism grubu trivial.
- Real power-associative locus tam olarak

  \[
  C=\operatorname{span}\{1,q\}\cong\mathbb R\times\mathbb R.
  \]

  Bütün idempotentler ve bütün two-sided unit'ler bu associative oasis içinde.
- Sol ve sağ operator envelope ayrı ayrı tüm \(M_3(\mathbb R)\); buna bağlı olarak proper non-zero left/right ideal yok. Buna rağmen zero divisor'lar var.
- \(h\)'nin right inverse'i \(q\), left inverse'i \(-q\); tek ortak inverse değiller.
- Kaynak cebirin içinde $s^2=h$ yok. Yalnız element root'u eklemek 4B'de kolay olsa da aynı anda $L_s^2=L_h$ ve $R_s^2=R_h$ isteyen common-unit reel uzantının minimal boyutu exact olarak 6. Açık witness'ta sol root 6-periyotlu, sağ root 12-periyotlu; ikisi $C_2^6\rtimes C_6$ mertebesi 384 clock group'unu üretiyor.
- Yalnız ordinary $s^2=h$ bağıntısını dayatan gerçek universal nesne ise 6B clock değildir: irreducible bracket tree'lerden oluşan sonsuz-boyutlu bir initial cebirdir. Non-unit growth

  \[
  b_1=3,\quad b_2=4,\quad b_n=\sum_{i=1}^{n-1}b_i b_{n-i},
  \qquad
  B(z)=\frac{1-\sqrt{(1-2z)(1-10z)}}2
  \]

  verir ve $b_n\sim10^n/(\sqrt{20\pi}\,n^{3/2})$. 6B clock bunun surjective, non-injective quotient'ıdır; $hs-sh$ açık bir kernel elemanıdır.
- Minimal 6B güçlü köklerde $sh=hs=t$ zorunlu, fakat $sq=qs$ değildir. Canonical $u:=qs$, $a:=sq$, $d:=su$ basis'inde kök iskeleti altı parametrelidir; sekiz serbest completion hücresiyle raw table familyası 54D, doğal $\mathbb Z_2$ grading altında 27D olur. Genel repeated-$s$ degree-5 yasası exact $\{a:7,u:7\}$'dir; simetrik $a=u$ dikişi bracket shock'ı altıncı dereceye erteler.
- Seçilen simetrik clock dikişi içinde completion fiber'ı 48D, parity kesiti 24D'dir. Bütün fiber boyunca exact degree-6 yasası

  \[
  \mu_6=19\delta_{+1}+19\delta_{-1}+4\delta_{tt}
  \]

  olur. Serbest hücrelerin ilk repeated-$s$ görünürlükleri sırasıyla `tt@6`, `qt/tq@7`, `tu/ut@8`, `qu/uq@9`, `uu@10`'dur.
- Sparse clock completion'ının kendi iç profili üç nucleus ve center $\mathbb R1$, commutant $\operatorname{span}\{1,t\}$, associator image rank 6 ve $\operatorname{Der}=0$'dır. Bunların tamamı bütün 48D fiber için sabit değildir: örneğin yalnız `q*t=s` seçmek operator saatini değiştirmeden commutant boyutunu $2\to1$ indirir. Nuclei/center/associator-rank/Der değerlerinin origin çevresindeki nonempty Zariski-open stratum'da korunduğu kanıtlandı; global rank-jump locus açık kaldı.

### Tree ekolojisi

- Yedi yaprağa kadar bütün Catalan tree'ler exact multilinear map olarak farklı: \(1,1,2,5,14,42,132\).
- Sabit bir `h/q` word'ü üzerinde root yalnız altı signed-basis state'inden birine düşebilir:

  \[
  \{\pm1,\pm h,\pm q\}.
  \]

  Multilinear-map identity ile tek-input phenotype identity bu nedenle dramatik biçimde ayrılıyor.
- `hhhh`: 5 tree, 3 phenotype, fakat 5 ayrı multilinear map. Aynı `hhhh` sonucuna gelen iki tree `1hhh` girdisinde ayrılıyor.
- İlk altı-mask word `hhqqhq` (6 yaprak); saf \(h^7\) de bütün altı maskeyi üretir.
- Tree-map kimliğini full $3^n$ basis signature ile okumak zorunlu değil: minimum **static** tomography probe sayıları $n=3,4,5,6$ için exact $1,2,3,4$. $n=7$ için sertifikalı aralık $4\le OPT\le5$; timeout optimalite sayılmıyor.
- Adaptive probe seçimi $n=3..7$ için exact worst-case derinlikleri $1,2,3,3,4$ veriyor. Böylece $n=6$'da adaptivity gerçekten static 4 probe'u 3'e indiriyor; greedy static seçimin 5'te kalması ayrıca portföy optimizasyonunun sezgisel olmadığını gösteriyor.

### Associahedron havası

- Rotation graph'ları \(n\le8\) için exact Catalan vertex/edge sayıları, regular degree ve connectivity ile yeniden üretildi.
- `hhqqhq`: 42 vertex, 84 edge; 40 active, 5 damped, 39 calm rotation. Aynı \(q\) phenotype'ı associahedron üzerinde iki ayrı adaya bölünüyor.
- \(h^7\): 132 vertex, 330 edge; yalnız altı phenotype fakat 38 phenotype-induced component.
- `DAMPED`, local associator non-zero iken dış context'in root delta'yı sıfırlayabildiğini somutlaştırıyor.
- Her rotation edge'inde dış tree exact bir one-hole lineer map $C_e$ kuruyor ve $\Delta_e^{root}=C_e(r_e)$. `DAMPED` tam olarak nonzero $r_e$'nin singular context kernel'ine düşmesi.
- Root delta 1-form'u bir gradient olduğu için bütün cycle circulation'ları sıfır. Buna karşılık canonical basis'le özdeşleştirilen ham lokal associator toplamı square/pentagon yüzlerinde nonzero olabiliyor; exact kapanış $\sum r_e+\sum(C_e-I)r_e=0$ context telafisiyle geliyor. Bu raw nicelik invertible gauge transport veya fiziksel curvature diye sunulmuyor.

### Metaspace sıkıştırmaları

- Sabit ordered word için ordinary operator multiplication bracket-blind'dır. En sonda \(M(1)\) projeksiyonu tamamen sağa-yaslı evaluation'ı seçer.
- `QHQQHHH`: 132 tree → 6 root → 95 çıplak defect ledger → tree-coordinate eklenince 132 ayrı audit kaydı.
- Sol operator monoid yalnız 99 exact state'ten oluşur. Sağ monoid 102, left/right combined monoid 192 state'tir.
- Combined monoid bütün 168 singular signed-basis action'ı ve 24 invertible cyclic-signed action'ı içerir; bütün matris girdileri \(\{-1,0,1\}\) içinde kalır.
- Bu sonlu monoid'lerin real linear span'ının \(M_3(\mathbb R)\) olması çelişki değildir: span arbitrary sum/scalar kullanır, monoid yalnız product kullanır.
- 192-state combined monoid, 216 elemanlı signed full transformation monoid'i içinde tam olarak bütün 168 singular state ile absolute permutation'ı even olan 24 unit'in birleşimidir:

  \[
  \mathcal M=\chi^{-1}(\{0,+1\})\subset C_2\wr T_3.
  \]

  Generator rankı 3'tür; \(L_q\) redundant'tır ve dışarıdaki herhangi bir odd unit eklenince ambient 216 state'in tamamı oluşur.
- Root'un anlık altı-value görünümü gizli state'i gerçekten kaybetmez: horizon profili \(6\to192\). `epsilon`, `Lh`, `Lq` probe'ları sırasıyla üç matrix sütununu okur; bir adımlık exact tomography verir.
- Sağ-action image spektrumu yalnız \(192,36,6\). `Lq Lq` 192 state'i altı sonuca indirir, fakat zero state olmadığı için reset word yoktur. 18.336 pair'in 7.632'si en az bir suffix ile birleşebilir; 10.704'ü hiçbir zaman birleşmez.
- Üç column-equality kernel'inin kesişimi yalnız identity relation, birleşimi tam synchronizable-pair kümesidir. Singular rank \(r\in\{1,2\}\) için sol/sağ information boyutları exact olarak

  \[
  |Mp|=6^r,\qquad |pM|=(2r)^3
  \]

  davranır; rank-2 fiber'larındaki \(12\times4+24\times6\) asimetrisi unit tabakasındaki even-parity izidir.
- Rank tek başına Markov state'i değildir. Exact Moore refinement rank-2'yi üç faza ayırıp \(3\to4\to5\) class'lık minimal hava makinesi üretir. Uniform dört-generator seçiminde identity'den rank 1'e ortalama iniş \(11/2\), variance \(59/4\) adımdır; eşit boyutlu üç rank-1 adaya entry olasılıkları sırasıyla \(1/3,1/6,1/2\)'dir.
- Aynı parity-cut signed-transformation yapısı abstract olarak her $n\ge2$ için $M_n=\chi_n^{-1}(\{0,+1\})$ biçiminde kurulabiliyor; $|M_n|=(2n)^n-2^{n-1}n!$. Yalnız $n=3$ literal source cebirle özdeşleştirildi; diğer boyutlar kontrollü semigroup türetimidir, cebirsel/physical extension iddiası değildir.
- Üç-generator 192-state monoid'in shortlex çapı 9 ve depth profili $1,3,9,23,38,44,34,24,12,4$. Canonical boundary transition'larından türeyen 385 yönlü equation, shortlex'i strict azalttığı ve irreducible'ları tam 192 canonical word'e kapattığı için gerçekten finite terminating/confluent rewriting presentation oluşturuyor; relation-basis minimality iddia edilmiyor.
- `Rq`, presentation'a dördüncü harf olarak eklenmiyor; exact `Lq Lh Lq` macro'su. $\{Lh,Rh,Lq\}$ ile $\{Lh,Rh,Rq\}$ aynı 192 state/diameter 9 closure'ını üretse de shortlex depth profilleri farklı: algebraic substitution ordered Cayley geometrisini isometry yapmıyor.

### Scheduler kontratı

- Verilen seed ile 5.000 trial: serial/wave mismatch 0; blind stale-snapshot mismatch 4.860.
- Bounded depth-four corpus: 69.905 schedule, 629.145 execution, mismatch 0.
- Doğruluk conditional: faithful reads/writes, conflict-free wave construction, trusted delivery identity ve belirli total order gerekiyor.
- Undeclared read sessiz yanlış sonuç üretebilir; manual RAW wave builder atlanırsa kaynak executor bunu tam doğrulamaz; tamamen eşit order key caller input order'ına düşer.
- Guarded executor bu toy model içinde actual Sequence read'lerini izler, bütün wave planını evaluation öncesi preflight eder ve semantically ambiguous duplicate order key'leri reddeder. 39.321 bounded execution'da valid davranışı değiştirmedi.

## Kaynak iğneleri

Verilen dış dosyalar özellikle değiştirilmedi. Okuma sırasında iki küçük ama anlamlı iğne kaydedildi:

1. Whitepaper bölüm 2.2, satır 141–143'te genel koordinat formülünün iki `+` operatörü eksik. Aynı formül Ek A.1'de doğru yazılmış ve bütün scriptler doğru formülü kullanıyor.
2. Pet içindeki `AlgebraElement` docstring'i coefficient ile basis sembolünü aynı `h/q` adıyla yazdığı için görsel olarak belirsiz; runtime çarpımı doğru.

Başlangıç/final kaynak hashleri:

```text
nonassoc_algebra_probe.py                         78A1948274F16E9872290FCD968137080884E56B1646831350EE0326F4100252
nonassoc_interrupt_pet.py                         46A406DCDD402FAEB2BA67E4E904E81C00040322AB1D8C2B3B6FF8F5995FC098
nonassociative_metaspace_interrupt_whitepaper.md  5E9DBB6C42EADDB8A7ADB91C73207CFE95E402CC66D942EA1C3128077B65E433
```

## Epistemik sınır

**Verified:** Yukarıdaki sonlu sayımlar, exact row reductions, basis-map equality testleri, closure taramaları, scheduler corpus'ları ve guard rejection örnekleri gerçekten çalıştırıldı.

**Inferred / proved from displayed equations:** associative oasis, unit sınıflandırması, signed-basis altı-state tavanı, operator monoid ambient bound ve one-sided ideal sonucu.

**Open:** Bütün derecelerde Catalan tree-map injectivity; $n=7$ static tomography için 4-probe feasibility (şimdiki exact sınır $4\le OPT\le5$); minimal projection-seam compression; typed effect calculus ve genel serializability proof; bütün 6B strong-root tablolarının izomorfizma/rank-jump sınıflandırması; universal strong-root quotient'ın ideal/representation teorisi; gerçek GPU latency/throughput; herhangi bir fiziksel yorum.

Bu kutunun şu anki merkezi sonucu bir slogan değil, bir interface ayrımıdır:

```text
payload truth        := explicit effects + serial semantics
ordered control      := finite operator quotient
bracket/path history := explicit tree + projection seams
```

Üçünü aynı nesne sanınca false positive ve false negative doğuyor. Üçünü ayrı tutup birlikte taşıyınca oyuncak bir araştırma mimarisine dönüşüyor.
