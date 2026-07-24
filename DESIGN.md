---
name: Celestial Citrus Dream
colors:
  surface: '#0b1229'
  surface-dim: '#0b1229'
  surface-bright: '#323851'
  surface-container-lowest: '#060d24'
  surface-container-low: '#141a32'
  surface-container: '#181e36'
  surface-container-high: '#222941'
  surface-container-highest: '#2d344c'
  on-surface: '#dce1ff'
  on-surface-variant: '#dac2ae'
  inverse-surface: '#dce1ff'
  inverse-on-surface: '#292f48'
  outline: '#a28d7a'
  outline-variant: '#544434'
  surface-tint: '#ffb86b'
  primary: '#ffc68b'
  on-primary: '#492900'
  primary-container: '#ff9f1c'
  on-primary-container: '#683c00'
  inverse-primary: '#895100'
  secondary: '#fff9ef'
  on-secondary: '#3a3000'
  secondary-container: '#ffdb3c'
  on-secondary-container: '#725f00'
  tertiary: '#c3cfff'
  on-tertiary: '#1c2d60'
  tertiary-container: '#a3b3ef'
  on-tertiary-container: '#344478'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdcbc'
  primary-fixed-dim: '#ffb86b'
  on-primary-fixed: '#2c1700'
  on-primary-fixed-variant: '#683d00'
  secondary-fixed: '#ffe16d'
  secondary-fixed-dim: '#e9c400'
  on-secondary-fixed: '#221b00'
  on-secondary-fixed-variant: '#544600'
  tertiary-fixed: '#dce1ff'
  tertiary-fixed-dim: '#b5c4ff'
  on-tertiary-fixed: '#02174b'
  on-tertiary-fixed-variant: '#344478'
  background: '#0b1229'
  on-background: '#dce1ff'
  surface-variant: '#2d344c'
  deep-nebula: '#1A1B41'
  starlight-white: '#F0F4FF'
  dream-purple: '#4B3B7B'
  comet-grey: '#4E596F'
typography:
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Merriweather
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 30px
  body-md:
    fontFamily: Merriweather
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 28px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 24px
  card-gap: 20px
  section-margin: 40px
  touch-target: 48px
---

## Brand & Style

The design system is crafted to evoke a sense of safety, warmth, and bedtime tranquility for a pre-teen audience. It leans heavily into a **Tactile Glassmorphism** style, combining the soft, translucent layers of frosted glass with rounded, physical metaphors that feel like plush toys or smooth river stones. 

The aesthetic is "Quietly Magical." It avoids the high-energy stimulation of typical children's apps in favor of a low-arousal, healing environment. Visuals prioritize depth through soft glows (simulating starlight) rather than harsh shadows. The "Star Orange" IP acts as a guiding companion, appearing in a consistent 3D-rendered style that feels touchable and friendly.

**Key Moods:**
*   **Healing:** Gentle transitions and soft-edged containers.
*   **Safe:** High legibility and clear, non-threatening iconography.
*   **Professional:** A structured, intentional layout that respects the maturity of 8-13 year olds while remaining whimsical.

## Colors

The palette is anchored in a multi-tonal dark mode to simulate the night sky without the starkness of pure black. 

*   **Primary (#FF9F1C):** A warm, energetic orange used for primary actions, progress indicators, and the core IP color. 
*   **Secondary (#FFD700):** A soft yellow reserved for "Star" moments—ratings, favorites, and text highlighting during audio playback.
*   **Backgrounds:** `Neutral (#0A1128)` serves as the base layer, while `deep-nebula` and `dream-purple` are used for gradients and container backgrounds to add depth and "nighttime" variety.
*   **Text:** `starlight-white` provides high contrast for body text, ensuring readability in low-light environments.

## Typography

The system employs a dual-font strategy to balance character and utility. 

**Headlines & UI:** **Plus Jakarta Sans** is used for all interface elements. Its soft, geometric curves match the "rounded" theme of the brand and remain legible even at smaller sizes in dark mode.

**Story Content:** **Merriweather** is the primary choice for story bodies. As a serif font designed for screens, it provides the "literary" feel of a physical book while offering exceptional readability. The line height is intentionally generous (1.6x - 1.8x) to prevent eye strain before sleep. In the settings, users can scale this font size up for a more comfortable reading experience.

## Layout & Spacing

This design system uses a **Fluid Grid** with generous safe areas to ensure a "breathable" feel. 

*   **Grid:** A 4-column grid for mobile and 8-column for tablet. 
*   **Margins:** 24px side margins on mobile to keep content away from screen edges, enhancing the "safe" feeling.
*   **Vertical Rhythm:** Based on an 8px base unit. Component spacing (e.g., between an icon and text) uses 8px or 12px, while larger structural gaps use 24px or 40px.
*   **Adaptation:** On tablets, story cards reflow from a vertical stack to a grid. The reading view maintains a "book-like" maximum width of 680px, centered on the screen, to prevent excessively long line lengths.

## Elevation & Depth

Depth is established through **Tonal Layering** and **Luminous Blurs** rather than traditional drop shadows.

1.  **Base Layer:** The deepest navy (#0A1128).
2.  **Surface Layer:** Semi-transparent "Glass" containers (10-15% white overlay) with a 20px backdrop blur. This creates a sense of the cards floating in a misty atmosphere.
3.  **Interactive Layer:** Elements like the active "Star Orange" button use a soft outer glow in the primary color (#FF9F1C) to simulate light emission.
4.  **Highlighting:** During audio playback, the current sentence is not just colored but sits on a subtle, luminous background "wash" of soft yellow.

## Shapes

The shape language is strictly organic and friendly. 
*   **Core Components:** Use a 16px radius for standard buttons and inputs.
*   **Large Cards:** Use a significant 24px to 32px radius to emphasize the "plush" or "cute" aesthetic. 
*   **Iconography:** Icons are thick-stroked with rounded terminals. Avoid any sharp 90-degree angles in the UI. 
*   **Decorative Elements:** Use "Squircle" shapes for IP avatars and profile settings to maintain a cohesive softness throughout the app.

## Components

### Buttons
*   **Primary:** Pill-shaped, #FF9F1C background, dark navy text. Includes a soft orange glow on tap.
*   **Secondary/Ghost:** Transparent background with a 2px starlight-white border and rounded corners.

### Story Cards
*   Large radius (24px+). 
*   Features a subtle gradient background from `deep-nebula` to `neutral`. 
*   Contains "Star Orange" accent illustrations in the corner. 
*   Includes "Tags" as small, pill-shaped chips with low-opacity purple backgrounds.

### Audio Player
*   **Visualizer:** A soft, pulsating "Star" or "Moon" icon that reacts to the volume of the narration.
*   **Controls:** Oversized touch targets (minimum 56px) for play/pause, using physical "pressed" states (neomorphic influence) to feel tactile.

### Input Fields & Toggles
*   Fields use a "deep-nebula" background with soft-yellow focus borders.
*   Toggles are designed to look like "moons" (off) and "suns" (on) to fit the theme.

### Empty States & Feedback
*   Feature full-page illustrations of Star Orange (e.g., sleeping for "No Stories," searching with a telescope for "No Connection").
*   Loading states use a rotating star animation.