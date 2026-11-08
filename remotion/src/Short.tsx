import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {Scene, Story, VideoProps, VisualElement} from './types';

const VIEWBOX = '0 0 100 177.78';

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const cameraTransform = (move: string | undefined, progress: number): string => {
  switch (move) {
    case 'push_in': return `scale(${1 + progress * 0.075})`;
    case 'pull_out': return `scale(${1.075 - progress * 0.075})`;
    case 'pan_left': return `translateX(${2.5 - progress * 5}%) scale(1.04)`;
    case 'pan_right': return `translateX(${-2.5 + progress * 5}%) scale(1.04)`;
    case 'tilt_up': return `translateY(${2 - progress * 4}%) scale(1.04)`;
    case 'tilt_down': return `translateY(${-2 + progress * 4}%) scale(1.04)`;
    case 'drift': return `translate(${Math.sin(progress * Math.PI * 2) * 1.2}%, ${Math.cos(progress * Math.PI * 2) * 1.0}%) scale(1.035)`;
    default: return 'scale(1)';
  }
};

const renderElement = (element: VisualElement, index: number): React.ReactNode => {
  const fill = element.fill ?? '#F4D35E';
  const stroke = element.stroke ?? 'none';
  const strokeWidth = element.stroke_width ?? 0.5;
  const rotation = element.rotation ? `rotate(${element.rotation} ${element.x} ${element.y})` : undefined;
  switch (element.type) {
    case 'rect':
      return <rect key={index} x={element.x} y={element.y} width={element.w ?? 1} height={element.h ?? 1} rx="1.4" fill={fill} stroke={stroke} strokeWidth={strokeWidth} transform={rotation} />;
    case 'ellipse':
      return <ellipse key={index} cx={element.x} cy={element.y} rx={(element.w ?? 1) / 2} ry={(element.h ?? 1) / 2} fill={fill} stroke={stroke} strokeWidth={strokeWidth} transform={rotation} />;
    case 'line':
      return <line key={index} x1={element.x} y1={element.y} x2={element.x2 ?? element.x} y2={element.y2 ?? element.y} stroke={element.stroke ?? fill} strokeWidth={strokeWidth || 1} strokeLinecap="round" />;
    case 'polygon':
      return <polygon key={index} points={(element.points ?? []).map(([x, y]) => `${x},${y}`).join(' ')} fill={fill} stroke={stroke} strokeWidth={strokeWidth} />;
    case 'text':
      return <text key={index} x={element.x} y={element.y} fill={fill} fontSize={element.font_size ?? 4} fontWeight="700" letterSpacing="0.15" paintOrder="stroke" stroke="#101820" strokeWidth="0.18">{element.text ?? ''}</text>;
    case 'character': {
      const width = element.w ?? 10;
      const height = element.h ?? 24;
      const head = width * 0.62;
      return (
        <g key={index} transform={`translate(${element.x}, ${element.y})`} stroke="#171923" strokeWidth="0.85" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="0" cy={-height * 0.72} rx={head / 2} ry={head / 2.1} fill="#F1C7A5" />
          <path d={`M ${-width * 0.35} ${-height * 0.48} Q 0 ${-height * 0.60} ${width * 0.35} ${-height * 0.48} L ${width * 0.28} ${-height * 0.10} L ${-width * 0.28} ${-height * 0.10} Z`} fill={fill} />
          <path d={`M ${-width * 0.18} ${-height * 0.10} L ${-width * 0.24} 0 M ${width * 0.18} ${-height * 0.10} L ${width * 0.24} 0`} fill="none" />
          <path d={`M ${-width * 0.32} ${-height * 0.43} L ${-width * 0.53} ${-height * 0.23} M ${width * 0.32} ${-height * 0.43} L ${width * 0.52} ${-height * 0.25}`} fill="none" />
          <circle cx={-head * 0.18} cy={-height * 0.74} r="0.45" fill="#171923" stroke="none" />
          <circle cx={head * 0.18} cy={-height * 0.74} r="0.45" fill="#171923" stroke="none" />
        </g>
      );
    }
    default:
      return null;
  }
};

const SceneCard: React.FC<{scene: Scene; index: number}> = ({scene, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durationFrames = Math.max(1, Math.round(scene.duration_seconds * fps));
  const progress = interpolate(frame, [0, Math.max(1, durationFrames - 1)], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const titleY = interpolate(frame, [0, 18], [12, 0], {...clamp, easing: Easing.out(Easing.quad)});
  const bg2 = scene.visual.secondary_background ?? '#FCA311';

  return (
    <AbsoluteFill style={{backgroundColor: scene.visual.background, overflow: 'hidden'}}>
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 72% 24%, ${bg2}55 0%, transparent 46%), linear-gradient(155deg, ${scene.visual.background} 10%, #0B132B 100%)`}} />
      <AbsoluteFill style={{transform: cameraTransform(scene.camera_move, progress), transformOrigin: '50% 55%'}}>
        <svg viewBox={VIEWBOX} width="100%" height="100%" preserveAspectRatio="xMidYMid slice" role="img" aria-label={scene.visual.title ?? scene.id}>
          <defs>
            <linearGradient id={`ground-${index}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={bg2} stopOpacity="0.3" />
              <stop offset="100%" stopColor="#030712" stopOpacity="0.75" />
            </linearGradient>
          </defs>
          <rect x="0" y="126" width="100" height="52" fill={`url(#ground-${index})`} />
          {scene.visual.elements.map(renderElement)}
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{padding: '8% 8% 10%', justifyContent: 'space-between', pointerEvents: 'none'}}>
        <div style={{transform: `translateY(${titleY}px)`, opacity: interpolate(frame, [0, 12], [0, 1], clamp)}}>
          {scene.visual.subtitle ? <div style={{fontFamily: 'Arial, sans-serif', color: '#FFFFFFB8', fontSize: 22, fontWeight: 700, letterSpacing: 4, textTransform: 'uppercase'}}>{scene.visual.subtitle}</div> : null}
          {scene.visual.title ? <div style={{fontFamily: 'Arial, sans-serif', color: '#FFFFFF', fontSize: 66, lineHeight: 0.98, fontWeight: 900, letterSpacing: -2, maxWidth: '90%', textShadow: '0 5px 22px #0009', marginTop: 16}}>{scene.visual.title}</div> : null}
        </div>
        <div style={{alignSelf: 'center', width: '100%', textAlign: 'center', padding: '22px 28px', borderRadius: 22, background: 'linear-gradient(180deg, #050B18B8, #050B1899)', color: '#FFFFFF', fontFamily: 'Arial, sans-serif', fontSize: 34, lineHeight: 1.18, fontWeight: 700, textShadow: '0 2px 7px #0008'}}>
          {scene.caption ?? ''}
        </div>
      </AbsoluteFill>
      <div style={{position: 'absolute', left: '8%', right: '8%', bottom: '4%', height: 5, background: '#FFFFFF35', borderRadius: 10}}>
        <div style={{height: '100%', width: `${Math.max(0, Math.min(100, progress * 100))}%`, background: '#FCA311', borderRadius: 10}} />
      </div>
    </AbsoluteFill>
  );
};

export const ShortVideo: React.FC<VideoProps> = ({story, narration_audio, music_audio, sfx_audio}) => {
  const {fps} = useVideoConfig();
  let cursor = 0;
  const sequences = story.scenes.map((scene, index) => {
    const from = cursor;
    const duration = Math.max(1, Math.round(scene.duration_seconds * fps));
    cursor += duration;
    return (
      <Sequence key={scene.id} from={from} durationInFrames={duration} name={scene.id}>
        <SceneCard scene={scene} index={index} />
      </Sequence>
    );
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#0B132B'}}>
      {sequences}
      {narration_audio ? <Audio src={staticFile(narration_audio)} volume={1} /> : null}
      {music_audio ? <Audio src={staticFile(music_audio)} volume={0.22} /> : null}
      {sfx_audio ? <Audio src={staticFile(sfx_audio)} volume={0.75} /> : null}
    </AbsoluteFill>
  );
};
