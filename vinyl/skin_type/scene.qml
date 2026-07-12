
import QtQuick
import QtQuick3D
import QtQuick3D.AssetUtils

Item {
    id: root
    width: 800
    height: 800
    
    // Angulo del vinilo (controlado desde Python)
    property real vinylAngle: 0
    property real vinylTiltY: 0
    
    // URL del modelo 3D
    property url modelSource: "file:///c:/Users/Aristoteles/Documents/Programacion/Python/ORMP/skins/very_simple_cd-_disc.glb"
    
    // Propiedades de camara
    property real camX: 0
    property real camY: 0
    property real camZ: 18
    property real camPitch: 0
    property real camYaw: 0
    property real camRoll: 0

    View3D {
        anchors.fill: parent
        
        environment: SceneEnvironment {
            clearColor: "#202020"
            backgroundMode: SceneEnvironment.Color
            
            // Máxima calidad de Anti-Aliasing (Super Sampling) para eliminar bordes de sierra
            antialiasingMode: SceneEnvironment.SSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            
            // AA Temporal: Ayuda enormemente a reducir el parpadeo en las ranuras del vinilo
            temporalAAEnabled: true
            
            // Específico para suavizar los brillos especulares (los reflejos blancos)
            specularAAEnabled: true
            
            // Image Based Lighting (IBL) para reflejos realistas PBR
            lightProbe: Texture {
                source: "file:///c:/Users/Aristoteles/Documents/Programacion/Python/ORMP/skins/studio.hdr"
            }
            probeExposure: 0.3 // Mantenemos el HDRI tenue solo para dar textura
            
            // Mejora muchísimo los materiales PBR
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
            
            // Permitir que la cámara se acerque mucho sin cortar el modelo
            clipNear: 0.1
            clipFar: 1000.0
        }

        // Efecto "Linterna / Foco" que te gustaba antes
        PointLight {
            x: 0
            y: 5
            z: 12
            brightness: 2.0
            linearFade: 0.05
            ambientColor: "#111111"
        }

        // Node padre para el tilt en Y
        Node {
            eulerRotation.y: root.vinylTiltY
            
            // Node hijo aplica SOLO el giro del vinilo en Z
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
