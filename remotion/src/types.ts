export type VisualElement = {
  type: 'rect' | 'ellipse' | 'line' | 'polygon' | 'text' | 'character';
  x: number;
  y: number;
  x2?: number;
  y2?: number;
  w?: number;
  h?: number;
  fill?: string;
  stroke?: string;
  stroke_width?: number;
  text?: string;
  font_size?: number;
  points?: [number, number][];
  rotation?: number;
  pose?: string;
};

export type Scene = {
  id: string;
  duration_seconds: number;
  narration: string;
  caption?: string;
  sfx?: string[];
  camera_move?: 'push_in' | 'pull_out' | 'pan_left' | 'pan_right' | 'tilt_up' | 'tilt_down' | 'drift' | 'static';
  visual: {
    background: string;
    secondary_background?: string;
    title?: string;
    subtitle?: string;
    elements: VisualElement[];
  };
};

export type Story = {
  schema_version: string;
  title: string;
  story_type: string;
  language: string;
  fps: number;
  width: number;
  height: number;
  target_duration_seconds?: number;
  style?: string;
  palette?: string[];
  sources?: {id: string; title: string; url: string; publisher?: string; accessed_at?: string}[];
  claims?: {claim: string; source_ids: string[]}[];
  scenes: Scene[];
};

export type VideoProps = {
  story: Story;
  narration_audio?: string;
  music_audio?: string;
  sfx_audio?: string;
};
