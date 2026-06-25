---
version: alpha
name: Mode Dark Editorial
description: A dark, premium BI brand system blending high-contrast serif headlines with restrained utility UI.
colors:
  primary: "#043f2e"
  secondary: "#eef2e3"
  tertiary: "#121212"
  neutral: "#f5f4ef"
  surface: "#0f2f25"
  on-surface: "#eef2e3"
  error: "#d96b6b"
  border: "#374151"
  muted: "#9ca3af"
typography:
  headline-display:
    fontFamily: Grenette
    fontSize: 72px
    fontWeight: 400
    lineHeight: 86px
    letterSpacing: -1.323px
  headline-lg:
    fontFamily: Grenette
    fontSize: 51px
    fontWeight: 400
    lineHeight: 79.2px
    letterSpacing: -1.44px
  headline-md:
    fontFamily: "Times New Roman"
    fontSize: 36px
    fontWeight: 400
    lineHeight: 43px
    letterSpacing: 0px
  headline-sm:
    fontFamily: "Times New Roman"
    fontSize: 25px
    fontWeight: 400
    lineHeight: 30px
    letterSpacing: 0px
  body-lg:
    fontFamily: "Times New Roman"
    fontSize: 18px
    fontWeight: 400
    lineHeight: 27px
    letterSpacing: 0px
  body-md:
    fontFamily: "Times New Roman"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: 0px
  body-sm:
    fontFamily: "Times New Roman"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 21px
    letterSpacing: 0px
  label-lg:
    fontFamily: Graphik
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0px
  label-md:
    fontFamily: Graphik
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: 0px
  label-sm:
    fontFamily: Graphik
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: 0px
  overline:
    fontFamily: Graphik
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.06em
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 20px
  full: 9999px
spacing:
  xs: 12px
  sm: 20px
  md: 30px
  lg: 56px
  xl: 120px
components:
  button-primary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.primary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.sm}"
    padding: 17px 30px 16px
    height: 50px
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.sm}"
    padding: 17px 30px 16px
    height: 50px
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.none}"
    padding: 0px
  card:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: 16px
  input:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.sm}"
    padding: 14px 16px
  badge:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.secondary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.full}"
    padding: 4px 10px
---

# Mode Dark Editorial

## Overview
Mode presents as a premium, confident business-intelligence brand with an editorial sensibility. The visual tone is dark, spacious, and sophisticated, with a clear balance between enterprise trust and creative energy. Large serif headlines and restrained utility controls suggest a product for data teams and business stakeholders who want clarity without feeling overly corporate.

## Colors
- **Primary (#043f2e):** A deep forest-green ink used for the brand’s strongest UI actions, navigation accents, and dark text on light surfaces. It feels authoritative and organic rather than harsh.
- **Secondary (#eef2e3):** A soft ivory used for primary CTA fills, light text on dark backgrounds, and warm contrast against the dominant green field.
- **Tertiary (#121212):** The near-black base of the page, creating the dramatic dark canvas that allows hero typography and cards to stand out.
- **Neutral (#f5f4ef):** A quieter off-white supporting readable sections and softening the overall contrast when the UI needs a lighter neutral.
- **Surface (#0f2f25):** A deep green surface tone for panels and layered containers, reinforcing the monochrome, tonal feel.
- **On-surface (#eef2e3):** The standard text color on dark surfaces, chosen for high legibility and a refined warm contrast.
- **Error (#d96b6b):** A muted red reserved for alerts or destructive states; it should stay subdued to match the system’s premium tone.
- **Border (#374151):** A cool, low-contrast divider color for cards and structural outlines.
- **Muted (#9ca3af):** A soft gray for secondary text, metadata, or de-emphasized UI affordances.

## Typography
Grenette is the signature display face and should be used for the largest headlines, especially marketing hero statements. It carries an elegant, editorial personality with strong negative letter-spacing and a generous line height, giving the page its distinctive presence. Times New Roman serves as the body and secondary heading serif, keeping paragraphs readable and classic without competing with the display type. Graphik is used for utility labels, navigation, buttons, and small UI text; it provides the modern, product-oriented counterbalance to the serif-led brand. Uppercase treatment is minimal, but labels may use subtle tracking only where a compact, system-like tone is needed.

## Layout
The layout is centered and wide, with a large hero zone that relies on open negative space and oversized type rather than dense column grids. Content blocks are arranged in large, staggered rectangular panels, and the spacing rhythm favors big jumps: 12px for fine spacing, then 20px, 30px, 56px, and expansive 120px section breathing room. Containers should feel broad and editorial, with strong left-right gutters and generous vertical separation between hero, CTA, and supporting sections. Buttons and cards should retain roomy internal padding so the interface feels calm and premium.

## Elevation & Depth
The system is intentionally flat overall, with very limited shadow usage. Hierarchy comes from tonal contrast, bright-on-dark color pairing, and bordered containers rather than heavy depth effects. When depth is needed, use subtle one-pixel borders and soft tonal blocks instead of layered shadows. Shadows should remain minimal and mostly reserved for transient overlays or the occasional elevated surface.

## Shapes
The shape language is soft-rectangular and modern, with small radii on actionable UI and more pronounced rounding on large editorial blocks. Buttons use a 4px corner radius, while cards can open slightly to 8px for a more container-like feel. The overall impression should remain crisp and architectural, not pill-shaped or playful. Large hero panels can keep broader rounded corners to echo the friendly, approachable brand energy.

## Components
Buttons are the clearest functional system element. `button-primary` should use the light ivory fill with dark green text, 17px/30px/16px padding, 50px height, and a 4px radius; it is the main call to action and should feel solid but understated. `button-secondary` uses transparent fill with ivory text and border on dark backgrounds, matching the same size and padding as primary. `button-link` is a minimal text-only action for utility navigation or inline references and should remain unboxed. Hover states should preserve the same tonal contrast rather than introducing bright gradients or heavy shadows.

Cards should use dark surfaces, subtle 1px borders, and 8px radius, with 16px padding for compact content clusters. Inputs should mirror cards in tonal treatment, keeping the same dark background and soft radius so form elements blend into the system instead of feeling chrome-like. Badges or chips, when needed, should be small, high-contrast capsules with Graphik text and restrained padding. Navigation items should rely on Graphik labels and quiet spacing rather than decorative separators. Any cookie banners, alerts, or informational overlays should stay light and readable, with clear contrast and modest borders rather than dramatic elevation.

## Do's and Don'ts
- Do use Grenette for hero-scale messaging and Times New Roman for long-form supporting copy.
- Do keep action buttons compact, rectangular, and consistently 50px tall.
- Do preserve the dark, editorial atmosphere with deep green and ivory contrasts.
- Do prefer borders and tonal shifts over shadows for hierarchy.
- Don't introduce bright saturated accent colors outside the established green/ivory palette.
- Don't round buttons or cards into pills; keep the corners modest and controlled.
- Don't use dense, cramped layouts; the brand depends on breathing room.
- Don't replace the serif-led voice with a purely sans-serif interface.