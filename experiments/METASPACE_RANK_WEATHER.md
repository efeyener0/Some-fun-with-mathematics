# Metaspace Rank Weather

Bu oyuncak, combined monoid üzerinde sağa rastgele generator eklerken matrix
rankının nasıl “hava değiştirdiğini” exact olarak izler.

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py -B .\experiments\metaspace_rank_weather.py
& $py -B .\experiments\metaspace_rank_weather.py --horizon 16 --json
& $py -B .\experiments\metaspace_rank_weather.py --deep-check
```

Randomness modeli açık ve küçük: her adımda `Lh`, `Lq`, `Rh`, `Rq` bağımsız ve
eşit olasılıkla, yani ayrı ayrı $1/4$ seçiliyor. Başka distribution'a dair
genelleme yapılmıyor.

## Üç rank yetmiyor

Rank product altında yükselmez:

- rank 3 unit'ler rank 3 veya rank 2'ye iner;
- rank 2 state'ler rank 2 veya rank 1'e iner;
- rank 1 ideal absorbandır.

Buna rağmen yalnız `rank ∈ {1,2,3}` bir Markov state'i değildir. Rank 2'deki
144 state'in 96'sı bir sonraki adımda hiç rank düşüremezken 48'i iki `q`
generatorıyla doğrudan rank 1'e düşebilir.

Rankı Moore output olarak tutup literal dört harfli transition sistemini exact
minimize edince refinement profili

\[
3\longrightarrow4\longrightarrow5\longrightarrow5
\]

olur. Yani doğru minimal hava makinesi üç değil beş state'tir.

## Beş-state exact hava makinesi

$H=\{L_h,R_h\}$ ve $Q=\{L_q,R_q\}$ aileleri olsun.

| Hava state'i | Eleman | $H$ ile | $Q$ ile |
|---|---:|---|---|
| `rank3_unit_weather` | 24 | kendisi | `rank2_drop_gate` |
| `rank2_funnel` | 48 | `rank2_drop_gate` | `rank2_drop_gate` |
| `rank2_drop_gate` | 48 | `rank2_return` | `rank1_absorbing` |
| `rank2_return` | 48 | `rank2_funnel` | `rank2_drop_gate` |
| `rank1_absorbing` | 24 | kendisi | kendisi |

Tablo yalnız uniform Markov lumping'i değil, generator isimlerini koruyan
deterministik Moore quotient'idir. Her bloktaki her 192-state transition aynı
beş-state hedefe gider.

Bu tablo rank-2 içindeki hidden phase'i görünür kılıyor:

- **funnel:** hangi harf gelirse gelsin gate'e gider;
- **gate:** `q` family rankı düşürür, `h` family bir return turu açar;
- **return:** `h` funnel'a, `q` tekrar gate'e döner.

## Rank 1'e iniş zamanı

Uniform seçimde $P(H)=P(Q)=1/2$. Exact Fraction lineer sistemi rank-1'e first
hitting time $T$ için şunları verir:

| Başlangıç havası | $\mathbb E[T]$ | $\operatorname{Var}(T)$ |
|---|---:|---:|
| rank 1 | $0$ | $0$ |
| funnel | $9/2$ | $51/4$ |
| gate | $7/2$ | $51/4$ |
| return | $5$ | $13$ |
| identity'nin unit havası | $11/2$ | $59/4$ |

Identity'den ilk rank düşüşü bir `q` bekler ve ortalama iki adım sürer; sonra
gate'ten rank 1'e kalan exact ortalama $7/2$ adımdır. Toplamın $11/2$ olması bu
iki dependency'nin açık toplamıdır.

İlk birkaç first-hit olasılığı:

| $n$ | $P(T=n)$ | $P(T\le n)$ |
|---:|---:|---:|
| 1 | $0$ | $0$ |
| 2 | $1/4$ | $1/4$ |
| 3 | $1/8$ | $3/8$ |
| 4 | $1/8$ | $1/2$ |
| 5 | $1/8$ | $5/8$ |
| 6 | $5/64$ | $45/64$ |
| 12 | $37/2048$ | $241/256$ |

`--horizon` yalnız bu sonlu tabloyu ne kadar yazdıracağımızı belirler; mean ve
variance truncation'dan değil exact absorbing-chain çözümünden gelir.

## Üç absorban ada, eşit olmayan yağmur

Rank-1 ideal tek bir recurrent component değildir. Range eksenine göre üç ayrı
closed SCC vardır ve her biri sekiz state taşır:

\[
\mathcal I_1,\qquad\mathcal I_h,\qquad\mathcal I_q.
\]

Boyutları eşit olsa da identity'den uniform generator yağmuru altında eventual
entry measure eşit değildir:

\[
\boxed{
P(\mathcal I_1)=\frac13,\qquad
P(\mathcal I_h)=\frac16,\qquad
P(\mathcal I_q)=\frac12
}
\]

Bu sayılar 21-block'luk exact strong lumping ve Fraction lineer sistemiyle
çözülür. $q$ adasının daha yakın olması yalnız shortest-word estetiği değildir;
transition measure içinde gerçekten daha fazla probability mass alır.

## Green geometry ile weather phase birbirine dik

192-state automaton'ın SCC profili:

| Rank | SCC sayısı | SCC boyutu |
|---:|---:|---:|
| 3 | 1 | 24 |
| 2 | 3 | 48 |
| 1 | 3 | 8 |

Bu, Synchronizer'daki Green-$\mathcal R$ class profilidir. Fakat rank-2'nin üç
48-state weather phase'i bu üç Green-$\mathcal R$ class ile aynı partition
değildir. Birbirlerini tam bir $3\times3$ grid olarak keserler:

| Green-$\mathcal R$ image class | funnel | gate | return |
|---|---:|---:|---:|
| image $\{1,h\}$ | 16 | 16 | 16 |
| image $\{1,q\}$ | 16 | 16 | 16 |
| image $\{h,q\}$ | 16 | 16 | 16 |

Green-$\mathcal R$ ekseni “hangi iki signed coordinate line korunuyor?” diye;
weather ekseni “rank düşüş çevriminin hangi fazındayız?” diye sorar. Aynı 144
state'i iki transverse yapısal koordinatla bölerler.

## Doğrulama ve sınır

Script:

- 192 state'in rank-output Moore minimization'ını yeniden yapar;
- beş bloktaki bütün symbol transition'larının stable olduğunu sınar;
- exact mean, second moment ve variance sistemlerini Fraction ile çözer;
- axis-labelled 21-block strong lumping'i kurar ve probability sum'ı 1 olarak
  doğrular;
- bütün SCC'leri çıkarır ve rank-2 $3\times3\times16$ transversality grid'ini
  denetler;
- `--deep-check` altında bağımsız Synchronizer Green-$\mathcal R$ ve minimum
  image sonuçlarıyla parity kurar.

**Exact:** literal dört generator, uniform $1/4$ seçim ve finite 192-state
automaton.

**İddia edilmeyen:** termodinamik equilibrium, fiziksel entropy üretimi,
gerçek-world randomness, non-uniform policy veya bu beş-state quotient'in
perturbed başka bir algebra için korunacağı.
