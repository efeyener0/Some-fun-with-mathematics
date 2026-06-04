/**
 * @file cebir_cuda_3d.cu
 * @brief High-performance GPU-accelerated 3D wave interference volumetric renderer
 *        that exports a 3D PLY color point cloud of the algebra's topology using CUDA.
 * 
 * Computes 24.5 Million 3D wave transformations on the GPU, applies an adaptive
 * topological envelope threshold, and saves the 3D structure as a PLY file.
 */

#include <iostream>
#include <fstream>
#include <vector>
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

// Structure for a 3D Point with color and active state
struct Point3D {
    float x, y, z;
    unsigned char r, g, b;
    unsigned char active;
};

/**
 * @brief CUDA Kernel to calculate the 3D wave interference at each grid node.
 * Evaluates the 3D space and maps constructive vs destructive phase states.
 */
__global__ void render_interference_3d_kernel(Point3D* output, int dim, float kx, float ky, float kz, float alpha, float zoom) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;

    if (x >= dim || y >= dim || z >= dim) return;

    // Convert pixel grid coordinates to physical space in 3D
    float fx = ((float)x / (float)dim * 2.0f - 1.0f) * zoom;
    float fy = ((float)y / (float)dim * 2.0f - 1.0f) * zoom;
    float fz = ((float)z / (float)dim * 2.0f - 1.0f) * zoom;

    float psi_real = 0.0f;
    float psi_imag = 0.0f;
    float incoherent_sum = 0.0f;

    // Sum wave packets transformed by the 6 elements on the GPU
    #pragma unroll
    for (int g = 0; g < 6; ++g) {
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
        incoherent_sum += wave * wave; // Incoherent sum of intensities
    }

    // Compute coherent intensity: I = ||Psi||^2
    float coherent_intensity = psi_real * psi_real + psi_imag * psi_imag;

    // Compare coherent vs incoherent intensity to find phase states
    float diff = coherent_intensity - incoherent_sum;
    float abs_diff = fabsf(diff);

    // Adaptive threshold based on distance from origin to show outer shells beautifully
    float d2_origin = fx * fx + fy * fy + fz * fz;
    float adaptive_threshold = 0.04f * __expf(-alpha * d2_origin * 0.8f);

    int target_idx = z * dim * dim + y * dim + x;
    Point3D& p = output[target_idx];
    p.x = fx;
    p.y = fy;
    p.z = fz;

    if (abs_diff > adaptive_threshold) {
        p.active = 1;
        if (diff > 0.0f) {
            // Constructive Interference: Glowing Gold/Orange (Warm color palette)
            float val = sqrtf(diff * 20.0f);
            int r = (int)(val * 255.0f);
            int g = (int)(val * val * 190.0f);
            int b = (int)(val * val * val * 90.0f);
            p.r = (r > 255) ? 255 : (r < 0 ? 0 : r);
            p.g = (g > 255) ? 255 : (g < 0 ? 0 : g);
            p.b = (b > 255) ? 255 : (b < 0 ? 0 : b);
        } else {
            // Destructive Interference: Glowing Neon Cyan/Blue (Cool color palette)
            float val = sqrtf(-diff * 20.0f);
            int r = (int)(val * val * val * 100.0f);
            int g = (int)(val * val * 210.0f);
            int b = (int)(val * 255.0f);
            p.r = (r > 255) ? 255 : (r < 0 ? 0 : r);
            p.g = (g > 255) ? 255 : (g < 0 ? 0 : g);
            p.b = (b > 255) ? 255 : (b < 0 ? 0 : b);
        }
    } else {
        p.active = 0;
    }
}

int main() {
    const int dim = 160; // 3D Grid dimension (160^3 = 4,096,000 grid points)
    const size_t num_points = dim * dim * dim;
    const size_t buffer_size = num_points * sizeof(Point3D);

    std::cout << "==================================================" << std::endl;
    std::cout << "     CUDA 3D HOLOGRAPHIC VOLUMETRIC PLY RENDERER" << std::endl;
    std::cout << "==================================================" << std::endl;

    // Define physical wave parameters
    float kx = 3.5f;
    float ky = 2.0f;
    float kz = 1.0f;
    float alpha = 0.40f;
    float zoom = 3.0f; // Zoom in to capture the core structures clearly

    std::cout << "Grid Resolution: " << dim << " x " << dim << " x " << dim << " points" << std::endl;
    std::cout << "Total kernel evaluations: ~24.5 Million 3D wave functions" << std::endl << std::endl;

    // 1. Allocate Host memory
    Point3D* host_points = (Point3D*)malloc(buffer_size);
    if (!host_points) {
        std::cerr << "Host memory allocation failed!" << std::endl;
        return -1;
    }

    // 2. Allocate Device memory
    Point3D* device_points = nullptr;
    cudaError_t err = cudaMalloc((void**)&device_points, buffer_size);
    if (err != cudaSuccess) {
        std::cerr << "GPU memory allocation failed: " << cudaGetErrorString(err) << std::endl;
        free(host_points);
        return -1;
    }

    // 3. Define block and grid configuration (3D block and grid)
    dim3 block(8, 8, 8); // 8*8*8 = 512 threads per block
    dim3 grid((dim + block.x - 1) / block.x, (dim + block.y - 1) / block.y, (dim + block.z - 1) / block.z);

    std::cout << "Launching GPU CUDA Volumetric Kernel..." << std::endl;
    
    // Time the computation
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);
    cudaEventRecord(start);

    // Launch the 3D volumetric kernel
    render_interference_3d_kernel<<<grid, block>>>(device_points, dim, kx, ky, kz, alpha, zoom);

    cudaEventRecord(stop);
    cudaEventSynchronize(stop);

    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start, stop);

    err = cudaGetLastError();
    if (err != cudaSuccess) {
        std::cerr << "Kernel launch failed: " << cudaGetErrorString(err) << std::endl;
        cudaFree(device_points);
        free(host_points);
        return -1;
    }

    std::cout << "GPU computation completed in " << milliseconds << " ms!" << std::endl;

    // 4. Copy rendered volumetric points from GPU to Host
    std::cout << "Copying 3D volume buffer from GPU..." << std::endl;
    err = cudaMemcpy(host_points, device_points, buffer_size, cudaMemcpyDeviceToHost);
    if (err != cudaSuccess) {
        std::cerr << "Memcpy Device-to-Host failed: " << cudaGetErrorString(err) << std::endl;
        cudaFree(device_points);
        free(host_points);
        return -1;
    }

    // 5. Count active surface points and write the 3D PLY file
    std::cout << "Filtering volumetric points..." << std::endl;
    std::vector<Point3D> active_points;
    active_points.reserve(num_points / 10); // Reserve memory to avoid reallocations

    for (size_t i = 0; i < num_points; ++i) {
        if (host_points[i].active) {
            active_points.push_back(host_points[i]);
        }
    }

    const std::string filename = "holographic_interference_3d.ply";
    std::cout << "Active surface points to export: " << active_points.size() << std::endl;
    std::cout << "Saving 3D PLY file to disk: " << filename << " ..." << std::endl;

    std::ofstream out(filename);
    if (!out.is_open()) {
        std::cerr << "Failed to create output 3D file!" << std::endl;
    } else {
        // Write the PLY header for color vertices
        out << "ply\n";
        out << "format ascii 1.0\n";
        out << "element vertex " << active_points.size() << "\n";
        out << "property float x\n";
        out << "property float y\n";
        out << "property float z\n";
        out << "property uchar red\n";
        out << "property uchar green\n";
        out << "property uchar blue\n";
        out << "end_header\n";

        // Write vertices (coordinates and colors)
        for (const auto& p : active_points) {
            out << p.x << " " << p.y << " " << p.z << " "
                << (int)p.r << " " << (int)p.g << " " << (int)p.b << "\n";
        }
        out.close();
        std::cout << "3D PLY file successfully written to: " << filename << std::endl;
    }

    // Cleanup resources
    cudaFree(device_points);
    free(host_points);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    std::cout << "GPU execution resource cleanup finished successfully." << std::endl;
    return 0;
}
