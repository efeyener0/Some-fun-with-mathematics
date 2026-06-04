/**
 * @file cebir_cuda.cu
 * @brief High-performance GPU-accelerated 3D holographic wave interference renderer
 *        for the non-associative projection algebra using CUDA.
 * 
 * Computes millions of coordinate transformations and wave packets on the GPU
 * and saves a high-resolution 2048x2048 PPM image.
 */

#include <iostream>
#include <fstream>
#include <cmath>
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

// CUDA constants representing the 6 inverse/pseudo-inverse matrices of the algebra elements
// {1, h, q, -1, -h, -q}
__constant__ float c_inv_matrices[6 * 9] = {
    // 0: L1_inv = Identity
    1.0f, 0.0f, 0.0f,  0.0f, 1.0f, 0.0f,  0.0f, 0.0f, 1.0f,
    // 1: Lh_inv = Transpose(Lh)
    0.0f, 1.0f, 0.0f,  0.0f, 0.0f, 1.0f,  1.0f, 0.0f, 0.0f,
    // 2: Lq_pinv (Pseudo-inverse of the non-invertible projection)
    0.0f, 0.0f, 1.0f, -1.0f, 0.0f, 0.0f,  0.0f, 0.0f, 0.0f,
    // 3: -L1_inv
   -1.0f, 0.0f, 0.0f,  0.0f,-1.0f, 0.0f,  0.0f, 0.0f,-1.0f,
    // 4: -Lh_inv
    0.0f,-1.0f, 0.0f,  0.0f, 0.0f,-1.0f, -1.0f, 0.0f, 0.0f,
    // 5: -Lq_pinv
    0.0f, 0.0f,-1.0f,  1.0f, 0.0f, 0.0f,  0.0f, 0.0f, 0.0f
};

// Superposition phase angles (c_g = exp(i * theta_g))
__constant__ float c_phases[6] = {
    0.0f,
    3.14159265f / 3.0f,       // pi/3
    2.0f * 3.14159265f / 3.0f,  // 2pi/3
    3.14159265f,              // pi
    4.0f * 3.14159265f / 3.0f,  // 4pi/3
    5.0f * 3.14159265f / 3.0f   // 5pi/3
};

// GPU structure to represent a RGB pixel
struct Pixel {
    unsigned char r, g, b;
};

/**
 * @brief CUDA Kernel to calculate the wave interference intensity at each pixel.
 * Utilizes GPU registers and fast math intrinsics for extreme performance.
 */
__global__ void render_interference_kernel(Pixel* output, int width, int height, float kx, float ky, float kz, float alpha, float zoom) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    if (x >= width || y >= height) return;

    // Convert pixel grid coordinates to physical space on the Z = 0 plane
    float fx = ((float)x / (float)width * 2.0f - 1.0f) * zoom;
    float fy = ((float)y / (float)height * 2.0f - 1.0f) * zoom;
    float fz = 0.0f;

    float psi_real = 0.0f;
    float psi_imag = 0.0f;
    float incoherent_sum = 0.0f;

    // Sum wave packets transformed by the 6 elements on the GPU
    #pragma unroll
    for (int g = 0; g < 6; ++g) {
        // Offset to access the 3x3 matrix coefficients
        int offset = g * 9;

        // Multiply coordinates by the inverse transformation matrix
        float rx = c_inv_matrices[offset + 0] * fx + c_inv_matrices[offset + 1] * fy + c_inv_matrices[offset + 2] * fz;
        float ry = c_inv_matrices[offset + 3] * fx + c_inv_matrices[offset + 4] * fy + c_inv_matrices[offset + 5] * fz;
        float rz = c_inv_matrices[offset + 6] * fx + c_inv_matrices[offset + 7] * fy + c_inv_matrices[offset + 8] * fz;

        // Compute Gaussian envelope: exp(-alpha * ||r||^2) using fast GPU intrinsic expf
        float d2 = rx * rx + ry * ry + rz * rz;
        float envelope = __expf(-alpha * d2);

        // Compute wave phase: cos(k * r) using fast GPU intrinsic cosf
        float phase_angle = kx * rx + ky * ry + kz * rz;
        float wave = envelope * __cosf(phase_angle);

        // Apply superposition phases c_g = exp(i * theta_g) using fast intrinsics
        float theta = c_phases[g];
        psi_real += wave * __cosf(theta);
        psi_imag += wave * __sinf(theta);
        incoherent_sum += wave * wave; // Incoherent sum of intensities (energy background)
    }

    // Compute coherent intensity: I = ||Psi||^2
    float coherent_intensity = psi_real * psi_real + psi_imag * psi_imag;

    // Compare coherent (phase-aware) vs incoherent (energy sum) intensity
    // diff > 0: Constructive interference (waves reinforce) -> Glowing Gold/Orange
    // diff < 0: Destructive interference (waves cancel)    -> Glowing Neon Cyan/Blue
    float diff = coherent_intensity - incoherent_sum;

    Pixel px;
    if (diff > 0.0f) {
        // Constructive Interference: Glowing Gold/Orange/White (Warm color palette)
        float val = sqrtf(diff * 20.0f);
        int r = (int)(val * 255.0f);
        int g = (int)(val * val * 190.0f);
        int b = (int)(val * val * val * 90.0f);
        px.r = (r > 255) ? 255 : (r < 0 ? 0 : r);
        px.g = (g > 255) ? 255 : (g < 0 ? 0 : g);
        px.b = (b > 255) ? 255 : (b < 0 ? 0 : b);
    } else {
        // Destructive Interference: Glowing Neon Cyan/Purple (Cool color palette)
        // Highlighting where phase cancellation occurs
        float val = sqrtf(-diff * 20.0f);
        int r = (int)(val * val * val * 100.0f);
        int g = (int)(val * val * 210.0f);
        int b = (int)(val * 255.0f);
        px.r = (r > 255) ? 255 : (r < 0 ? 0 : r);
        px.g = (g > 255) ? 255 : (g < 0 ? 0 : g);
        px.b = (b > 255) ? 255 : (b < 0 ? 0 : b);
    }

    // Flip vertically to match standard coordinate layout
    int target_idx = (height - 1 - y) * width + x;
    output[target_idx] = px;
}

int main() {
    const int width = 2048;
    const int height = 2048;
    const size_t buffer_size = width * height * sizeof(Pixel);

    std::cout << "==================================================" << std::endl;
    std::cout << "     CUDA HOLOGRAPHIC WAVE INTERFERENCE RENDERER" << std::endl;
    std::cout << "==================================================" << std::endl;

    // Define physical wave parameters
    float kx = 3.5f;
    float ky = 2.0f;
    float kz = 1.0f;
    float alpha = 0.40f;
    float zoom = 5.0f;

    std::cout << "Grid Resolution: " << width << " x " << height << " pixels" << std::endl;
    std::cout << "Calculations per pixel: 6 GPU transform operations" << std::endl;
    std::cout << "Total kernel evaluations: ~25.1 Million wave functions" << std::endl << std::endl;

    // 1. Allocate Host memory
    Pixel* host_pixels = (Pixel*)malloc(buffer_size);
    if (!host_pixels) {
        std::cerr << "Host memory allocation failed!" << std::endl;
        return -1;
    }

    // 2. Allocate Device memory
    Pixel* device_pixels = nullptr;
    cudaError_t err = cudaMalloc((void**)&device_pixels, buffer_size);
    if (err != cudaSuccess) {
        std::cerr << "GPU memory allocation failed: " << cudaGetErrorString(err) << std::endl;
        free(host_pixels);
        return -1;
    }

    // 3. Define block and grid configuration
    dim3 block(16, 16);
    dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);

    std::cout << "Launching GPU CUDA Kernel..." << std::endl;
    std::cout << "Block Size: " << block.x << "x" << block.y << std::endl;
    std::cout << "Grid Size: " << grid.x << "x" << grid.y << std::endl;

    // CUDA profiling event handles for accurate performance measurement
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);
    cudaEventRecord(start);

    // Launch the high-performance kernel
    render_interference_kernel<<<grid, block>>>(device_pixels, width, height, kx, ky, kz, alpha, zoom);

    cudaEventRecord(stop);
    cudaEventSynchronize(stop);

    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start, stop);

    // Check for kernel launch errors
    err = cudaGetLastError();
    if (err != cudaSuccess) {
        std::cerr << "Kernel launch failed: " << cudaGetErrorString(err) << std::endl;
        cudaFree(device_pixels);
        free(host_pixels);
        return -1;
    }

    std::cout << "GPU computation completed in " << milliseconds << " ms!" << std::endl;

    // 4. Copy rendered data from GPU to Host
    err = cudaMemcpy(host_pixels, device_pixels, buffer_size, cudaMemcpyDeviceToHost);
    if (err != cudaSuccess) {
        std::cerr << "Memcpy Device-to-Host failed: " << cudaGetErrorString(err) << std::endl;
        cudaFree(device_pixels);
        free(host_pixels);
        return -1;
    }

    // 5. Save the render buffer as a high-quality PPM file
    const std::string filename = "holographic_interference_cuda.ppm";
    std::cout << "Saving image to disk: " << filename << " ..." << std::endl;

    std::ofstream out(filename, std::ios::binary);
    if (!out.is_open()) {
        std::cerr << "Failed to create output image file!" << std::endl;
    } else {
        // Write the PPM P6 header
        out << "P6\n" << width << " " << height << "\n255\n";
        // Write binary pixel data
        out.write((char*)host_pixels, buffer_size);
        out.close();
        std::cout << "Image successfully written to: " << filename << std::endl;
    }

    // Cleanup resources
    cudaFree(device_pixels);
    free(host_pixels);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    std::cout << "GPU execution resource cleanup finished successfully." << std::endl;
    return 0;
}
