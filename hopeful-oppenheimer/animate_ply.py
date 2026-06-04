"""
@file animate_ply.py
@brief GPU-Accelerated 3D point cloud video compiler launcher.
       Utilizes static-ffmpeg to fetch a platform-specific static FFmpeg executable,
       compiles the high-performance CUDA video renderer on-the-fly,
       and runs the GPU pipeline to generate high-fidelity H.264 MP4 videos.
"""

import os
import sys
import subprocess
from static_ffmpeg import run

def print_header(title):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def compile_cuda_renderer():
    """
    Compiles cebir_cuda_video.cu dynamically using nvcc and Visual Studio compiler env.
    """
    print("\nCUDA Video Renderer is compiling on the GPU...")
    
    # Locate Visual Studio vcvars64.bat path
    vcvars_path = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    
    if not os.path.exists(vcvars_path):
        print("Error: Visual Studio environment vars not found! Please compile cebir_cuda_video.cu manually.")
        return False

    # Compilation command linking Visual Studio tools and NVCC
    compile_cmd = f'cmd.exe /c \'call "{vcvars_path}" && nvcc -O3 cebir_cuda_video.cu -o cebir_cuda_video.exe\''
    
    try:
        # Run compilation synchronously
        result = subprocess.run(compile_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("CUDA compiler successfully created: cebir_cuda_video.exe")
        return True
    except subprocess.CalledProcessError as e:
        print("\nCompilation failed!")
        print(e.stderr.decode('utf-8', errors='ignore'))
        return False

def main():
    print_header("3D HOLOGRAPHIC TOPOLOGY GPU VIDEO RENDERER")
    
    ply_filename = "holographic_interference_3d.ply"
    if not os.path.exists(ply_filename):
        print(f"Error: '{ply_filename}' not found!")
        print("Please run 'cebir_cuda_3d.exe' first to generate the 3D PLY point cloud data.")
        sys.exit(-1)

    # 1. Fetch static FFmpeg executable path automatically using static-ffmpeg
    print("Locating static FFmpeg library environment...")
    try:
        ffmpeg_path, _ = run.get_or_fetch_platform_executables_else_raise()
        print(f"FFmpeg binary loaded: {ffmpeg_path}")
    except Exception as e:
        print(f"Failed to fetch static FFmpeg: {e}")
        sys.exit(-1)

    # 2. Get video duration from user
    try:
        duration_input = input("Enter video duration in seconds (default: 8): ").strip()
        duration = float(duration_input) if duration_input else 8.0
    except ValueError:
        duration = 8.0
        
    print(f"Target Video Duration: {duration} seconds")

    # 3. Compile the CUDA renderer dynamically to ensure latest changes are included
    if not compile_cuda_renderer():
        sys.exit(-1)

    # 4. Launch the GPU-Accelerated C++/CUDA renderer
    output_mp4 = "holographic_interference_3d.mp4"
    print("\nLaunching CUDA GPU video rendering pipe...")
    
    # Run the native CUDA video renderer passing the arguments
    run_cmd = [
        f".\\{cuda_exe}",
        ply_filename,
        ffmpeg_path,
        str(duration),
        output_mp4
    ]
    
    try:
        # Run the CUDA application and pipe stdout directly to the console
        subprocess.run(run_cmd, check=True)
        print(f"\nSuccess! 3D GPU-accelerated video successfully compiled: {output_mp4}")
    except subprocess.CalledProcessError as e:
        print(f"\nCUDA renderer process failed: {e}")
        sys.exit(-1)

if __name__ == '__main__':
    main()
