# Metaspace Projection-Seam Seismograph

Bu oyuncak, operator metaspace ile parantez ağacı arasındaki ilişkiyi biraz daha kesinleştirir. Ana bulgu şudur:

> Geciktirilmiş projeksiyon sıralı operator bileşimini korur; fakat ordinary matris çarpımı associative olduğu için aynı sözcüğün iç parantezlerini tek başına korumaz. Parantez geçmişi, projeksiyonun **nerede** yapıldığını da taşımalıdır.

Bu bir reddiye değil, mimarinin iç ayrımını keskinleştiren bir ek katmandır:

- operator word: sıralı composition;
- projection schedule: binary tree;
- seam defect: her projection sınırındaki yerel residual;
- effect graph: payload güvenliğinin ayrı sertifikası.

## Çalıştırma

```powershell
<python> .\experiments\metaspace_seismograph.py
<python> .\experiments\metaspace_seismograph.py --word QQQ --max-length 7 --json
```

Script yalnız standard library ve exact integer arithmetic kullanır. Başlangıçta kendi cebir, operator, Catalan-tree ve effect-separation kontrollerini çalıştırır.

## Matematiksel dikiş

İki element arasındaki projeksiyon dikişi:

\[
D(x,y)=L_xL_y-L_{xy}
\]

olarak tutulur. Her \(z\) için:

\[
D(x,y)z=x(yz)-(xy)z=-[x,y,z].
\]

Dolayısıyla \(D\), associator'ın üçüncü argüman üzerindeki operator biçimidir. Bir evaluation tree'nin her iç düğümünde şu kayıt bırakılır:

```text
(leaf interval, split point, local projection defect)
```

Yalnız defect dizisi hâlâ çakışabilir. Leaf interval ve split eklendiğinde tree topolojisi açıkça korunur; bu injectivity cebirin mucizesi değil, metadata kontratının bilinçli sonucudur.

## Gözlenen manzara

17 Temmuz 2026 çalıştırmasında:

| Deney | Sonuç |
|---|---:|
| `HHHHQ` full binary tree | 14 |
| `HHHHQ` farklı root elementi | 4 |
| `HHHHQ` farklı ham defect ledger'ı | 8 |
| `HHHHQ` tree-annotated ledger | 14 |
| 7 yaprakta tree / word | 132 |
| 7 yaprakta herhangi bir word için en çok farklı root | 6 |
| 7 yaprakta en çok ham ledger | 95 (`QHQQHHH`) |

Generator word'lerinin root'ta en çok altı değer üretmesi tesadüf değildir. Signed basis kümesi

\[
\{\pm1,\pm h,\pm q\}
\]

çarpım altında kapalıdır. Dolayısıyla yalnız `H/Q` yapraklarından kurulan **her** bracketed tree, uzunluğu ne olursa olsun bu altı elementten birine düşer. Bu, root kanalındaki altı-state tavanını exact bir induction sonucu yapar; tree-map'lerin multilinear haritalar olarak ayrı kalmasıyla çelişmez.

\(H/Q\) sözcükleri üçten yedi yaprağa kadar tam tarandığında, bütün parantezleri aynı root elementine çöken tek sözcük her uzunlukta \(Q^n\) oldu. Bu sonlu bir gözlemdir; bütün \(n\) için ispat değildir.

`QQQ` özellikle güzel bir küçük yaratık:

- iki tree de root'ta \(q\) verir;
- ham defect ledger'ları da aynıdır;
- buna rağmen toplam seam energy sıfır değil, 4'tür;
- tree ancak projection konumları açıkça taşındığında ayrılır.

Root element bu nedenle path'in çok kayıplı bir özeti; residual'ın varlığı ise tek başına topology kimliği değildir.

## Geciktirilmiş projeksiyonun yönü

\[
L_{x_1}L_{x_2}\cdots L_{x_n}(1)
=x_1(x_2(\cdots x_n))
\]

olduğu için operator word en sonda projekte edildiğinde tamamen sağa yaslı evaluation elde edilir. Script bunu bütün \(H/Q\) sözcüklerinde altı yaprağa kadar exact kontrol eder.

Bu şu ayrımı verir:

- projection'ı geciktirmek, erken projection'da kaybolan operator action bilgisini korur;
- fakat sabit ordered word içindeki alternatif bracketings'i korumaz;
- alternatif bracketings için tree veya eşdeğer projection-seam programı ayrıca authoritative olmalıdır.

### Operator word de tam history değildir

Exact breadth-first closure ayrıca şaşırtıcı bir ikinci sıkıştırma buldu:

\[
\langle I,L_h,L_q\rangle_{\text{multiplicative}}
\]

monoid'i yalnız **99 farklı matristen** oluşuyor. Closure, her bulunan matrisin sağdan hem \(L_h\) hem \(L_q\) ile çarpılması ve yeni state kalmayana kadar exact integer karşılaştırmasıyla doğrulandı.

- bütün 99 matrisin girdileri \(\{-1,0,1\}\) içinde;
- en uzun minimal temsil 13 sembol;
- bu temsili veren witness `HHQHHQHHQHQHH`;
- depth başına yeni state sayısı `1,2,4,6,9,11,13,12,12,10,9,6,3,1,0`.

Monoid'in küçük anatomisi de exact çıkarıldı:

| Operator rankı | State |
|---:|---:|
| 3 | 3 |
| 2 | 72 |
| 1 | 24 |
| 0 | 0 |

Yalnız 3 state invertible, 19 state idempotent ve nilpotent state yok. Özellikle element-level \(q^2=q\), operator-level \(L_q^2=L_q\) anlamına gelmiyor:

\[
L_q^2\ne L_q,
\qquad
(L_q^2)^2=L_q^2,
\qquad
L_q^3=L_q^2.
\]

Bu ayrım ACK metaforu için önemlidir. Pet'teki `ack * q` element state'inde gerçekten ilk retry'dan itibaren sabitlenir; fakat \(L_q\)'yu keyfi continuation'lar üzerinde tek-adımlı idempotent bir operator sanmak yanlış olur.

Sonluluğun yapısal nedeni de görünür: \(L_h\) ve \(L_q\), her basis vektörünü yine tek bir işaretli basis vektörüne yollar. Bu özellik composition altında korunur. Üç kolonun her biri bağımsız olarak altı işaretli basis hedefinden birini seçebildiği için ambient evren en fazla

\[
(2\cdot3)^3=216
\]

signed-basis action matrisidir. Sol generator çifti bu sonlu evrenin tam 99 state'ini erişiyor.

Bu, whitepaper'daki

\[
\operatorname{Alg}\langle I,L_h,L_q\rangle=M_3(\mathbb R)
\]

sonucuyla çelişmez. `Alg` lineer kombinasyonlarla oluşan dokuz boyutlu associative envelope'dur; 99 elemanlı sonlu bir matris kümesi bu uzayın tamamını lineer olarak span edebilir. Fakat multiplicative history açısından sonuç nettir: operator metaspace, altı root state'inden daha zengin olsa da sonsuz word geçmişini injective saklamaz; onu 99-state bir quotient'a sıkıştırır.

## Effect semantiğiyle ayrışma

İki karşı-örnek özellikle bilerek yan yana kuruldu.

### Güvenli fakat algebraically path-sensitive

Üç handler ayrık register'lara etki ediyor. Altı permutation'ın tamamı aynı payload state'ine ulaşıyor; explicit effect graph'ta conflict yok. Control word `HHH` ise iki parantezde iki farklı root üretiyor.

Sonuç: non-zero associator, payload hazard'ı olmak zorunda değil.

### Güvensiz fakat algebraically root-silent

`set`, `mul`, `add` aynı register üzerinde çalışıyor. Altı permutation beş farklı payload state'i üretiyor; bütün event çiftleri conflict. Control word `QQQ` ise bütün parantezlerde yalnız \(q\) üretiyor.

Sonuç: zero associator, yeniden sıralamanın güvenli olduğunu göstermez.

## Rol haritası

| Kavram | Birincil rol | Authoritative? | Failure condition / sınır |
|---|---|---:|---|
| Payload state | Gözlenebilir hesap sonucu | Evet | Handler semantiği yanlış modellenirse |
| Effect conflict graph | Serializability/safety sertifikası | Evet, tanımlı model içinde | Effect declaration eksikse |
| Root algebra elementi | Kayıplı path özeti | Hayır | Farklı tree'ler çakışabilir |
| Unprojected operator word | Ordered composition | Hayır | Bracketing'i associative olarak siler; word çakışmaları da mümkün |
| Projection defect | Yerel associator operatorü | Hayır | Tek başına topology veya safety vermez |
| Annotated seam ledger | Tree-indexed audit kaydı | Tree için, bilinen word altında | Metadata çıkarılırsa injectivity kaybolabilir |

## Epistemik kayıt

**Doğrulandı:** Yukarıdaki sonlu sayımlar, \(D(x,y)z=-[x,y,z]\) basis kontrolleri, late projection/right-comb eşitliği, güvenli ve güvensiz effect örnekleri script çalıştırılarak kontrol edildi.

**Güçlü çıkarım:** Projection-seam ledger, metaspace'te “history” denilen şeyi order history ve bracketing/projection history olarak ikiye ayırmak için uygun bir executable contract'tır.

**Doğrulanmadı:** Ledger'ın minimal olduğu, yedi yapraktan sonraki landscape davranışı, gerçek scheduler'da fayda veya compression oranı, GPU performansı ve fiziksel yorum.
