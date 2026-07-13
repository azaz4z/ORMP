
import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils

Item {
    id: root
    width: 800
    height: 800
    
    // Vinyl angle (controlled from Python)
    property real vinylAngle: 0
    property real vinylTiltY: 0
    
    // 3D model URL
    property url modelSource: "file:///c:/Users/Aristoteles/Documents/Programacion/Python/ORMP/skins/very_simple_cd-_disc.glb"
    
    // Camera properties
    property real camX: 0
    property real camY: 0
    property real camZ: 16
    property real camPitch: 0
    property real camYaw: 0
    property real camRoll: 0

    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            clearColor: "#202020"
            backgroundMode: SceneEnvironment.Color
            
            // Maximum Anti-Aliasing quality (Super Sampling) to eliminate jagged edges
            antialiasingMode: SceneEnvironment.SSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            
            // Temporal AA: Greatly helps reduce flickering in vinyl grooves
            temporalAAEnabled: true
            
            // Specific for smoothing specular highlights (white reflections)
            specularAAEnabled: true
            
            // Image Based Lighting (IBL) for realistic PBR reflections
            lightProbe: Texture {
                source: "file:///c:/Users/Aristoteles/Documents/Programacion/Python/ORMP/skins/studio.hdr"
            }
            probeExposure: 0.3 // Keep HDRI dim just for texture
            
            // Greatly improves PBR materials
            tonemapMode: SceneEnvironment.TonemapACES
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

        // Parent Node for Y tilt
        Node {
            eulerRotation.y: root.vinylTiltY
            
            // Child Node applies ONLY vinyl Z rotation
            Node {
                eulerRotation.z: root.vinylAngle
                
                RuntimeLoader {
                    id: vinylModel
                    source: root.modelSource
                    scale: Qt.vector3d(3.5, 3.5, 3.5)
                }
            }
        }
    }
}
