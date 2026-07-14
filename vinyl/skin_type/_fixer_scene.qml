
import QtQuick
import QtQuick3D
import QtQuick3D.Helpers
import QtQuick3D.AssetUtils

Item {
    id: root
    width: 800
    height: 600
    
    property color bgColor: "#1a1a1a"
    
    property real vinylAngle: 0
    property real manualRotX: 0
    property real manualRotY: 0
    property real manualRotZ: 0
    
    property real camX: 0
    property real camY: 0
    property real camZ: 8.1
    property real camPitch: 0
    property real camYaw: 0
    
    property url modelSource: "file:///c:/Users/Aristoteles/Documents/Programacion/Python/ORMP/skins/_fixer_preview.glb"

    View3D {
        id: view
        anchors.fill: parent
        
        environment: ExtendedSceneEnvironment {
            backgroundMode: SceneEnvironment.Color
            clearColor: root.bgColor
            
            antialiasingMode: SceneEnvironment.SSAA
            antialiasingQuality: SceneEnvironment.VeryHigh
            temporalAAEnabled: true
            specularAAEnabled: true
            
            lightProbe: Texture {
                source: "file:///c:/Users/Aristoteles/Documents/Programacion/Python/ORMP/skins/studio.hdr"
            }
            probeExposure: 2.0
            
            tonemapMode: SceneEnvironment.TonemapACES
        }

        PerspectiveCamera {
            id: camera
            x: root.camX
            y: root.camY
            z: root.camZ
            eulerRotation.x: root.camPitch
            eulerRotation.y: root.camYaw
            clipNear: 0.1
            clipFar: 1000.0
        }

        PointLight {
            x: 0; y: 5; z: 12
            brightness: 2.0
            linearFade: 0.05
            ambientColor: "#111111"
        }
        
        DirectionalLight {
            eulerRotation.x: -20
            eulerRotation.y: -30
            brightness: 1.5
            ambientColor: "#333333"
        }

        // Manual rotation node (user adjustments)
        Node {
            eulerRotation.x: root.manualRotX
            eulerRotation.y: root.manualRotY
            eulerRotation.z: root.manualRotZ
            
            // Spin animation node
            Node {
                eulerRotation.z: root.vinylAngle
                
                RuntimeLoader {
                    id: vinylModel
                    source: root.modelSource
                    property real scaleFactor: 3.5 * Math.min(1.0, root.width / Math.max(1.0, root.height))
                    scale: Qt.vector3d(scaleFactor, scaleFactor, scaleFactor)
                }
            }
        }
    }
    
    // Grid helper lines
    Rectangle {
        anchors.centerIn: parent
        width: parent.width
        height: 1
        color: "#33ffffff"
    }
    Rectangle {
        anchors.centerIn: parent
        width: 1
        height: parent.height
        color: "#33ffffff"
    }
}
