import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick3D.AssetUtils

Item {
    id: root
    width: 800
    height: 600
    
    // Background color from PyQt
    property color bgColor: "#1a1a1a"
    
    // Post-Processing Properties
    property real envExposure: 2.0
    property bool envBloom: false
    property real envBloomStrength: 0.5
    property bool envAo: false
    property real envAoStrength: 0.5
    
    // Material Properties — Only applied when user moves a slider.
    // These defaults match what most GLB models already have, so they
    // won't visually change the model until the user adjusts them.
    property real matMetalness: -1
    property real matRoughness: -1
    property real matAnisotropy: -1
    property real matAnisotropyRotation: -1
    property real matSheen: -1
    property real matSheenRoughness: -1
    property real matSpecular: -1
    property real matClearcoat: -1
    property real matClearcoatRoughness: -1
    property real matOpacity: -1
    
    function updateMaterials(prop, value) {
        if (!vinylModel) return;
        let traverse = function(node) {
            if (node.materials) {
                for (let i = 0; i < node.materials.length; ++i) {
                    let mat = node.materials[i];
                    try {
                        if (prop === "metalness") {
                            mat.metalness = value;
                        } else if (prop === "roughness") {
                            mat.roughness = value;
                        } else if (prop === "anisotropy") {
                            mat.anisotropyLevel = value;
                            mat.anisotropyEnabled = (value > 0);
                        } else if (prop === "anisotropyRotation") {
                            mat.anisotropyRotation = value;
                        } else if (prop === "sheen") {
                            mat.sheenAmount = value;
                            mat.sheenEnabled = (value > 0);
                        } else if (prop === "sheenRoughness") {
                            mat.sheenRoughness = value;
                        } else if (prop === "specular") {
                            mat.specularAmount = value;
                        } else if (prop === "clearcoat") {
                            mat.clearcoatAmount = value;
                            mat.clearcoatEnabled = (value > 0);
                        } else if (prop === "clearcoatRoughness") {
                            mat.clearcoatRoughnessAmount = value;
                        } else if (prop === "opacity") {
                            mat.opacity = value;
                        }
                    } catch (e) {}
                }
            }
            if (node.children) {
                for (let i = 0; i < node.children.length; ++i) {
                    traverse(node.children[i]);
                }
            }
        };
        traverse(vinylModel);
    }
    
    // Only apply material overrides when value is explicitly set (not the -1 sentinel)
    onMatMetalnessChanged: if (matMetalness >= 0) updateMaterials("metalness", matMetalness)
    onMatRoughnessChanged: if (matRoughness >= 0) updateMaterials("roughness", matRoughness)
    onMatAnisotropyChanged: if (matAnisotropy >= 0) updateMaterials("anisotropy", matAnisotropy)
    onMatAnisotropyRotationChanged: if (matAnisotropyRotation >= 0) updateMaterials("anisotropyRotation", matAnisotropyRotation)
    onMatSheenChanged: if (matSheen >= 0) updateMaterials("sheen", matSheen)
    onMatSheenRoughnessChanged: if (matSheenRoughness >= 0) updateMaterials("sheenRoughness", matSheenRoughness)
    onMatSpecularChanged: if (matSpecular >= 0) updateMaterials("specular", matSpecular)
    onMatClearcoatChanged: if (matClearcoat >= 0) updateMaterials("clearcoat", matClearcoat)
    onMatClearcoatRoughnessChanged: if (matClearcoatRoughness >= 0) updateMaterials("clearcoatRoughness", matClearcoatRoughness)
    onMatOpacityChanged: if (matOpacity >= 0) updateMaterials("opacity", matOpacity)
    
    // Vinyl angle (controlled from Python)
    property real vinylAngle: 0
    property real vinylTiltY: 0
    
    // External paths
    property url modelSource: ""
    property url hdrSource: ""
    
    // Camera properties
    property real camX: 0
    property real camY: 0
    property real camZ: 8.1
    property real camPitch: 0
    property real camYaw: 0
    property real camRoll: 0

    View3D {
        id: view
        anchors.fill: parent
        
        environment: ExtendedSceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: root.bgColor
            
            // Maximum Anti-Aliasing quality (Super Sampling) to eliminate jagged edges
            antialiasingMode: SceneEnvironment.SSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            
            // Temporal AA: Greatly helps reduce flickering in vinyl grooves
            temporalAAEnabled: true
            
            // Specific for smoothing specular highlights (white reflections)
            specularAAEnabled: true
            
            // Image Based Lighting (IBL) for realistic PBR reflections
            lightProbe: Texture {
                source: root.hdrSource
            }
            probeExposure: root.envExposure
            
            tonemapMode: SceneEnvironment.TonemapModeAces
            
            // Post-Processing
            glowEnabled: root.envBloom
            glowStrength: root.envBloomStrength
            glowBloom: 0.25
            glowIntensity: 2.0
            glowQualityHigh: true
            glowUseBicubicUpscale: true
            glowBlendMode: ExtendedSceneEnvironment.GlowBlendMode.Additive
            
            aoEnabled: root.envAo
            aoStrength: root.envAoStrength * 100
            aoSampleRate: 3
            aoDistance: 5.0
            aoSoftness: 50.0
            aoDither: true
        }

        PerspectiveCamera {
            id: camera
            x: root.camX
            y: root.camY
            z: root.camZ
            eulerRotation.x: root.camPitch
            eulerRotation.y: root.camYaw
            eulerRotation.z: root.camRoll
            
            // Allow camera to get very close without clipping the model
            clipNear: 0.1
            clipFar: 1000.0
        }

        // Flashlight / Spotlight effect that you liked before
        PointLight {
            x: 0
            y: 5
            z: 12
            brightness: 2.0
            linearFade: 0.05
            ambientColor: "#111111"
        }
        
        // Add a strong DirectionalLight to properly illuminate the metallic surface
        // and reveal the baked rainbow textures which require bright light to shine.
        DirectionalLight {
            eulerRotation.x: -20
            eulerRotation.y: -30
            brightness: 1.5
            ambientColor: "#333333"
        }

        // Parent Node for Y tilt
        Node {
            eulerRotation.y: root.vinylTiltY
            
            // Child Node applies ONLY vinyl Z rotation
            Node {
                eulerRotation.z: root.vinylAngle
                
                RuntimeLoader {
                    id: vinylModel
                    source: root.modelSource
                    // Aspect ratio scaling: only shrink when width is smaller than height to prevent side-clipping
                    property real scaleFactor: 3.5 * Math.min(1.0, root.width / Math.max(1.0, root.height))
                    scale: Qt.vector3d(scaleFactor, scaleFactor, scaleFactor)
                    
                    onStatusChanged: {
                        if (status === RuntimeLoader.Success) {
                            console.log("[QML] Model loaded successfully. Using model's own PBR materials.");
                        }
                    }
                }
            }
        }
    }
}
