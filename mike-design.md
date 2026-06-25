---
version: alpha
name: zkPass Neon Serif
description: A stark black-and-white editorial system energized by a luminous lime accent and technical precision.
colors:
  primary: "#C5FF4A"
  secondary: "#000000"
  tertiary: "#FFFFFF"
  neutral: "#E5E7EB"
  surface: "#FFFFFF"
  on-surface: "#000000"
  error: "#FF4D4F"
  primary-60: "#B0E645"
  primary-70: "#96C93C"
  primary-80: "#7EAB33"
typography:
  headline-display:
    fontFamily: "PT Serif"
    fontSize: "57px"
    fontWeight: 400
    lineHeight: "58.968px"
    letterSpacing: "-1.2474px"
  headline-lg:
    fontFamily: "PT Serif"
    fontSize: "41px"
    fontWeight: 400
    lineHeight: "55.566px"
    letterSpacing: "-1.134px"
  headline-md:
    fontFamily: "PT Serif"
    fontSize: "29px"
    fontWeight: 400
    lineHeight: "35px"
    letterSpacing: "-0.2079px"
  headline-sm:
    fontFamily: "PT Serif"
    fontSize: "21px"
    fontWeight: 300
    lineHeight: "24px"
    letterSpacing: "-0.2px"
  body-lg:
    fontFamily: "Inter Tight"
    fontSize: "18px"
    fontWeight: 300
    lineHeight: "28px"
    letterSpacing: "0px"
  body-md:
    fontFamily: "Inter Tight"
    fontSize: "15px"
    fontWeight: 300
    lineHeight: "23.25px"
    letterSpacing: "0px"
  body-sm:
    fontFamily: "Inter Tight"
    fontSize: "13px"
    fontWeight: 300
    lineHeight: "20px"
    letterSpacing: "0px"
  label-lg:
    fontFamily: "Inter Tight"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: "1"
    letterSpacing: "0.16em"
  label-md:
    fontFamily: "Inter Tight"
    fontSize: "10px"
    fontWeight: 600
    lineHeight: "1"
    letterSpacing: "0.18em"
  label-sm:
    fontFamily: "Inter Tight"
    fontSize: "9px"
    fontWeight: 600
    lineHeight: "1"
    letterSpacing: "0.2em"
  link-sm:
    fontFamily: "PT Serif"
    fontSize: "10px"
    fontWeight: 400
    lineHeight: "1"
    letterSpacing: "0px"
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  xs: 6px
  sm: 14px
  md: 24px
  lg: 32px
  xl: 88px
  gutter: 24px
  margin: 32px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.none}"
    padding: 19px 16px
    height: 48px
    width: 104px
  button-primary-hover:
    backgroundColor: "{colors.primary-60}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.none}"
    padding: 19px 16px
    height: 48px
    width: 104px
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-md}"
    rounded: "{rounded.none}"
    padding: 19px 16px
    height: 48px
    width: 104px
  button-tertiary:
    backgroundColor: "transparent"
    textColor: "{colors.on-surface}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.none}"
    padding: 0px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: 16px
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.none}"
    padding: 14px
  chip:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.full}"
    padding: 6px 10px
# zkPass Neon Serif

## Overview
zkPass presents a stark, high-contrast, tech-forward identity with an editorial serif centerpiece and a neon-lime accent. The tone is serious and futuristic, aimed at a privacy- and infrastructure-aware audience that values trust, verification, and technical credibility. The layout feels spacious and dramatic, with a strong visual hierarchy that uses darkness, glow, and precise type scaling rather than decorative ornament.

## Colors
- **Primary (#C5FF4A):** A vivid lime signal used as the brand’s energy color, calling attention to launch actions, emphasis text, and the central emblem. It should be reserved for high-value moments so it keeps its “signal light” effect.
- **Secondary (#000000):** Deep black is the dominant structural color for backgrounds, typography, and the overall security-minded atmosphere. It creates the strongest possible contrast with the accent and white text.
- **Tertiary (#FFFFFF):** Pure white is used for the main serif headlines and key contrast elements, keeping the editorial message crisp against the dark field.
- **Neutral (#E5E7EB):** A soft cool gray for secondary UI dividers, subtle borders, and low-emphasis text surfaces where pure white would be too intense.
- **Surface (#FFFFFF):** The primary surface color for cards and panels when the design lifts content off the black backdrop.
- **On-surface (#000000):** The default text color on light surfaces, matching the utility-driven black/white system.
- **Error (#FF4D4F):** A reserved alert tone for validation or destructive states; it is not prominent in the screenshot but fits the system’s restrained palette.
- **Primary-60 (#B0E645), Primary-70 (#96C93C), Primary-80 (#7EAB33):** Darker lime steps for hover, pressed, and muted accent states when the pure primary would be too bright.

## Typography
The system is defined by a deliberate dual-family contrast: PT Serif for expressive headlines and Inter Tight for functional UI copy. PT Serif carries the emotional weight of the hero messaging, with large sizes, negative letter spacing, and a refined editorial voice that feels authoritative rather than playful. Inter Tight provides the technical backbone for paragraphs, labels, navigation, and buttons, especially in uppercase tracking-heavy treatments that reinforce precision and scanability.

Headlines should use the serif scale from `headline-display` down through `headline-sm`, with lighter weights and tight leading for dramatic composition. Body copy should stay in `body-md` or `body-sm`, using the sans family and light weight for a clean, understated tone. Labels and buttons should rely on `label-md` and related small caps-like tracking conventions to match the top navigation and CTA styling.

## Layout
The page uses a wide, immersive, full-bleed composition rather than a boxed content container. Spacing is generous, with large vertical breathing room between the nav, hero headline, supporting copy, and central emblem; the rhythm is built from a small set of repeated gaps rather than dense modular grids. The spacing scale of 6px, 14px, 24px, 32px, and 88px suggests a stepped system where small UI adjustments are precise, while major section separations are intentionally dramatic.

Navigation items are arranged in fixed-width blocks across the top, creating a disciplined header band. Content alignment is centered in the hero, but surrounding visual elements extend outward to the edges, reinforcing a cinematic, panoramic feel. Cards and smaller modules should use modest internal padding, while section-level containers should favor wider margins and uncluttered negative space.

## Elevation & Depth
The design is mostly flat and relies on contrast, linework, and glow rather than traditional shadow elevation. The only noticeable depth effect is a soft lime glow around accent elements, especially the logo/emblem and highlighted calls to action. Borders are thin and restrained, so hierarchy comes from brightness, type scale, and tonal separation instead of layered surfaces.

For panels or cards, use subtle borders on white surfaces and avoid heavy drop shadows. When depth is needed, prefer minimal glow or a slight tonal lift rather than complex elevation stacks. This keeps the interface aligned with the brand’s “verifiable” and technical personality.

## Shapes
The shape language is severe and architectural. Corners are mostly square, with `rounded.none` on buttons and navigation elements to preserve the machine-like precision of the system. Where softness is needed, only secondary surfaces such as cards may use `rounded.md` for a light structural contrast.

Overall, shapes should feel rectilinear, stable, and unembellished. Avoid organic curves, pill buttons, or decorative blobs unless they are introduced very sparingly for status chips or badges.

## Components
Buttons are the clearest signature component: primary buttons use the lime `button-primary` treatment with black text, uppercase tracking, 48px height, and compact horizontal padding. Secondary buttons should remain transparent with a black border and identical sizing to keep the hierarchy clear without visual clutter. Tertiary buttons and links should be minimal, preferably text-only and serif-based when used in editorial contexts. Hover states should darken the accent slightly with `button-primary-hover`, not introduce shadows or rounded corners.

Cards should use `card` with a white surface, thin neutral border, and modest 16px padding. Keep card content lightweight and sharply aligned, with black text and little to no internal ornament. Inputs should follow the same square, crisp language as buttons and cards, with simple borders, white backgrounds, and strong contrast for form readability.

Chips and small status pills should be compact and highly legible, using dark surfaces with lime text or vice versa, and should remain visually secondary to the main CTA system. Navigation items should be treated like utility labels: uppercase, spaced out, and separated by thin dividers or clear blocks rather than heavy menu chrome. Any list or helper text should stay understated and use the sans body scale.

## Do's and Don'ts
- Do use PT Serif for the primary message and large brand statements.
- Do keep UI labels, navigation, and controls in Inter Tight with tight uppercase tracking.
- Do reserve lime `#C5FF4A` for launches, emphasis, and key interactive states.
- Do preserve the strong black-and-white contrast; it is central to the brand.
- Do keep corners square on buttons and navigation for a technical, disciplined feel.
- Don't introduce soft gradients, heavy shadows, or glossy glass effects.
- Don't overuse the accent color on large text blocks or long paragraphs.
- Don't replace the editorial serif/sans contrast with a single generic UI typeface.
