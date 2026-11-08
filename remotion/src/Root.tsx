import React from 'react';
import {Composition} from 'remotion';
import story from '../../examples/stories/seed-on-roof.json';
import {ShortVideo} from './Short';
import type {Story, VideoProps} from './types';

const defaultProps: VideoProps = {story: story as Story};

export const Root: React.FC = () => (
  <Composition
    id="KinoquenceShort"
    component={ShortVideo}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={1}
    defaultProps={defaultProps}
    calculateMetadata={({props}) => {
      const videoProps = props as VideoProps;
      const fps = Number(videoProps.story.fps || 30);
      return {
        fps,
        width: Number(videoProps.story.width || 1080),
        height: Number(videoProps.story.height || 1920),
        // Match the exact per-scene frame rounding used by <Sequence> in Short.tsx.
        durationInFrames: videoProps.story.scenes.reduce(
          (sum, scene) => sum + Math.max(1, Math.round(Number(scene.duration_seconds) * fps)),
          0,
        ),
      };
    }}
  />
);
