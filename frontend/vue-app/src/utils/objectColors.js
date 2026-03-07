export const OBJECT_COLORS = [
  '#06b6d4',  // cyan
  '#a855f7',  // purple
  '#3b82f6',  // blue
  '#ec4899',  // pink
  '#84cc16',  // lime
  '#14b8a6',  // teal
  '#8b5cf6',  // violet
  '#f0abfc',  // fuchsia
]

export const objectColor = (i) => OBJECT_COLORS[i % OBJECT_COLORS.length]
