import type { CSSProperties } from 'react'

export function luminance(hex: string): number {
  const channels = hex.replace('#', '').match(/.{2}/g)!.map(v => parseInt(v, 16) / 255)
  const linear = channels.map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
  return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722
}
export function contrast(a: string, b: string): number {
  const x = luminance(a), y = luminance(b)
  return (Math.max(x, y) + .05) / (Math.min(x, y) + .05)
}
export function teamTheme(input: string): CSSProperties {
  const primary = /^#[0-9a-f]{6}$/i.test(input) ? input : '#0058A4'
  const rgb = primary.slice(1).match(/.{2}/g)!.map(v => parseInt(v, 16))
  const mutedBackground = '#' + [23,35,46].map((v,i)=>Math.round(v*.88+rgb[i]*.12).toString(16).padStart(2,'0')).join('')
  let readable = primary
  for (let step = 1; Math.min(contrast(readable, '#17232E'),contrast(readable,mutedBackground)) < 4.5 && step <= 100; step++) {
    readable = '#' + rgb.map(v => Math.round(v + (255 - v) * step / 100).toString(16).padStart(2, '0')).join('')
  }
  return {
    '--team-primary': primary,
    '--accent': readable,
    '--accent-ink': contrast(readable, '#000000') >= contrast(readable, '#FFFFFF') ? '#000000' : '#FFFFFF',
    '--accent-muted': `rgba(${rgb.join(',')},.12)`,
    '--accent-border': `rgba(${rgb.join(',')},.45)`,
  } as CSSProperties
}
