/**
 * Shared constants used across multiple components.
 */

export const SCENE_LABELS = [
  "testimonial",
  "b-roll",
  "audience_reaction",
  "establishing_shot",
  "other"
];

export const EMOTIONS = [
  "null",
  "happy",
  "sad",
  "angry",
  "fear",
  "surprise",
  "disgust",
  "neutral"
];

export const labelColors = {
  testimonial: '#58a6ff',
  'b-roll': '#f0883e',
  audience_reaction: '#56d364',
  establishing_shot: '#79c0ff',
  other: '#8b949e'
};

// Per-emotion colors for the timeline strip on review cards. `_none` is the muted
// fill for sampled frames where no face was detected.
export const emotionColors = {
  happy: '#e3b341',
  sad: '#58a6ff',
  angry: '#f85149',
  fear: '#bc8cff',
  surprise: '#ff9bce',
  disgust: '#56d364',
  neutral: '#8b949e',
  _none: '#30363d'
};
