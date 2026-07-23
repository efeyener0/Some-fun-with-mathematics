# Certified Signed Metaspace

Bu oyuncak, 192 matrislik combined operator monoid'ini daha küçük bir yüzeyde
gösterir: her durum aslında üç imzalı eksen numarasıyla tam olarak kodlanabilir.
Bu bir yaklaşık temsil değil; literal $3\times3$ integer matrislerle birebir ve
çarpımı koruyan bir normal formdur.

Çalıştırmak için:

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py -B .\experiments\certified_signed_metaspace.py
& $py -B .\experiments\certified_signed_metaspace.py --word 'Lh Lq Rh Rq Lh' --json
& $py -B .\experiments\certified_signed_metaspace.py --deep-check --json
```

## Üç koordinatlı exact normal form

Basis sırası $(1,h,q)=(e_1,e_2,e_3)$ olsun. Her signed-basis action matrisi
benzersiz bir

\[
a=(a_1,a_2,a_3)\in\{\pm1,\pm2,\pm3\}^3
\]

tuple'ıyla kodlanır:

\[
M(a)e_j=\operatorname{sgn}(a_j)e_{|a_j|}.
\]

Örneğin dört generator:

\[
L_h=(2,3,1),\qquad L_q=(3,-1,3),
\]

\[
R_h=(2,3,-1),\qquad R_q=(3,1,3).
\]

Mevcut “word'ü sağa ekle” sözleşmesinde çarpım:

\[
M(a)M(b)=M(a\star b),
\qquad
(a\star b)_j=\operatorname{sgn}(b_j)a_{|b_j|}.
\]

Bunun nedeni doğrudan sütun action'ıdır: $b$, $e_j$'yi önce
$\operatorname{sgn}(b_j)e_{|b_j|}$'ye; $a$ da o ekseni kendi ilgili
sütununa gönderir. Float, tolerance veya hash collision yoktur.

## 216'nın içindeki 192

Bütün signed transformation'lar

\[
\Sigma_3=\{\pm1,\pm2,\pm3\}^3
\]

ve dolayısıyla $|\Sigma_3|=6^3=216$. Bu, signed full transformation
monoid'i $C_2\wr T_3$ olarak okunabilir.

Combined monoid'in kapalı-form üyelik karakteri şudur. Önce

\[
\chi(a)=
\begin{cases}
0, & |a|\text{ tekilse},\\
+1, & |a|\in A_3,\\
-1, & |a|\in S_3\setminus A_3
\end{cases}
\]

tanımlansın. Mutlak harita sıradan composition yaptığı için

\[
\chi(a\star b)=\chi(a)\chi(b).
\]

O zaman deneydeki monoid tam olarak

\[
\boxed{\mathcal M=\chi^{-1}(\{0,+1\})}
\]

oluyor. Başka deyişle:

- bütün singular signed transformation'lar içeride;
- mutlak eksen permütasyonu even olan bütün signed unit'ler içeride;
- dışarıda yalnız mutlak permütasyonu odd olan 24 unit var.

“Even” determinantı $+1$ demek değildir. Sütun işaretleri serbesttir;
even olması gereken, işaretler silindikten sonraki eksen permütasyonudur.
Örneğin $\operatorname{diag}(-1,1,1)$ determinantı $-1$ olsa da içeridedir.

Matris yüzünde aynı karakter çok ucuz görünür:

\[
\chi(M)=\det(M)\prod_{j=1}^3 s_j,
\]

burada $s_j$, $j$. sütundaki tek non-zero girdinin işaretidir.

### Sayım

| Tabaka | Mutlak harita sayısı | Sign lift | Toplam |
|---|---:|---:|---:|
| Rank 1 | $3$ | $2^3$ | 24 |
| Rank 2 | $\binom32(2^3-2)=18$ | $2^3$ | 144 |
| Even permutation unit | $|A_3|=3$ | $2^3$ | 24 |
| **Combined** | 24 | 8 | **192** |

Singular 168 durum bir two-sided ideal'dır. Parite yalnız unit tabakasında
anlamlıdır; singular composition onun işaretini $0$'a emer. “Tekillik parite
hafızasını siliyor” cümlesi burada metafor değil, doğrudan homomorphism
eşitliğidir.

## Generator rankı ve redundant kapı

Exact tuple BFS şu daha küçük sunumu doğruladı:

\[
\langle L_h,R_h,R_q\rangle=\mathcal M.
\]

Dolayısıyla $L_q$, combined monoid için generator olarak redundant. Üç
generator aynı 192 duruma ulaşıyor ve maksimal minimal-word derinliği yine 9.

Üç ayrıca minimaldir:

1. Unit group $C_2^3\rtimes A_3\cong C_2\times A_4$ cyclic değildir; en az
   iki unit generator gerekir.
2. Singular elemanların product'ı yeniden singular olduğu için singular bir
   generator unit üretemez.
3. Singular ideal'e girmek için en az bir singular generator daha gerekir.

Böylece monoid generator rankı tam olarak 3'tür.

Daha keskin bir sınır da var: dışarıdaki 24 odd unit'ten herhangi bir tanesini
eklemek 216 durumlu ambient monoid'in tamamını üretir. Bu nedenle
$\mathcal M$, $C_2\wr T_3$ içinde maximal proper submonoid'dir.

## Exact oracle ve hızlı lane ayrımı

Kod üç sorumluluğu ayırır:

| Lane | Temsil | Yetki |
|---|---|---|
| Exact witness | 9 integer girdili matris | Authoritative source model |
| Certified compact | 3 signed-axis girdisi ve $\star$ | Yalnız ispatlı signed-action domain'i |
| State table | 192 state ID × 4 transition | Derived accelerator |

Tablo başlangıçta kapalı-form predicate'den deterministik üretilir; sonra exact
matrix closure ile state-set equality, bütün 768 generator transition'ı ve
canonical BFS depth'leri karşılaştırılır. Model, state set ve transition table
ayrı SHA-256 fingerprint'lerle literal source generatorlarına bağlanır.

Signed-action domain'i dışındaki bir matris kompakt lane'e zorlanmaz. Örneğin
$2I$ exact integer matrix fallback'ine gider. `--deep-check` ayrıca:

- 192² = 36.864 compact pair product'ı matrix oracle ile karşılaştırır;
- 216² = 46.656 karakter çarpımını doğrular;
- dışarıdaki 24 odd unit'in her birinin ambient'i 216'ya tamamladığını sınar;
- bozulmuş bir transition ve bozulmuş table fingerprint'i enjekte edip ikisinin
  de reddedildiğini doğrular.

Bu yapı hızlı lane'in oracle'ın yerine geçtiğini iddia etmez. Tam tersine, exact
omurga karar yetkisini korur; kompakt lane yalnız kanıtlı domain'de onunla eşdeğer
olduğu için kullanılabilir.

## Şu an doğrulanan fingerprint'ler

```text
model       c42d225ccda025a81fc3941cff9a541d85f1011030885e8553a5b7f64a1c9a3e
states      82495596ee42be3ee8c946e5a64ebb93c2b2e9e43e24a074db7181800f02f971
transitions 8baeb58631b2c08f7c4e6bc88000258c01bec3d28fd1927ac87d21efeea530f7
```

Bu fingerprint'ler değişirse script sessizce yeni tabloyu authoritative kabul
etmez; re-certification gerektiren bir model/table drift'i olarak kapanır.

## Epistemik sınır

**Algebraically exact:** Signed-code composition formülü, tanımlı domain'de
matrix product'a eşittir; $\chi$ multiplicative'dir; singular set ideal'dır.

**Computationally certified:** Literal dört source matrisi tarafından üretilen
exact closure'ın kapalı-form 192-state predicate ile eşitliği; bütün transition,
pair, character ve maximal-extension kontrolleri gerçekten çalıştırıldı.

**İddia edilmeyen:** Gerçek donanım performance kazanımı, noisy ölçüm,
continuous extension veya fiziksel yorum. Bu script'in “fast” kelimesi daha
küçük exact state representation ve O(1) transition lookup anlamındadır.
