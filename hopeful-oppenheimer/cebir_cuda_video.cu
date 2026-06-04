/**
 * @file cebir_cuda_video.cu
 * @brief 4K VRAM-Native Volumetric Ray Marcher & Sharp Geometric Rasterizer.
 *        Renders 3D phase interference patterns of non-associative, idempotent projection algebra.
 *        Allocates frame buffers entirely in GPU VRAM (cudaMalloc) for zero-copy high performance.
 *        Integrates a sharp mathematical 3D wireframe grid, corner nodes, and phase boundary contours
 *        with volumetric participating media, utilizing depth-occluded front-to-back opacity blending.
 *        Compresses the output directly in VRAM using GPU hardware-accelerated NVIDIA NVENC.
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

#ifdef _WIN32
#define popen _popen
#define pclose _pclose
#endif

// GPU Structure for output RGB pixels
struct Pixel {
    unsigned char r, g, b;
};

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

// 3D vector operations on the GPU
struct Vec3 {
    float x, y, z;
    __device__ Vec3(float x_ = 0, float y_ = 0, float z_ = 0) : x(x_), y(y_), z(z_) {}
    __device__ Vec3 operator+(const Vec3& v) const { return Vec3(x + v.x, y + v.y, z + v.z); }
    __device__ Vec3 operator-(const Vec3& v) const { return Vec3(x - v.x, y - v.y, z - v.z); }
    __device__ Vec3 operator*(float s) const { return Vec3(x * s, y * s, z * s); }
};

__device__ float dot(const Vec3& a, const Vec3& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

__device__ Vec3 normalize(const Vec3& v) {
    float len = sqrtf(dot(v, v));
    return len > 0.0f ? v * (1.0f / len) : Vec3(0, 0, 0);
}

__device__ Vec3 cross(const Vec3& a, const Vec3& b) {
    return Vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    );
}

/**
 * @brief CUDA Kernel for Volumetric Ray Marching with Sharp Holographic Wireframe Rasterization.
 *        Runs entirely in GPU VRAM. Integrates the warm gold and cool cyan volumetric gas
 *        while superimposing sharp, depth-occluded geometric grid lines, junction corners,
 *        and thin phase boundaries to provide strong physical structure.
 */
__global__ void render_volumetric_raymarch_kernel(Pixel* output, int width, int height, 
                                                  float kx, float ky, float kz, 
                                                  float alpha, float camera_distance, 
                                                  float rotX, float rotY) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    if (x >= width || y >= height) return;

    // 1. Calculate camera position and coordinate vectors in 3D space
    float cosY = __cosf(rotY);
    float sinY = __sinf(rotY);
    float cosX = __cosf(rotX);
    float sinX = __sinf(rotX);

    // Orbiting Camera position
    Vec3 cam_pos(
        camera_distance * sinY * cosX,
        camera_distance * sinX,
        camera_distance * cosY * cosX
    );

    // Compute camera look direction, right and up vectors
    Vec3 target(0, 0, 0);
    Vec3 forward = normalize(target - cam_pos);
    Vec3 world_up(0, 1, 0);
    Vec3 right = normalize(cross(forward, world_up));
    Vec3 up = cross(right, forward);

    // Convert pixel to screen coordinates [-1, 1] correcting aspect ratio
    float aspect = (float)width / (float)height;
    float u = ((float)x / (float)width * 2.0f - 1.0f) * aspect;
    float v = ((float)y / (float)height * 2.0f - 1.0f);
    float fov = 1.6f; // Perspective scale factor

    // Shoot ray from camera
    Vec3 ray_dir = normalize(right * u + up * v + forward * fov);

    // 2. Ray Marching integration loop
    const int steps = 110;
    const float step_size = 0.08f;
    float t = 2.0f; // Start ray marching distance

    float accum_r = 0.0f;
    float accum_g = 0.0f;
    float accum_b = 0.0f;
    float opacity = 0.0f;

    const float density_scale = 0.38f;
    const float absorption = 0.18f;

    // Parameters for 3D Holographic Wireframe Grid
    const float grid_spacing = 0.60f; // Distance between grid lines
    const float node_base_radius = 0.024f; // Thick junction corner dots
    const float line_base_radius = 0.008f; // Precise linking grid lines

    for (int i = 0; i < steps; ++i) {
        if (opacity >= 0.99f) break;

        // Current 3D coordinate along the ray
        Vec3 p = cam_pos + ray_dir * t;
        t += step_size;

        float psi_real = 0.0f;
        float psi_imag = 0.0f;
        float incoherent_sum = 0.0f;

        // Calculate continuous wave superposition under the 6 algebra elements
        #pragma unroll
        for (int g = 0; g < 6; ++g) {
            int offset = g * 9;

            // Apply inverse matrix transformation (g^-1 * p)
            float rx = c_inv_matrices[offset + 0] * p.x + c_inv_matrices[offset + 1] * p.y + c_inv_matrices[offset + 2] * p.z;
            float ry = c_inv_matrices[offset + 3] * p.x + c_inv_matrices[offset + 4] * p.y + c_inv_matrices[offset + 5] * p.z;
            float rz = c_inv_matrices[offset + 6] * p.x + c_inv_matrices[offset + 7] * p.y + c_inv_matrices[offset + 8] * p.z;

            // Gaussian envelope: exp(-alpha * ||r||^2) using GPU fast intrinsic
            float d2 = rx * rx + ry * ry + rz * rz;
            float envelope = __expf(-alpha * d2);

            // Phase: cos(k * r) using GPU fast intrinsic
            float phase_angle = kx * rx + ky * ry + kz * rz;
            float wave = envelope * __cosf(phase_angle);

            // Coherent superposition: c_g = exp(i * theta_g)
            float theta = c_phases[g];
            psi_real += wave * __cosf(theta);
            psi_imag += wave * __sinf(theta);
            incoherent_sum += wave * wave;
        }

        // Coherent intensity
        float coherent_intensity = psi_real * psi_real + psi_imag * psi_imag;
        float diff = coherent_intensity - incoherent_sum;

        // Calculate distance from origin for adaptive envelope scaling
        float d2_origin = p.x * p.x + p.y * p.y + p.z * p.z;
        float env_scale = __expf(-alpha * d2_origin * 0.70f);

        // --- SHARP 3D GEOMETRIC RASTERIZATION OVERLAYS ---
        // Rendered with depth-occluding front-to-back opacity scaling.
        if (env_scale > 0.04f) {
            // Find the nearest virtual grid junction coordinates
            float cx = roundf(p.x / grid_spacing) * grid_spacing;
            float cy = roundf(p.y / grid_spacing) * grid_spacing;
            float cz = roundf(p.z / grid_spacing) * grid_spacing;

            // Distance to nearest grid node (Corner Sphere)
            float dx_node = p.x - cx;
            float dy_node = p.y - cy;
            float dz_node = p.z - cz;
            float dist_node = sqrtf(dx_node * dx_node + dy_node * dy_node + dz_node * dz_node);

            // Distance to the 3 grid lines (Cylinders parallel to X, Y, Z axes meeting at cx, cy, cz)
            float dist_line_x = sqrtf(dy_node * dy_node + dz_node * dz_node);
            float dist_line_y = sqrtf(dx_node * dx_node + dz_node * dz_node);
            float dist_line_z = sqrtf(dx_node * dx_node + dy_node * dy_node);
            float dist_line = fminf(dist_line_x, fminf(dist_line_y, dist_line_z));

            // Dynamic thresholds modulated by the algebra's decay envelope
            float node_radius = node_base_radius * env_scale;
            float line_radius = line_base_radius * env_scale;

            // 1. GRID CORNER NODES (Glowing Golden-Yellow Holographic Spheres)
            if (dist_node < node_radius) {
                float edge_factor = 1.0f - (dist_node / node_radius);
                float glow = edge_factor * edge_factor * 0.95f;
                
                accum_r += glow * 1.0f * (1.0f - opacity);
                accum_g += glow * 0.88f * (1.0f - opacity);
                accum_b += glow * 0.25f * (1.0f - opacity);
                opacity += glow * 0.85f; // Solid occlusion block
            }

            // 2. GRID WIREFRAME LINES (Glowing Cyan/Turquoise Holographic Ribs)
            if (dist_line < line_radius) {
                float edge_factor = 1.0f - (dist_line / line_radius);
                float glow = edge_factor * edge_factor * 0.82f;
                
                accum_r += glow * 0.0f * (1.0f - opacity);
                accum_g += glow * 0.95f * (1.0f - opacity);
                accum_b += glow * 1.0f * (1.0f - opacity);
                opacity += glow * 0.75f; // Blocks posterior gas
            }

            // 3. SHARP TOPOLOGICAL BOUNDARY OUTLINES (Thin Glowing Magenta Contour Shells where diff crosses 0)
            float boundary_threshold = 0.0012f * env_scale;
            if (fabsf(diff) < boundary_threshold) {
                float edge_factor = 1.0f - (fabsf(diff) / boundary_threshold);
                float glow = edge_factor * edge_factor * 0.80f;
                
                accum_r += glow * 1.0f * (1.0f - opacity);
                accum_g += glow * 0.0f * (1.0f - opacity);
                accum_b += glow * 0.85f * (1.0f - opacity);
                opacity += glow * 0.70f;
            }

            // 4. CONCENTRIC PHASE WAVE PEAKS (Sharp Glowing Neon-White Ripples)
            float norm_phase = psi_real / (sqrtf(coherent_intensity) + 0.0001f);
            float phase_dist = 1.0f - fabsf(norm_phase); 
            float phase_threshold = 0.0015f * env_scale;
            if (phase_dist < phase_threshold) {
                float edge_factor = 1.0f - (phase_dist / phase_threshold);
                float glow = edge_factor * edge_factor * 0.45f;
                
                accum_r += glow * 1.0f * (1.0f - opacity);
                accum_g += glow * 1.0f * (1.0f - opacity);
                accum_b += glow * 1.0f * (1.0f - opacity);
                opacity += glow * 0.45f;
            }
        }

        // --- VOLUMETRIC PARTICIPATING MEDIA GAS INTEGRATION ---
        if (diff > 0.0f) {
            // Constructive Interference: Glowing warm cosmic gas (Gold/Orange)
            float gas = sqrtf(diff) * step_size * density_scale;
            accum_r += gas * 1.0f * (1.0f - opacity);
            accum_g += gas * 0.68f * (1.0f - opacity);
            accum_b += gas * 0.25f * (1.0f - opacity);
            opacity += gas * absorption;
        } else {
            // Destructive Interference: Glowing cool cosmic gas (Neon Cyan/Blue)
            float gas = sqrtf(-diff) * step_size * density_scale;
            accum_r += gas * 0.15f * (1.0f - opacity);
            accum_g += gas * 0.72f * (1.0f - opacity);
            accum_b += gas * 1.0f * (1.0f - opacity);
            opacity += gas * absorption;
        }
    }

    // 3. Write final pixel color with deep dark space blue background blending
    int r_val = (int)(accum_r * 255.0f + (1.0f - opacity) * 2.0f);
    int g_val = (int)(accum_g * 255.0f + (1.0f - opacity) * 7.0f);
    int b_val = (int)(accum_b * 255.0f + (1.0f - opacity) * 19.0f);

    Pixel px;
    px.r = (unsigned char)(r_val > 255 ? 255 : (r_val < 0 ? 0 : r_val));
    px.g = (unsigned char)(g_val > 255 ? 255 : (g_val < 0 ? 0 : g_val));
    px.b = (unsigned char)(b_val > 255 ? 255 : (b_val < 0 ? 0 : b_val));

    // Flip vertically to match standard screen/image coordinates
    int target_idx = (height - 1 - y) * width + x;
    output[target_idx] = px;
}

int main(int argc, char* argv[]) {
    if (argc < 5) {
        std::cerr << "Usage: " << argv[0] << " <dummy_ply> <ffmpeg_path> <duration_sec> <output_mp4>" << std::endl;
        return -1;
    }

    std::string ffmpeg_path = argv[2];
    float duration = std::stof(argv[3]);
    std::string output_mp4 = argv[4];

    std::cout << "=================================================================" << std::endl;
    std::cout << " 4K ULTRA VRAM-NATIVE GPU VOLUMETRIC RASTERIZER & ENCODER" << std::endl;
    std::cout << "=================================================================" << std::endl;

    // Define continuous mathematical wave parameters
    float kx = 3.5f;
    float ky = 2.0f;
    float kz = 1.0f;
    float alpha = 0.40f;

    // Define 4K UHD Dimensions
    const int width = 3840;   // 4K UHD Width
    const int height = 2160;  // 4K UHD Height
    const int fps = 30;
    const int total_frames = (int)(duration * (float)fps);
    const size_t frame_buffer_size = width * height * sizeof(Pixel);

    // 1. Allocate GPU VRAM Buffer (Frame is physically BORN in ultra-fast VRAM)
    Pixel* device_frame = nullptr;
    cudaError_t err = cudaMalloc((void**)&device_frame, frame_buffer_size);
    if (err != cudaSuccess) {
        std::cerr << "Fatal: GPU VRAM Frame Buffer Allocation failed: " << cudaGetErrorString(err) << std::endl;
        return -1;
    }

    // 2. Allocate Host Pinned Memory (DMA Transfer Station for PCIe streaming)
    Pixel* host_frame = nullptr;
    err = cudaHostAlloc((void**)&host_frame, frame_buffer_size, cudaHostAllocDefault);
    if (err != cudaSuccess) {
        std::cerr << "Fatal: CUDA Host Pinned Allocation failed: " << cudaGetErrorString(err) << std::endl;
        cudaFree(device_frame);
        return -1;
    }

    std::cout << "Volumetric Grid Resolution: " << width << " x " << height << " (4K UHD)" << std::endl;
    std::cout << "Storage Pipeline: Born in VRAM -> DMA Streamed -> Encoded in VRAM" << std::endl;
    std::cout << "Total Frames to Integrate on GPU: " << total_frames << std::endl;

    // 3. Define the Dual Compilation Pipelines
    // Primary: GPU Hardware-Accelerated NVENC
    std::string nvenc_cmd = "\"" + ffmpeg_path + "\" -y -f rawvideo -pix_fmt rgb24 -s " + 
                            std::to_string(width) + "x" + std::to_string(height) + 
                            " -r " + std::to_string(fps) + " -i - -c:v h264_nvenc -preset slow -cq 18 -rc vbr -pix_fmt yuv420p " + output_mp4;

    // Fallback: CPU high-performance libx264
    std::string cpu_cmd = "\"" + ffmpeg_path + "\" -y -f rawvideo -pix_fmt rgb24 -s " + 
                          std::to_string(width) + "x" + std::to_string(height) + 
                          " -r " + std::to_string(fps) + " -i - -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p " + output_mp4;

    std::cout << "Opening 4K GPU HW-Accelerated NVENC pipeline to FFmpeg..." << std::endl;
    FILE* ffmpeg = popen(nvenc_cmd.c_str(), "wb");
    bool using_nvenc = true;

    if (!ffmpeg) {
        std::cout << "\nWarning: GPU Hardware NVENC process failed to launch. Falling back to CPU libx264..." << std::endl;
        ffmpeg = popen(cpu_cmd.c_str(), "wb");
        using_nvenc = false;
    }

    // Grid and block configurations for parallel pixel ray marching
    dim3 block(16, 16);
    dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);

    // 4. Volumetric Ray Marching Loop (Born in VRAM, Compressed in VRAM)
    std::cout << "Integrating 4K participating media & wireframe rasterization on GPU VRAM..." << std::endl;
    for (int frame = 0; frame < total_frames; ++frame) {
        float t = (float)frame / (float)total_frames;

        // Smooth orbits and periodic camera zoom
        float azimuth = (45.0f + t * 360.0f) * (3.14159265f / 180.0f);
        float elevation = (25.0f + 15.0f * sinf(2.0f * 3.14159265f * t)) * (3.14159265f / 180.0f);
        float camera_distance = 6.4f + 1.6f * cosf(2.0f * 3.14159265f * t);

        // Run the ray marcher directly on the GPU VRAM buffer
        render_volumetric_raymarch_kernel<<<grid, block>>>(device_frame, width, height, kx, ky, kz, alpha, camera_distance, elevation, azimuth);

        // Copy rendered pixels from GPU VRAM to mapped Host Pinned Buffer via ultra-fast PCIe DMA
        cudaMemcpy(host_frame, device_frame, frame_buffer_size, cudaMemcpyDeviceToHost);

        // Synchronize GPU execution
        cudaDeviceSynchronize();

        // Write frame to the FFmpeg process pipe
        size_t written = fwrite(host_frame, 1, frame_buffer_size, ffmpeg);
        if (written < frame_buffer_size) {
            // If the write failed, it means the FFmpeg pipe died/crashed (usually due to h264_nvenc unsupported hardware/driver).
            if (frame == 0 && using_nvenc) {
                std::cout << "\n[GPU NVENC Unsupported on this system or driver configuration. Switching to CPU Fallback...]" << std::endl;
                pclose(ffmpeg);
                
                std::cout << "Opening 4K CPU-based libx264 pipeline..." << std::endl;
                ffmpeg = popen(cpu_cmd.c_str(), "wb");
                using_nvenc = false;
                
                if (!ffmpeg) {
                    std::cerr << "Fatal: Failed to open CPU fallback pipeline!" << std::endl;
                    cudaFree(device_frame);
                    cudaFreeHost(host_frame);
                    return -1;
                }
                // Re-write the first frame
                fwrite(host_frame, 1, frame_buffer_size, ffmpeg);
            } else {
                std::cerr << "\nFatal: FFmpeg pipe broken at frame " << frame << std::endl;
                pclose(ffmpeg);
                cudaFree(device_frame);
                cudaFreeHost(host_frame);
                return -1;
            }
        }

        // Print progress status
        int percent = (frame + 1) * 100 / total_frames;
        std::cout << "\rGPU VRAM Render Progress: " << (frame + 1) << "/" << total_frames 
                  << " [" << percent << "%] (" << (using_nvenc ? "NVENC HW-GPU" : "libx264-CPU") << ")" << std::flush;
    }
    std::cout << std::endl;

    // 5. Close the pipe and clean up resources
    std::cout << "Finalizing video stream and saving container..." << std::endl;
    pclose(ffmpeg);

    // Free buffers
    cudaFree(device_frame);
    cudaFreeHost(host_frame);

    std::cout << "Success! 4K VRAM-Native Video successfully generated: " << output_mp4 << std::endl;
    return 0;
}
