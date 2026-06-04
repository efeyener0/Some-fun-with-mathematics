# 🌌 2T-Fizik Tabanlı İzdüşümsel Kuantum Girişim Topolojisi (CUDA/C++)

Bu proje; değişmeli (non-commutative) ve birleşmeli olmayan (non-associative) idempotent projeksiyon cebrini ($q^2 = q$) 3 boyutlu uzayda modelleyen, **NVIDIA CUDA C++** ile ekran kartı üzerinde yüksek performanslı **3D Evre Girişimi (Phase-Interference)** hesaplamaları gerçekleştiren ve bunu **sıfır bağımlılıklı Win32/OpenGL** görüntüleyici ile interaktif 3D olarak canlandıran bilimsel bir görselleştirme ve analiz kütüphanesidir.

---

## 📖 1. Matematiksel Cebirsel Altyapı

Cebirimiz, değişmeli olmayan ve birleşmeli olmayan 6 elemanlı bir diskre kümeden oluşur:
$$\mathcal{G} = \{1, h, q, -1, -h, -q\}$$

Burada $1$ birim elemandır. Temel elemanlar arasındaki kurallar ve çarpım tablosu şu şekilde tanımlanmıştır:

* **$h^2 = q$**: Kiral salınımın (rotasyonel zaman) karesi sistemi doğrudan izdüşüm eksenine taşır.
* **$q^2 = q$**: İzdüşüm (projeksiyon) operatörünün karesi yine kendisini verir (**idempotency**). Bu özellik fiziksel olarak kararlı bir holografik sınır tanımlar.
* **Değişmesizlik (Non-commutativity)**: $h \cdot q = 1$ iken $q \cdot h = -1$ sonucunu verir.

### Çarpım Tablosu (Multiplication Table)

| $\cdot$ | **$1$** | **$h$** | **$q$** |
| :---: | :---: | :---: | :---: |
| **$1$** | $1$ | $h$ | $q$ |
| **$h$** | $h$ | $q$ | $1$ |
| **$q$** | $q$ | $-1$ | **$q$** |

### Spektral Temsil Teorisi (Spectral Representation)
Cebir, $\mathbb{R}^3$ uzayında baz vektörleri $\{e_1, e_h, e_q\}$ olan Left-Multiplication ($L_x(y) = x \cdot y$) matris temsilleriyle modellenmiştir:
* **$L_h$ (Rotasyon)**: $[1, 1, 1]^T$ ekseni etrafında $120^\circ$lik dairesel dönmeler yaratan döngüsel permütasyondur ($\lambda = 1, e^{i2\pi/3}, e^{-i2\pi/3}$).
* **$L_q$ (İzdüşüm)**: Sistemi $[0,0,1]^T$ kararlı projeksiyon eksenine kilitleyen projeksiyondur ($\lambda = 1, 0, 0$).

---

## 🌀 2. Hacimsel 3D Girişim Topolojisi ve Görselleştirme

Kuantum ve dalga mekaniğinde yıkıcı girişimlerin karanlıkta kalıp kaybolmasını engellemek amacıyla **Evre Duyarlı İki-Renkli Girişim Filtresi** geliştirilmiştir.

GPU üzerinde her bir $\mathbf{x} \in \mathbb{R}^3$ noktası için iki farklı dalga yoğunluğu hesaplanır:

1. **Uyumlu Yoğunluk (Coherent Intensity - $I_{coherent}$)**: Dalgaların faz farklarıyla süperpoze olduğu toplam genliğin karesi:
   $$I_{coherent}(\mathbf{x}) = \left| \sum_g \psi(L_g^{-1} \mathbf{x}) \right|^2$$
2. **Uyumsuz Yoğunluk (Incoherent Intensity - $I_{incoherent}$)**: Sadece dalgaların taşıdığı enerjilerin toplamı:
   $$I_{incoherent}(\mathbf{x}) = \sum_g \left| \psi(L_g^{-1} \mathbf{x}) \right|^2$$

Bu iki yoğunluğun farkı ($\Delta I = I_{coherent} - I_{incoherent}$) faz geometrisini belirler:
* **$\Delta I > \text{Threshold}$ (Yapıcı Girişim)**: Dalgaların tepe noktalarının üst üste bindiği alanları gösterir. **Akkor Altın ve Sıcak Turuncu** renkte parlar.
* **$\Delta I < -\text{Threshold}$ (Yıkıcı Girişim)**: Dalgaların birbirini söndürdüğü evre iptallerini gösterir. **Neon Mavi ve Turkuaz** renkte parlar.

---

## ⚡ 3. C++/CUDA Yüksek Performanslı Mimari

Hesaplama yükü, NVIDIA GPU'ların paralel mimarisinden en üst düzeyde faydalanacak şekilde tasarlanmıştır:
* **Constant Memory (`__constant__`)**: Matrisler ve evre katsayıları sıfır gecikmeli sabit bellekte saklanır.
* **GPU Intrinsics**: Ekran kartının register'ları üzerinde doğrudan işlenen `__expf` ve `__cosf` gibi hızlı donanımsal fonksiyonlar kullanılmıştır.
* **Adaptif Zarf Eşiği (Adaptive Envelope)**: Gaussian sönümünü kompanse eden dinamik filtre sayesinde, merkezden uzaktaki sönük dalga kabuklarının da parlaması sağlanmıştır.

---

## 💡 4. Potansiyel Uygulama Alanları

Bu özgün değişmeli ve birleşmeli olmayan projeksiyon cebri, modern fizik ve bilgi kuramında birçok yenilikçi uygulama alanına sahiptir:

### A. 2T-Fizik (İki Zamanlı Fizik) ve Holografi
* İki zaman boyutuna sahip kozmolojik teorilerde nedensellik (causality) ihlallerini ve kapalı zamansal eğrileri (CTC) engellemek için **Gauge/Projeksiyon simetrileri** şarttır.
* $q^2 = q$ idempotent kuralı, fazladan olan zaman boyutunu bizim algıladığımız 1 zamanlı dünyaya kararlı bir şekilde **holografik olarak projekte eden** perde görevi görür. Girişim desenindeki elektrik mavisi tüneller zaman boyutunun sönümlendiği fazları görselleştirir.

### B. Topolojik Kuantum Hesaplama (Topological Quantum Computing)
* Kuantum bilgisayarlarında gürültüye karşı korumalı topolojik kübitler tasarlamak için birleşmeli olmayan örgüler (non-associative braiding) kullanılır (örneğin Octonion veya non-abelian anyon sistemleri).
* Bu cebirdeki yön-bağımlı birleşmeme anomalileri ve evre fazları, hataya toleranslı kuantum kapılarının modellenmesinde kullanılabilir.

### C. Kiral Optik ve Metamalzemeler (Chiral Metamaterials)
* $120^\circ$lik dairesel simetri ($h$) ve yön-bağımlı değişmesizlik ($q \cdot h \neq h \cdot q$), ışığı tek yönde geçiren (non-reciprocal) optik izolatörlerin ve metamalzemelerin tasarımı için matematiksel altyapı sağlar.
* Dalga girişimindeki kiral girdaplar, ışığın polarizasyon durumlarını ve kiral saçılımlarını simüle etmek için kullanılabilir.

---

## 🚀 5. Nasıl Derlenir ve Çalıştırılır?

Projede yer alan tüm araçlar **sıfır harici kütüphane bağımlılığına** sahiptir. Windows platformunda yerleşik MSVC ve CUDA SDK derleyicileri ile doğrudan derlenebilirler.

### A. 3D Girişim Nokta Bulutunun GPU Üzerinde Render Edilmesi
CUDA kodunu derleyip $160 \times 160 \times 160$ çözünürlüğünde 3D dalga topolojisi üreten çalıştırılabilir dosyayı oluşturun:

```bash
# NVIDIA CUDA Compiler ile derleme (Constant Memory & O3 Optimize)
nvcc -O3 cebir_cuda_3d.cu -o cebir_cuda_3d.exe

# GPU Render'ını başlatma (~24.5 Milyon işlem GPU'da 30 ms sürer)
.\cebir_cuda_3d.exe
```
*Bu işlem sonucunda diskte `holographic_interference_3d.ply` (~130 MB) adında 3.08 Milyon aktif renkli noktadan oluşan 3D model dosyası üretilir.*

### B. İnteraktif 3D OpenGL Görüntüleyicinin Derlenmesi ve Çalıştırılması
Üretilen 3D PLY dosyasını, fareyle serbestçe döndürüp yakınlaşarak inceleyebileceğiniz yerel Windows programını derleyin:

```bash
# MSVC ile Windows subsystem standartlarında derleme (OpenGL32 ve GLU32 yerleşik bağlanır)
cl.exe /EHsc /O2 cebir_viewer.cpp /link /subsystem:windows

# Programı çalıştırma
.\cebir_viewer.exe
```

#### 🎮 Görüntüleyici Kontrolleri:
* **Sol Tık + Sürükle**: 3D dalga topolojisini kendi etrafında 360 derece **döndürür**.
* **Sağ Tık + Sürükle**: Kamerayı yukarı, aşağı, sağa ve sola **kaydırır (pan)**.
* **Fare Tekerleği (Scroll)**: 3D uzayda **yakınlaşır / uzaklaşır**.
* **Klavye 'R' Tuşu**: Kamerayı başlangıç konumuna **sıfırlar**.
