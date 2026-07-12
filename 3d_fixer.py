"""
3D Model Fixer — Normalizes a GLB model so that:
  1. The record is perfectly flat on the XY plane
  2. Its geometric center is at (0, 0, 0)
  3. The Z axis is perpendicular to the face of the record

Usage:
  python 3d_fixer.py                         # Uses default model in skins/
  python 3d_fixer.py my_model.glb            # Custom model
  python 3d_fixer.py input.glb output.glb    # Separate input and output
"""

import sys
import os
import numpy as np
import trimesh


def load_model(path):
    """Loads a GLB/GLTF model and combines the meshes WITH the scene graph transformations applied."""
    print(f"[3D Fixer] Loading model: {path}")
    scene = trimesh.load(path)
    
    if isinstance(scene, trimesh.Scene):
        # Extract meshes WITH their scene graph transformations
        # (scene.geometry only gives raw meshes without transforms)
        meshes = []
        for node_name in scene.graph.nodes_geometry:
            transform, geometry_name = scene.graph[node_name]
            geom = scene.geometry[geometry_name]
            if isinstance(geom, trimesh.Trimesh):
                mesh_copy = geom.copy()
                mesh_copy.apply_transform(transform)
                meshes.append(mesh_copy)
                print(f"  - Mesh: '{geometry_name}' (node: '{node_name}', {len(geom.vertices)} vertices, {len(geom.faces)} faces)")
                # Show applied transformation
                from trimesh.transformations import euler_from_matrix
                angles = np.degrees(euler_from_matrix(transform))
                pos = transform[:3, 3]
                print(f"    Transform: pos=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}) rot=({angles[0]:.1f}, {angles[1]:.1f}, {angles[2]:.1f}) deg")
        
        if not meshes:
            print("[3D Fixer] ERROR: No meshes found in the model.")
            sys.exit(1)
        
        combined = trimesh.util.concatenate(meshes)
        return scene, combined
    elif isinstance(scene, trimesh.Trimesh):
        print(f"  - Single mesh: {len(scene.vertices)} vertices, {len(scene.faces)} faces")
        return None, scene
    else:
        print(f"[3D Fixer] ERROR: Unsupported model type: {type(scene)}")
        sys.exit(1)


def analyze_model(mesh):
    """Analyzes the current orientation of the model."""
    bounds = mesh.bounds
    center = mesh.centroid
    extents = mesh.extents  # size in each axis (dx, dy, dz)
    
    print(f"\n=== MODEL ANALYSIS ===")
    print(f"Geometric center: ({center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f})")
    print(f"X Extent: {extents[0]:.4f}")
    print(f"Y Extent: {extents[1]:.4f}")
    print(f"Z Extent: {extents[2]:.4f}")
    print(f"Bounding box min: ({bounds[0][0]:.4f}, {bounds[0][1]:.4f}, {bounds[0][2]:.4f})")
    print(f"Bounding box max: ({bounds[1][0]:.4f}, {bounds[1][1]:.4f}, {bounds[1][2]:.4f})")
    
    # The thinnest axis is likely the axis perpendicular to the record
    thin_axis = np.argmin(extents)
    axis_names = ['X', 'Y', 'Z']
    print(f"Thinnest axis (record normal): {axis_names[thin_axis]} ({extents[thin_axis]:.4f})")
    
    # Verify using face normals
    face_normals = mesh.face_normals
    # Average the normals (weighted by area)
    areas = mesh.area_faces
    weighted_normal = np.average(face_normals, weights=areas, axis=0)
    weighted_normal = weighted_normal / np.linalg.norm(weighted_normal)
    print(f"Weighted average normal: ({weighted_normal[0]:.4f}, {weighted_normal[1]:.4f}, {weighted_normal[2]:.4f})")
    
    # Use PCA to determine principal axes
    covariance = np.cov(mesh.vertices.T)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    
    # The eigenvector with the smallest eigenvalue is the record normal
    normal_idx = np.argmin(eigenvalues)
    disc_normal = eigenvectors[:, normal_idx]
    
    print(f"\n=== PCA (Principal Component Analysis) ===")
    for i in range(3):
        ev = eigenvalues[i]
        vec = eigenvectors[:, i]
        label = " <-- RECORD NORMAL (thinnest axis)" if i == normal_idx else ""
        print(f"  Eigenvalue {i}: {ev:.6f}  Vector: ({vec[0]:.4f}, {vec[1]:.4f}, {vec[2]:.4f}){label}")
    
    return disc_normal, center


def compute_rotation_matrix(current_normal, target_normal):
    """Calculates the rotation matrix to align current_normal with target_normal."""
    current_normal = current_normal / np.linalg.norm(current_normal)
    target_normal = target_normal / np.linalg.norm(target_normal)
    
    # Cross product and angle
    cross = np.cross(current_normal, target_normal)
    dot = np.dot(current_normal, target_normal)
    
    # If already aligned (or anti-aligned)
    if np.linalg.norm(cross) < 1e-8:
        if dot > 0:
            print("[3D Fixer] The normal already points in the correct direction.")
            return np.eye(4)
        else:
            # 180 degree rotation around any perpendicular axis
            perp = np.array([1, 0, 0]) if abs(current_normal[0]) < 0.9 else np.array([0, 1, 0])
            axis = np.cross(current_normal, perp)
            axis = axis / np.linalg.norm(axis)
            return trimesh.transformations.rotation_matrix(np.pi, axis)
    
    # Rodrigues' rotation formula via transformation matrix
    axis = cross / np.linalg.norm(cross)
    angle = np.arccos(np.clip(dot, -1.0, 1.0))
    
    print(f"[3D Fixer] Required rotation: {np.degrees(angle):.2f}° around axis ({axis[0]:.4f}, {axis[1]:.4f}, {axis[2]:.4f})")
    
    return trimesh.transformations.rotation_matrix(angle, axis)


def fix_model(input_path, output_path):
    """Full pipeline: loads, analyzes, fixes, and saves preserving materials/textures."""
    scene, combined_mesh = load_model(input_path)
    disc_normal, center = analyze_model(combined_mesh)
    
    # Goal: make the record's normal point towards +Z (0, 0, 1)
    target_normal = np.array([0.0, 0.0, 1.0])
    
    # Ensure the normal points "upwards" (positive Z component)
    if disc_normal[2] < 0:
        disc_normal = -disc_normal
    
    rotation_matrix = compute_rotation_matrix(disc_normal, target_normal)
    
    # Normalize scale
    TARGET_SIZE = 4.28
    current_size = max(combined_mesh.extents[0], combined_mesh.extents[1])
    scale_factor = TARGET_SIZE / current_size
    print(f"[3D Fixer] Normalizing scale: factor {scale_factor:.4f} (from {current_size:.4f} to {TARGET_SIZE})")
    
    # Build the complete correction transformation:
    # 1. Center at origin, 2. Rotate, 3. Scale
    translation = trimesh.transformations.translation_matrix(-center)
    scale_matrix = trimesh.transformations.scale_matrix(scale_factor)
    correction = scale_matrix @ rotation_matrix @ translation
    
    if scene is not None:
        # Apply the correction to the entire scene using trimesh's public API.
        # This transforms the base frame of the scene graph, affecting all
        # geometries but preserving materials, textures, and internal structure.
        scene.apply_transform(correction)
        
        # Verify with transformed meshes
        verify_meshes = []
        for node_name in scene.graph.nodes_geometry:
            t, gname = scene.graph[node_name]
            geom = scene.geometry[gname]
            if isinstance(geom, trimesh.Trimesh):
                m = geom.copy()
                m.apply_transform(t)
                verify_meshes.append(m)
        
        if verify_meshes:
            verify_combined = trimesh.util.concatenate(verify_meshes)
        else:
            verify_combined = combined_mesh
    else:
        # Model is a simple mesh (no scene)
        combined_mesh.apply_transform(correction)
        verify_combined = combined_mesh
        scene = combined_mesh
    
    # Verify result
    new_center = verify_combined.centroid
    new_extents = verify_combined.extents
    
    print(f"\n=== FIXED MODEL ===")
    print(f"New center: ({new_center[0]:.4f}, {new_center[1]:.4f}, {new_center[2]:.4f})")
    print(f"New extents:")
    print(f"  X: {new_extents[0]:.4f} (record width)")
    print(f"  Y: {new_extents[1]:.4f} (record height)")
    print(f"  Z: {new_extents[2]:.4f} (thickness -- should be the smallest)")
    
    thin_axis = np.argmin(new_extents)
    axis_names = ['X', 'Y', 'Z']
    if thin_axis == 2:
        print(f"[OK] Correct! The thinnest axis is Z -> the record is flat on XY")
    else:
        print(f"[!!] The thinnest axis is {axis_names[thin_axis]}, expected Z. May need manual adjustment.")
    
    # Save the complete SCENE (preserves materials and textures)
    print(f"\n[3D Fixer] Saving fixed model to: {output_path}")
    scene.export(output_path)
    print(f"[OK] Model saved successfully!")


if __name__ == "__main__":
    # Default paths
    default_input = os.path.join("skins", "very_simple_cd-_disc.glb")
    default_output = os.path.join("skins", "vinyl_fixed.glb")
    
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) == 2:
        input_path = sys.argv[1]
        name, ext = os.path.splitext(input_path)
        output_path = f"{name}_fixed{ext}"
    else:
        input_path = default_input
        output_path = default_output
    
    if not os.path.exists(input_path):
        print(f"[3D Fixer] ERROR: File not found: {input_path}")
        sys.exit(1)
    
    fix_model(input_path, output_path)
