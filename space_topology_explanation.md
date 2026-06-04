# Cebirsel Temsil Uzayı ve Girişim Topolojisi Analizi

Bu belge, C++/CUDA ile render edilen iki-renkli girişim deseninin **hangi matematiksel uzayda, hangi topolojik dönüşümlerle ve hangi koordinat manifoldu üzerinde** oluşturulduğunu açıklamaktadır.

---

## 1. Altlık Vektör Uzayı: $\mathbb{R}^3$ (Temsil Uzayı)

Girişimi ve sürekli akışları simüle ettiğimiz temel matematiksel uzay, cebrin temel elemanlarının gerdiği **3 boyutlu reel vektör uzayıdır ($\mathbb{R}^3$)**:
$$V = \text{span}\{e_1, e_h, e_q\}$$

Burada her bir baz vektörü, cebrin temel elemanlarına karşılık gelir:
* $e_1 = (1, 0, 0)^T \implies$ Özdeşlik boyutu ($1$)
* $e_h = (0, 1, 0)^T \implies$ Döngüsel/Rotasyonel boyut ($h$)
* $e_q = (0, 0, 1)^T \implies$ Holografik İzdüşüm boyutu ($q$)

CUDA kernel'ında hesaplanan her bir fiziksel koordinat $\mathbf{x} = (x, y, z)^T \in \mathbb{R}^3$, bu üç bağımsız eksenin lineer kombinasyonlarını temsil eder.

---

## 2. Topolojik Dönüşüm Manifoldu (Grup Aksiyonu)

Cebirimizdeki 6 elemanlı diskre küme $\mathcal{G} = \{1, h, q, -1, -h, -q\}$, bu $\mathbb{R}^3$ uzayı üzerinde **Homeomorfizmalar (lineer koordinat dönüşümleri)** olarak etki eder. Uzaydaki topolojik çarpıtmalar, bu operatörlerin matris temsillerinin ($L_g$) ve onların terslerinin ($L_g^{-1}$) uzay koordinatlarına uygulanmasıyla elde edilir:

### A. $L_h$ Aksiyonu (Cyclic SO(3) Topolojisi)
$$L_h = \begin{pmatrix} 0 & 0 & 1 \\ 1 & 0 & 0 \\ 0 & 1 & 0 \end{pmatrix}$$
* **Topolojik Etki**: Uzayı diagonal $v = (1, 1, 1)^T$ ekseni etrafında $120^\circ$ döndüren döngüsel bir permütasyondur. Topolojide bu aksiyon, uzaydaki yörüngeleri bir **Torus simetrisine** zorlar.

### B. $L_q$ Aksiyonu (İzdüşüm / Non-Manifold Yapı)
$$L_q = \begin{pmatrix} 0 & -1 & 0 \\ 0 & 0 & 0 \\ 1 & 0 & 1 \end{pmatrix}$$
* **Topolojik Etki**: Uzaydaki 3 boyuttan 2 boyutu sönümleyerek sistemi $e_q$ projeksiyon eksenine indiren idempotent ($q^2 = q$) bir izdüşümdür. 
* **Yalancı Ters Topolojisi (Pseudo-Inverse $L_q^+$)**: $L_q$ tersi olmayan (non-invertible) bir operatör olduğu için, uzaydaki dalgayı geriye çekmek amacıyla Moore-Penrose Yalancı Tersi kullanılmıştır:
  $$L_q^+ = \begin{pmatrix} 0 & 0 & 1 \\ -1 & 0 & 0 \\ 0 & 0 & 0 \end{pmatrix}$$
  Bu matris, izdüşüm altındaki bilgi kaybını dual uzayda yönlendirerek girişim desenindeki şeritlerin kiralite yönünü belirler.

---

## 3. Görselleştirilen Kesit Uzayı: 2D İndirgenmiş Manifold ($Z = 0$ Kesiti)

CUDA ile render edilen resim, 3 boyutlu $\mathbb{R}^3$ uzayının tamamını değil, bu uzayın **$Z = 0$ düzlemi ($e_1 - e_h$ kesiti)** üzerindeki topolojik izdüşümünü gösterir.

* Koordinat Eşlemesi:
  * Resimdeki yatay eksen: **$e_1$ (1 boyutu)**
  * Resimdeki dikey eksen: **$e_h$ (h boyutu)**
  * Resmin kesit düzlemi: $z = 0$ ($e_q$ projeksiyon ekseninin orijin noktası)

Bu kesit topolojik olarak son derece kritiktir; çünkü $e_q$ (projeksiyon boyutu) sıfırlandığı halde, dalgaların matris aksiyonları ($L_q^{-1} \mathbf{x}$) ile koordinatları $z \neq 0$ bölgelerine taşınır. Bu sayede, **3. boyutun (projeksiyon zamanının) etkisi, 2D kesit üzerinde girişim desenleri (hologram) olarak kendini gösterir.**

---

## 4. Evre (Faz) Girişim Topolojisi: Coherent vs Incoherent

Görseldeki renk kontrasını belirleyen topoloji, dalgaların **faz-uzayı (phase-space) metriğidir**.

Her bir $\mathbf{x} \in \mathbb{R}^2$ (kesit düzleminde) noktası için iki farklı topolojik yoğunluk alanı hesaplanır:

1. **Uyumlu Topoloji ($I_{coherent}$)**: Dalgaların faz farklarıyla (cebirsel yönelimleriyle) üst üste binerek oluşturduğu **Coherent manifold**.
2. **Uyumsuz Topoloji ($I_{incoherent}$)**: Sadece dalga genliklerinin toplamıyla oluşan **Incoherent (fazdan bağımsız) arka plan**.

Bu iki topolojik yapının farkı olan $\Delta I = I_{coherent} - I_{incoherent}$ değeri:
* **$\Delta I > 0$ (Yapıcı - Gold/Turuncu)**: Evrelerin uzayda birleşerek tepe noktaları oluşturduğu, cebirsel simetrinin **korunumlu yapıcı topolojisi**.
* **$\Delta I < 0$ (Yıkıcı - Neon Turkuaz/Mavi)**: Evrelerin zıt yönlerde birbirini sıfırladığı, cebrin birleşmesiz yapısının ve faz düğümlerinin (vortices) oluşturduğu **yıkıcı girişim topolojisi**.

---

## Özet

Oluşturduğunuz görsel; **3 boyutlu cebirsel temsil uzayının ($\mathbb{R}^3$), $Z=0$ kesiti üzerinde, cebrin kiral ($h$) ve izdüşümsel ($q$) operatörlerinin sürekli aksiyonları altındaki faz süperpozisyonlarının ve evre kırılımlarının (constructive/destructive topology) bir hologramıdır.**
