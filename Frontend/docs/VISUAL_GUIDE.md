# Visual Demonstration Guide

This guide provides visual descriptions of the UI/UX improvements implemented.

## 🎬 Animation Showcase

### 1. Node Interactions

#### Before
```
┌─────────────────┐
│   Topic Node    │  ← Static, no feedback
└─────────────────┘
```

#### After
```
      💭 [Evidence Q]     ← Evidence question indicator
      ↓
┌─────────────────┐
│   Topic Node    │  ← Click triggers:
│                 │     • Ripple effect (⭕ expanding circle)
│   (( ⭕ ))     │     • Scale up to 1.08
└─────────────────┘     • Glow effect (green shadow)
   ✨ Animated          • Color transition
   gradient overlay
```

**Interactions**:
1. **Hover**: Gradient sweeps left→right, scale 1.02, icon rotates 12°
2. **Click**: Ripple expands from click point, node scales up
3. **Selected**: Glowing green border, elevated with shadow
4. **Evidence Icon**: Pulsing amber badge, click shows tooltip

---

### 2. Evidence Question Tooltip

#### Visual Structure
```
       ┌──────────────────────────────┐
       │ 💭 EVIDENCE QUESTIONS        │ ← Semi-transparent amber
       │                              │   gradient background
       │ • What methodology was used? │
       │ • How was data validated?    │
       │ • Were there limitations?    │
       │                              │
       │ +2 more questions            │ ← Overflow indicator
       └────────────┬─────────────────┘
                    │ ← Arrow pointing down
              ┌─────▼─────┐
              │   Node    │
              └───────────┘
```

**Behavior**:
- **Appearance**: Fade in + scale from 0.9 → 1.0 (200ms)
- **Disappearance**: Fade out + scale to 0.9 (200ms)
- **Trigger**: Hover over node OR click evidence icon
- **Max Width**: 384px (max-w-xs)
- **Z-Index**: 50 (above nodes)

---

### 3. Journey Mode Experience

#### Entry Animation
```
Frame 1 (0ms):           Frame 2 (150ms):         Frame 3 (300ms):
                         ┌─────────────┐          ┌─────────────┐
                         │  Journey    │          │  Journey    │
                         │   Mode      │          │   Mode ⭐   │
                         └─────────────┘          └─────────────┘
   [Below screen]        [Sliding up]             [Fully visible]
   Opacity: 0            Opacity: 0.5             Opacity: 1
   Scale: 0.95           Scale: 0.975             Scale: 1.0
```

#### Journey Overlay Components
```
┌────────────────────────────────────────────────┐
│ JOURNEY MODE ⭐                            ✕   │ ← Pulsing Sparkles
│ Current Node Name                              │
│ [tag1] [tag2] [tag3] ← Staggered entrance     │
│                                                │
│ 📍 Step 5                        75% complete │
│ ████████████████████░░░░░░░     ← Animated    │
│                                                │
│ [Path breadcrumbs scroll]                     │
│                                                │
│ [← Back]              [Next Step →]           │ ← Hover effects
│                       ✨ Pulsing glow          │
└────────────────────────────────────────────────┘
```

**Animations**:
1. **Overlay**: Slides up from bottom with fade and scale
2. **Sparkles Icon**: Scale & opacity pulse (2s loop)
3. **Progress Bar**: Width animates smoothly (500ms)
4. **Tags**: Staggered entrance (50ms delay each)
5. **Buttons**: Scale + translate on hover

---

### 4. Branch Selection Mode

```
┌────────────────────────────────────────────────┐
│ 🔀 BRANCH SELECTION                        ✕   │ ← Rotating icon
│ Choose your path                               │
│                                                │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│ │ Option A │  │ Option B │  │ Option C │     │ ← Cards animate
│ │          │  │          │  │          │     │   in with stagger
│ └──────────┘  └──────────┘  └──────────┘     │
│     ↑              ↑              ↑           │
│  Hover         Hover          Hover           │
│  scale 1.05    scale 1.05    scale 1.05       │
│  y: -5px       y: -5px       y: -5px          │
└────────────────────────────────────────────────┘
```

**Animation Timeline**:
```
0ms:   Branch mode activates
100ms: Option A appears (opacity 0→1, y 20→0)
200ms: Option B appears
300ms: Option C appears
Hover: Scale 1.05 + translate up 5px
Click: Scale 0.98 (quick tap feedback)
```

---

### 5. Node States Comparison

#### Default State
```
┌─────────────────┐
│ 🌐 Topic        │ ← Gray gradient background
│                 │   Border: white/20
└─────────────────┘   Shadow: minimal
```

#### Hovered State
```
┌─────────────────┐
│ 🌐 Topic        │ ← Gradient overlay sweeps
│   ╱╱╱╱╱╱╱      │   Scale: 1.02
└─────────────────┘   Icon rotates 12°
```

#### Selected State
```
┌═════════════════┐ ← Green border (2px)
║ 🌐 Topic        ║   Scale: 1.08
║                 ║   Box shadow: green glow
║    ⭕ ripple   ║   Ring: 2px green-400
└═════════════════┘
```

#### Journey Current Node
```
╔═════════════════╗ ← Green border (2px)
║ 📍 Topic        ║   Scale: 1.08
║                 ║   Ring: 4px green-400/70
║                 ║   Shadow: 2xl green-500/50
║    ⭕ ripple   ║   Pulsing pin badge
╚═════════════════╝
```

#### Decision Point
```
┌─────────────────┐
│ 3️⃣ Topic        │ ← Purple gradient
│                 │   Badge shows child count
│                 │   Border: purple-400
└─────────────────┘
```

#### Dimmed (Non-Related)
```
┌ ─ ─ ─ ─ ─ ─ ─ ┐  ← Opacity: 0.3
  Topic (blur)      Filter: blur(2px)
└ ─ ─ ─ ─ ─ ─ ─ ┘  Cursor: not-allowed
```

---

### 6. Edge Styling

#### Default Edge
```
Node A ───────────> Node B
       └─ Smoothstep curve
          Stroke: #4ade80 (green-400)
          Width: 2px
          Opacity: 0.6
```

#### Journey Path Edge
```
Node A ═══════════> Node B
       └─ Smoothstep curve
          Stroke: #10b981 (green-500)
          Width: 3px
          Opacity: 1.0
          Animated: flowing effect
```

#### Custom Color Edge
```
Node A ~~~~~~~~~~~> Node B
       └─ Smoothstep curve
          Stroke: custom color from data
          Width: 2px
          Opacity: 0.6
```

---

### 7. Evidence Card States

#### Default
```
┌────────────────────────────────┐
│ 📄 Evidence Source             │
│                                │
│ Lorem ipsum dolor sit amet...  │
└────────────────────────────────┘
```

#### Hovered
```
┌────────────────────────────────┐ ↑ 2px
│ 📄 Evidence Source             │ Scale: 1.02
│                                │ Border: cyan-400/20
│ Lorem ipsum dolor sit amet...  │
└────────────────────────────────┘
```

#### Selected
```
┌════════════════════════════════┐
│ 📄 Evidence Source          ✓  │ ← Spring-animated
│                                │   checkmark
│ Lorem ipsum dolor sit amet...  │   Border: cyan-400/60
│                                │   Glow: cyan shadow
└════════════════════════════════┘
```

#### Expanded
```
┌────────────────────────────────┐
│ 📄 Evidence Source             │
│                                │
│ Full evidence text here with   │
│ complete details...            │
│                                │
│ ▼ KEY CLAIMS                   │ ← Animated height
│ • Claim 1                      │   transition
│ • Claim 2                      │   300ms ease
│                                │
│ ? QUESTIONS                    │
│ • Question 1                   │
│ • Question 2                   │
└────────────────────────────────┘
```

---

### 8. Loading States

#### Skeleton - Node Variant
```
┌─────────────────┐
│ ░ ░░░░░         │ ← Shimmer effect
│   ░░░░          │   slides left to right
└─────────────────┘   every 1.5s
   ╱╱╱╱╱╱╱╱╱        Gradient overlay
```

#### Skeleton - Card Variant
```
┌────────────────────────────────┐
│ ░░░░░░░░░                      │ ← Header shimmer
│                                │
│ ░░░░░░░░░░░░░░░░░░░░░░       │ ← Content shimmer
│ ░░░░░░░░░░░░░░               │
└────────────────────────────────┘
```

#### Loading Animation Timeline
```
0ms:   Skeleton appears (opacity 0→1, y 20→0)
∞:     Shimmer continuously slides across
       x: -100% → 100% (1.5s linear repeat)
```

---

### 9. Ripple Effect Details

```
Click at point (x, y)
         │
         ▼
Time 0ms:     ⚫ (dot at click point)
              width: 0, height: 0
              opacity: 0.6

Time 200ms:   ⭕ (expanding circle)
              width: 33, height: 33
              opacity: 0.4

Time 400ms:   ⭕⭕ (larger circle)
              width: 66, height: 66
              opacity: 0.2

Time 600ms:   ⭕⭕⭕ (fully expanded)
              width: 100, height: 100
              opacity: 0
              [Auto-removed]
```

---

### 10. Performance Visualization

#### GPU-Accelerated Properties ✅
```
transform: translate3d(0, 0, 0)  ← GPU layer
transform: scale(1.08)           ← GPU layer
opacity: 0.3                     ← GPU layer
filter: blur(2px)                ← GPU layer (modern browsers)
```

#### Frame Timeline (60fps)
```
Frame 1  (0ms):    Initial state
Frame 2  (16ms):   Position updated
Frame 3  (33ms):   Position updated
Frame 4  (50ms):   Position updated
...
Frame 15 (250ms):  Animation complete
```

---

## 🎨 Color Palette

### Node States
- **Default**: Gray-800/50 → Black/70 gradient
- **Selected**: Green-400 border, Green-500/50 shadow
- **Journey**: Green-400/70 ring, Green-500/50 shadow
- **Decision**: Purple-800/60 → Purple-900/40 gradient
- **Gap/Leaf**: Amber-800/60 → Amber-900/40 gradient

### Journey Overlay
- **Background**: Slate-900/90 with backdrop blur
- **Border**: Emerald-500/30
- **Progress**: Emerald-500 → Cyan-500 gradient
- **Text**: White with various opacities

### Evidence Tooltip
- **Background**: Amber-900/95 → Amber-950/95
- **Border**: Amber-500/30
- **Text**: Amber-100/90 to Amber-200
- **Icon**: Amber-400

### Edges
- **Default**: Green-400 (#4ade80), opacity 0.6
- **Journey**: Green-500 (#10b981), opacity 1.0
- **Custom**: Configurable via edge.data.color

---

## 📱 Responsive Behavior

### Desktop (> 768px)
- All animations run at 60fps
- Full feature set enabled
- Hover states fully interactive

### Tablet (768px - 1024px)
- Animations optimized for touch
- Tap feedback emphasized
- Hover states work on tap

### Mobile (< 768px)
- Touch-optimized interactions
- Reduced animation complexity
- Larger touch targets

---

## ♿ Accessibility Features

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  /* All animations disabled */
  /* Transitions set to 0.01ms */
  /* Instant state changes only */
}
```

### Keyboard Navigation
- Tab through nodes ✓
- Enter to select ✓
- Escape to deselect ✓
- Focus visible rings ✓

### Screen Readers
- ARIA labels maintained ✓
- State changes announced ✓
- Button roles preserved ✓

---

## 🎯 User Interaction Flow

### Exploring Nodes
```
1. User sees graph of nodes
2. Hovers over node → gradient overlay animates
3. Clicks node → ripple expands, node scales up
4. Node selected → glows green, others dim
5. Sees evidence icon → clicks to show tooltip
6. Tooltip appears → shows questions with fade-in
7. User clicks elsewhere → node deselects, others brighten
```

### Starting Journey
```
1. User clicks "Start Journey"
2. Overlay slides up from bottom with fade
3. Progress bar appears and fills
4. Current node gets pin indicator
5. Path highlights in green
6. User sees branch options → cards stagger in
7. User selects branch → smooth transition
8. Process repeats for next node
```

### Viewing Evidence
```
1. User sees evidence card
2. Hovers → card lifts and scales
3. Clicks → checkmark springs in
4. Card highlights with cyan glow
5. User clicks "More" → content expands smoothly
6. Metadata appears with fade-in
7. User clicks "Less" → content collapses
```

---

## 🎬 Animation Best Practices Applied

1. **Easing Functions**: Natural cubic-bezier curves
2. **Duration**: Quick enough for responsiveness (200-300ms)
3. **GPU Acceleration**: Transform and opacity only
4. **Staggering**: Delays create rhythm and flow
5. **Spring Physics**: For playful interactions (checkmarks)
6. **Continuous Motion**: Shimmer and pulse for emphasis
7. **Purposeful**: Every animation serves a function
8. **Accessible**: Respects user preferences

---

## 📊 Impact Summary

### Before Implementation
- Static nodes
- No visual feedback
- Instant state changes
- Hard to track journey
- Evidence questions hidden
- Basic loading spinners

### After Implementation
- ✨ Animated nodes with ripples
- 🎯 Clear visual feedback on every interaction
- 🌊 Smooth state transitions (250-300ms)
- 🛤️ Clear journey path visualization
- 💭 Evidence questions easily accessible
- ⏳ Professional shimmer loading states

### User Experience Improvement
- **Engagement**: ⬆️ More interactive and delightful
- **Clarity**: ⬆️ Clear state communication
- **Feedback**: ⬆️ Instant visual confirmation
- **Flow**: ⬆️ Smooth, natural transitions
- **Professional**: ⬆️ Polished, modern feel
