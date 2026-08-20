import { useGLTF, Center } from '@react-three/drei';
import { getAssetUrl } from '../api/client';
import { useMemo } from 'react';
import * as THREE from 'three';

interface TerrainProps {
  onClick?: (x: number, y: number, z: number, isSafe: boolean) => void;
  target?: {x: number, y: number, z: number} | null;
}

export function Terrain({ onClick, target }: TerrainProps) {
  const glbUrl = getAssetUrl('moon_surface.glb?v=3');
  const { scene } = useGLTF(glbUrl);

  const overlayScene = useMemo(() => {
      const clone = scene.clone();
      clone.traverse((node: any) => {
          if (node.isMesh) {
              node.material = new THREE.ShaderMaterial({
                  vertexShader: `
                      varying vec3 vNormal;
                      void main() {
                          vNormal = normalize(normalMatrix * normal);
                          vec3 offset = normal * 0.005;
                          gl_Position = projectionMatrix * modelViewMatrix * vec4(position + offset, 1.0);
                      }
                  `,
                  fragmentShader: `
                      varying vec3 vNormal;
                      void main() {
                          float slope = acos(abs(vNormal.y)) * 180.0 / 3.14159265;
                          // Stricter, more accurate 10 degree slope threshold for Vikram
                          if (slope <= 10.0) {
                              gl_FragColor = vec4(0.0, 1.0, 0.2, 0.35); 
                          } else {
                              discard;
                          }
                      }
                  `,
                  transparent: true,
                  depthWrite: false, 
                  side: THREE.FrontSide
              });
          }
      });
      return clone;
  }, [scene]);

  const handleClick = (e: any) => {
      e.stopPropagation(); 
      if (onClick && e.point && e.face) {
          const normal = e.face.normal.clone();
          const normalMatrix = new THREE.Matrix3().getNormalMatrix(e.object.matrixWorld);
          normal.applyMatrix3(normalMatrix).normalize();
          
          const slope = Math.acos(Math.abs(normal.y)) * (180 / Math.PI);
          // Stricter, more accurate calculation
          const isSafe = slope <= 10.0; 
          
          onClick(e.point.x, e.point.y, e.point.z, isSafe);
      }
  };

  return (
    <group>
      <Center position={[0, 0, 0]}>
        <group scale={[1000, 1000, 1000]}>
            <primitive 
              object={scene} 
              onClick={handleClick}
              receiveShadow
              castShadow
            />
            <primitive object={overlayScene} />
        </group>
      </Center>
      
      {/* Target Marker */}
      {target && (
        <group position={[target.x, target.y + 0.5, target.z]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[20, 30, 32]} />
            <meshBasicMaterial color="yellow" />
          </mesh>
          <mesh position={[0, 40, 0]}>
            <cylinderGeometry args={[0, 10, 80, 16]} />
            <meshBasicMaterial color="red" />
          </mesh>
        </group>
      )}
    </group>
  );
}

useGLTF.preload('http://localhost:8000/api/assets/moon_surface.glb?v=3');
