# Bracket Garden

`bracket_garden.py`, \(1,h,q\) non-associative cebirini bir sonuç
hesaplayıcısı gibi değil, **soy ağacı koruyan bir keşif oyuncağı** gibi ele
alır.

Çekirdek çarpım:

\[
h^2=q,\qquad q^2=q,\qquad hq=1,\qquad qh=-1.
\]

Genel koordinat çarpımı tam sayı aritmetiğiyle uygulanır:

\[
(a+bh+cq)(d+eh+fq)
=(ad+bf-ce)+(ae+bd)h+(af+be+cd+cf)q.
\]

Harici paket yoktur; Python 3.10+ yeterlidir.

## Korunan üç kimlik katmanı

Araç, birbirine benzetilmesi tehlikeli olan üç şeyi özellikle ayırır:

1. **Tree identity:** Catalan ağacının kendisi. `T6:00` gibi kararlı bir ID ve
   yaprak konumlarını içeren `shape` koduyla korunur.
2. **Phenotype:** Seçilmiş tek bir yaprak kelimesinde ağacın ürettiği cebir
   elemanı. İki ayrı ağaç burada çarpışabilir.
3. **Multilinear-map identity:** Ağacın indüklediği bütün \(n\)-lineer harita.
   Bu kimlik, \((1,h,q)^n\) tensor-basis girdilerinin tamamında exact imzayla
   karşılaştırılır.

Dolayısıyla aynı phenotype'a gelen iki ağaç birleştirilmez. Buna
**phenotype collision** denir. Aynı yaprak kelimesinin farklı phenotype'lara
ayrılmasına ise **split** denir. `--audit-maps`, görünüşte çarpışan iki ağacın
başka bir basis kelimesinde ayrıldığı bir *camouflage witness* da verir.

Bu ayrım whitepaper'daki temel invariant'ı korur: element sonucu contraction
tree metadata'sının yerine geçmez.

## Kullanım

### Bir kelimeyi ek

```powershell
python .\experiments\bracket_garden.py plant hhhh
```

Bu komut bütün \(C_3=5\) full binary tree'yi üretir, değerlendirir ve
phenotype kovalarına ayırır. Her satır tree ID, kayıpsız shape kodu ve tam
parantezli ifadeyi taşır.

Exact multilinear-map ayrımını da görmek için:

```powershell
python .\experiments\bracket_garden.py plant hhhh --audit-maps
```

Varsayılan gösterim her phenotype için sekiz ağaçla sınırlıdır; hesaplanan
ağaçlar silinmez. Hepsini yazdırmak için `--limit 0` kullanılır.

Kelime parser'ı `1`, `h`, `q` ve bunların işaretli hallerini kabul eder:

```powershell
python .\experiments\bracket_garden.py plant '-h, q, +1'
```

Parantez girilmez; oyuncağın işi zaten bütün parantezleri büyütmektir.

### Tek ağacın contraction izini izle

```powershell
python .\experiments\bracket_garden.py trace hhqq --tree 3
```

Tree index'i sıfır tabanlıdır ve `plant` çıktısındaki `Tn:index` ile aynıdır.
Trace post-order'da her gerçek çarpımı gösterir; örtük reassociation yapmaz.

### Deterministik “six-mask expedition”

```powershell
python .\experiments\bracket_garden.py expedition --max-leaves 8
```

Altkomutsuz çalıştırma da bu expedition'ı başlatır.

Expedition, her \(n\) için bütün \(2^n\) `h/q` kelimelerini ve bütün Catalan
ağaçlarını exhaustive tarar. Önce phenotype sayısını maksimize eder; eşitlikte
en büyük collision kovasını küçültür; son eşitliği `h < q` lexical sırası
bozar. Randomness yoktur.

Buradaki küçük fakat güzel tuhaflık şudur: basis çarpım tablosu kapalı olduğu
için yalnız `h/q` yapraklarından oluşan **her** ağaç şu altı maskeden birine
gelir:

\[
\{1,-1,h,-h,q,-q\}.
\]

Fakat ağaç sayısı Catalan hızında büyür. Expedition, phenotype uzayının altı
renkte doymasını ve tree-history uzayının büyümeye devam etmesini yan yana
gösterir. Bu “altı sonuç var, öyleyse altı ağaç var” demek değildir; tam
tersine aracın sergilediği bilgi kaybı budur.

### Bütün ağacı multilinear harita olarak denetle

```powershell
python .\experiments\bracket_garden.py maps 7
```

`maps`, her tree için \(3^n\) basis tuple'ını exact değerlendirir. Bilineer
çarpımın tree composition'ı multilinear olduğundan bu rastgele test değil,
sonlu bir harita eşitliği testidir. Hesap etkileşimli kalsın diye sınır yedi
yapraktır; bu aynı zamanda kaynak whitepaper'daki doğrulama sınırıdır.

Genel `plant`/`trace` tree üretimi de kazara Catalan patlaması yaratmamak
için 11 yaprakta durur. Bu bir cebirsel quotient değildir: sınır içindeki bütün
ağaçlar korunur; sınır aşılırsa sessizce örneklemek yerine açık hata verilir.

### Yerleşik testler

```powershell
python .\experiments\bracket_garden.py test
python .\experiments\bracket_garden.py test --deep
```

`--deep`, birden yedi yaprağa kadar bütün Catalan ağaçlarının multilinear
imzalarını exact karşılaştırır.

## Matematiksel sınır ve dürüstlük notu

- `phenotype collision`, tree-map eşitliği değildir.
- Yedi yaprağa kadar map ayrımı sonlu exact doğrulamadır; bütün dereceler için
  ispat değildir.
- Altı-mask sınırı yalnız yaprakları işaretli basis elemanlarından seçilen
  kelimeler içindir. Genel \(a+bh+cq\) girdilerinin sonuç uzayı altı elemanla
  sınırlı değildir.
- Araç non-associativity'yi ordinary bir fold'a dönüştürmez. Her çarpım
  explicit `Branch(left, right)` düğümünden gelir.
- Kaynak dosyalar yalnız cebir tanımını ve doğrulanmış sınırı anlamak için
  okundu; bu deney bağımsız, standard-library-only bir uygulamadır.

## Dosya sınırı

Deney yalnız şu iki dosyadan oluşur:

- `experiments/bracket_garden.py`
- `experiments/BRACKET_GARDEN.md`

Kalıcı veri, network erişimi, global kurulum veya workspace dışı mutation
yapmaz.
