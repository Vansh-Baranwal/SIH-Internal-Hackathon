import type { TargetSite } from '../types/api';

interface TerrainProps {
  primaryTarget: TargetSite | null;
  replannedTarget: TargetSite | null;
  replanTriggered: boolean;
}

export function Terrain({ primaryTarget, replannedTarget, replanTriggered }: TerrainProps) {
  return (
    <group>
      {/* Base Terrain Surface - Size 200x200 matching M4 synthetic map */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[100, 0, -100]} receiveShadow>
        <planeGeometry args={[200, 200, 16, 16]} />
        <meshStandardMaterial color="#666666" roughness={0.9} />
      </mesh>
      
      {/* Grid Helper to show scale */}
      <gridHelper args={[200, 20, 0x444444, 0x222222]} position={[100, 0.1, -100]} />

      {/* Primary Target Site A */}
      {primaryTarget && (
        <group position={[primaryTarget.x, 0.2, -primaryTarget.y]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[2, 3, 32]} />
            <meshBasicMaterial color={replanTriggered ? "red" : "cyan"} />
          </mesh>
        </group>
      )}

      {/* Replanned Target Site B */}
      {replannedTarget && replanTriggered && (
        <group position={[replannedTarget.x, 0.2, -replannedTarget.y]}>
          <mesh rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[2, 3, 32]} />
            <meshBasicMaterial color="lime" />
          </mesh>
        </group>
      )}
    </group>
  );
}
