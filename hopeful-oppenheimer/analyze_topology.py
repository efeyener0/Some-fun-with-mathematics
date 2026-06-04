/**
 * @file analyze_topology.py
 * @brief Python script for spectral decomposition, Lie algebra continuous flow simulation,
 *        and 3D holographic wave interference pattern generation for the non-associative projection algebra.
 */

import os
import numpy as np
from scipy.linalg import expm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def print_header(title):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def main():
    print_header("TOPOLOGICAL & SPECTRAL ANALYSIS OF THE ALGEBRA")

    # 1. Base Representations
    # Basis: e1 = [1,0,0]^T, eh = [0,1,0]^T, eq = [0,0,1]^T
    L1 = np.eye(3)
    Lh = np.array([
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0]
    ])
    Lq = np.array([
        [0, -1, 0],
        [0,  0, 0],
        [1,  0, 1]
    ])

    print("\n--- Matrix Representations (Left Multiplication) ---")
    print(f"L1 (Identity):\n{L1}\n")
    print(f"Lh (120-degree Cyclic Permutation):\n{Lh}\n")
    print(f"Lq (Idempotent Projection with Shear):\n{Lq}\n")

    # 2. Spectral Analysis
    print("--- Spectral Analysis (Eigenvalues & Eigenvectors) ---")
    
    # Lh Spectrum
    val_h, vec_h = np.linalg.eig(Lh)
    print("Lh Eigenvalues:")
    for idx, lam in enumerate(val_h):
        print(f"  lambda_{idx+1}: {lam:.4f}")
    print("Lh Eigenvectors (Columns):")
    print(vec_h)
    print("Note: Eigenvalue 1 corresponds to rotation axis [1, 1, 1]^T. Complex roots represent 120-deg rotation.\n")

    # Lq Spectrum
    val_q, vec_q = np.linalg.eig(Lq)
    print("Lq Eigenvalues:")
    for idx, lam in enumerate(val_q):
        print(f"  lambda_{idx+1}: {lam:.4f}")
    print("Lq Eigenvectors (Columns):")
    print(vec_q)
    print("Note: Eigenvalue 1 represents stable projection axis [0, 0, 1]^T. 0 represents kernel (projection loss).\n")

    # 3. Lie Algebra Generators (Skew-symmetric parts)
    print("--- Lie Algebra Generators (so(3) Rotation Generators) ---")
    Omega_h = 0.5 * (Lh - Lh.T)
    Omega_q = 0.5 * (Lq - Lq.T)
    print(f"Omega_h (Permutation flow generator):\n{Omega_h}\n")
    print(f"Omega_q (Projection flow generator):\n{Omega_q}\n")

    # 4. Continuous Flow Visualizations (Saving to CWD)
    print("--- Generating 3D Lie Group Continuous Flow Streams ---")
    fig = plt.figure(figsize=(12, 5))
    
    # Plot Lh Streamlines
    ax1 = fig.add_subplot(121, projection='3d')
    ax1.set_title("Lh Cyclic Flow (Rotation around [1,1,1])")
    
    # Create grid for stream vectors
    x, y, z = np.meshgrid(np.linspace(-2, 2, 8), np.linspace(-2, 2, 8), np.linspace(-2, 2, 8))
    u_h = np.zeros_like(x)
    v_h = np.zeros_like(y)
    w_h = np.zeros_like(z)
    
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            for k in range(x.shape[2]):
                vec = np.array([x[i,j,k], y[i,j,k], z[i,j,k]])
                flow_h = Omega_h @ vec
                u_h[i,j,k] = flow_h[0]
                v_h[i,j,k] = flow_h[1]
                w_h[i,j,k] = flow_h[2]

    ax1.quiver(x, y, z, u_h, v_h, w_h, length=0.15, normalize=True, color='cyan', alpha=0.6)
    ax1.set_xlabel('e1 (1)')
    ax1.set_ylabel('eh (h)')
    ax1.set_zlabel('eq (q)')
    
    # Plot Lq Streamlines
    ax2 = fig.add_subplot(122, projection='3d')
    ax2.set_title("Lq Projection Flow (Spiral to [0,0,1])")
    u_q = np.zeros_like(x)
    v_q = np.zeros_like(y)
    w_q = np.zeros_like(z)
    
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            for k in range(x.shape[2]):
                vec = np.array([x[i,j,k], y[i,j,k], z[i,j,k]])
                flow_q = Omega_q @ vec
                u_q[i,j,k] = flow_q[0]
                v_q[i,j,k] = flow_q[1]
                w_q[i,j,k] = flow_q[2]

    ax2.quiver(x, y, z, u_q, v_q, w_q, length=0.15, normalize=True, color='magenta', alpha=0.6)
    ax2.set_xlabel('e1 (1)')
    ax2.set_ylabel('eh (h)')
    ax2.set_zlabel('eq (q)')

    plt.tight_layout()
    flow_plot_path = "lie_group_flows.png"
    plt.savefig(flow_plot_path, dpi=150)
    print(f"Lie group flow streamlines saved to: {flow_plot_path}")
    plt.close()

    # 5. Coherent Holographic Wave Interference Simulation
    print("\n--- Simulating Coherent 3D Holographic Wave Interference ---")
    grid_size = 80
    lim = 3.0
    x_lin = np.linspace(-lim, lim, grid_size)
    y_lin = np.linspace(-lim, lim, grid_size)
    
    X, Y = np.meshgrid(x_lin, y_lin)
    
    # Define a 3D Wave Packet: psi(x) = cos(k * x) * exp(-alpha * ||x||^2)
    # Let's visualize the Z=0 slice of the 3D field
    k = np.array([3.5, 2.0, 1.0]) # Wave vector
    alpha = 0.4                  # Gaussian spatial envelope decay
    
    # Group elements and representation matrices
    # {1, h, q, -1, -h, -q}
    group_ops = [L1, Lh, Lq, -L1, -Lh, -Lq]
    phases = [0.0, np.pi/3, 2*np.pi/3, np.pi, 4*np.pi/3, 5*np.pi/3] # Superposition phase factors

    # Compute intensity on Z = 0 plane
    Z_val = 0.0
    field = np.zeros_like(X, dtype=complex)
    
    for i in range(grid_size):
        for j in range(grid_size):
            r = np.array([X[i,j], Y[i,j], Z_val])
            psi_total = 0.0
            
            # Superpose wave functions transformed by all 6 group elements
            for idx, Mg in enumerate(group_ops):
                # Apply inverse matrix action on coordinates (g^-1 * x)
                try:
                    Mg_inv = np.linalg.inv(Mg)
                except np.linalg.linalg.LinAlgError:
                    # Lq is not invertible, so we use pseudo-inverse for physical representation
                    Mg_inv = np.linalg.pinv(Mg)
                
                r_trans = Mg_inv @ r
                
                # Compute single wave packet contribution
                envelope = np.exp(-alpha * np.sum(r_trans**2))
                phase_val = np.cos(np.dot(k, r_trans))
                wave = envelope * phase_val
                
                # Apply phase superposition coefficient c_g = exp(i * theta_g)
                c_g = np.exp(1j * phases[idx])
                psi_total += c_g * wave
                
            field[i,j] = psi_total

    intensity = np.abs(field)**2

    # Plot 2D Slice Heatmap of Interference Pattern
    plt.figure(figsize=(7, 6))
    plt.title("Algebra Holographic Wave Interference (Z = 0 Slice)")
    plt.pcolormesh(X, Y, intensity, cmap='inferno', shading='auto')
    plt.colorbar(label='Interference Intensity I(x,y,0)')
    plt.xlabel('e1 (1)')
    plt.ylabel('eh (h)')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    interference_plot_path = "holographic_interference_z0.png"
    plt.savefig(interference_plot_path, dpi=150)
    print(f"Interference slice plot saved to: {interference_plot_path}")
    plt.close()

    print("\nAll simulations completed. Report figures successfully generated.")

if __name__ == '__main__':
    main()
