# Animation Specifications Guide

This document provides detailed specifications for all animations implemented in the UI/UX optimization.

## Node Animations

### 1. Ripple Effect
```typescript
// Location: CustomNode.tsx, handleClick()
Trigger: onClick
Animation Properties:
  - Position: Calculated from click coordinates (x, y)
  - Initial State: { width: 0, height: 0, opacity: 0.6 }
  - Final State: { width: 100, height: 100, opacity: 0 }
  - Duration: 600ms
  - Easing: easeOut
  - Cleanup: Auto-remove after animation
```

**Visual Description**: A white semi-transparent circle that expands from the click point and fades out.

### 2. Node Scale Animation
```typescript
// Location: CustomNode.tsx, motion.div animate prop
Trigger: Node selection state change
Animation Properties:
  - Default Scale: 1.0
  - Selected Scale: 1.08
  - Hover Scale: 1.02 (when not dimmed)
  - Duration: 250ms
  - Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

### 3. Node Glow Effect
```typescript
// Location: CustomNode.tsx, className
Trigger: Node selection
Visual Properties:
  - Box Shadow: 0 0 20px rgba(74, 222, 128, 0.6)
  - Border: 2px solid #4ade80 (green-400)
  - Ring: 4px for journey nodes
  - Transition: 300ms ease-out
```

### 4. Gradient Overlay
```typescript
// Location: CustomNode.tsx, motion.div with gradient
Trigger: Mouse enter
Animation Properties:
  - Initial Position: x: -100%
  - Animated Position: x: 100%
  - Condition: Only when isHovered
  - Duration: 700ms
  - Easing: easeInOut
```

### 5. Icon Rotation
```typescript
// Location: CustomNode.tsx, icon wrapper
Trigger: Mouse hover
Animation Properties:
  - Default Rotation: 0deg
  - Hover Rotation: 12deg
  - Duration: 300ms
  - Applied to: Node type icons
```

### 6. Expand/Collapse Indicator
```typescript
// Location: CustomNode.tsx, expand/collapse span
Trigger: Node expansion state change
Animation Properties:
  - Collapsed Rotation: 0deg
  - Expanded Rotation: 180deg
  - Duration: 300ms
  - Easing: easeInOut
```

## Journey Overlay Animations

### 1. Overlay Entry/Exit
```typescript
// Location: JourneyOverlay.tsx, motion.div wrapper
Trigger: journey.isActive state change
Animation Properties:
  Entry:
    - Initial: { y: 100, opacity: 0, scale: 0.95 }
    - Animate: { y: 0, opacity: 1, scale: 1 }
  Exit:
    - Animate: { y: 100, opacity: 0, scale: 0.95 }
  Duration: 300ms
  Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

### 2. Sparkles Icon Animation
```typescript
// Location: JourneyOverlay.tsx, Sparkles icon wrapper
Trigger: Always when journey is active
Animation Properties:
  - Scale: [1, 1.2, 1]
  - Opacity: [0.7, 1, 0.7]
  - Duration: 2000ms
  - Repeat: Infinity
```

### 3. Progress Bar Animation
```typescript
// Location: JourneyOverlay.tsx, progress bar div
Trigger: Journey progress change
Animation Properties:
  - Initial Width: 0%
  - Animated Width: progress% (calculated)
  - Duration: 500ms
  - Easing: easeOut
```

### 4. Tag Stagger Animation
```typescript
// Location: JourneyOverlay.tsx, tag mapping
Trigger: Tags render
Animation Properties:
  - Initial Scale: 0
  - Animate Scale: 1
  - Delay: 0.3 + (index * 0.05)s
  - Stagger: 50ms between each tag
```

### 5. Branch Option Cards
```typescript
// Location: JourneyOverlay.tsx, branch option buttons
Trigger: Branch selection mode
Animation Properties:
  Entry:
    - Initial: { opacity: 0, y: 20 }
    - Animate: { opacity: 1, y: 0 }
    - Delay: index * 0.1s (staggered)
  Hover:
    - Scale: 1.05
    - Y Offset: -5px
  Tap:
    - Scale: 0.98
```

### 6. Close Button
```typescript
// Location: JourneyOverlay.tsx, X button
Trigger: Mouse hover/tap
Animation Properties:
  Hover:
    - Scale: 1.1
    - Rotation: 90deg
  Tap:
    - Scale: 0.9
```

### 7. Navigation Buttons
```typescript
// Location: JourneyOverlay.tsx, Back/Next buttons
Trigger: Mouse hover/tap
Animation Properties:
  Back Button Hover:
    - Scale: 1.05
    - X Offset: -5px
  Next Button Hover:
    - Scale: 1.05
    - Box Shadow: Pulsing effect
  Tap:
    - Scale: 0.95
```

## Evidence Tooltip Animations

### 1. Tooltip Entry/Exit
```typescript
// Location: EvidenceQuestionTooltip.tsx, motion.div
Trigger: isVisible prop change
Animation Properties:
  Entry:
    - Initial: { opacity: 0, y: 10, scale: 0.9 }
    - Animate: { opacity: 1, y: 0, scale: 1 }
  Exit:
    - Animate: { opacity: 0, y: 10, scale: 0.9 }
  Duration: 200ms
  Easing: easeOut
```

### 2. Help Icon Badge
```typescript
// Location: CustomNode.tsx, evidence question button
Trigger: Mouse hover/tap
Animation Properties:
  Hover: { scale: 1.1 }
  Tap: { scale: 0.95 }
  Background: Gradient amber-400 to amber-600
```

## Evidence Card Animations

### 1. Card Entry
```typescript
// Location: EvidenceCard.tsx, motion.article
Trigger: Component mount
Animation Properties:
  - Initial: { opacity: 0, y: 20 }
  - Animate: { opacity: 1, y: 0 }
  - Duration: 200ms
```

### 2. Card Hover
```typescript
// Location: EvidenceCard.tsx, whileHover
Trigger: Mouse enter (when not disabled)
Animation Properties:
  - Scale: 1.02
  - Y Offset: -2px
```

### 3. Card Tap
```typescript
// Location: EvidenceCard.tsx, whileTap
Trigger: Mouse down (when not disabled)
Animation Properties:
  - Scale: 0.98
```

### 4. Selection Indicator
```typescript
// Location: EvidenceCard.tsx, checkmark div
Trigger: selected prop becomes true
Animation Properties:
  - Initial: { scale: 0, rotate: -180deg }
  - Animate: { scale: 1, rotate: 0deg }
  - Type: spring
  - Spring Config: { stiffness: 200, damping: 15 }
```

### 5. Expand/Collapse
```typescript
// Location: EvidenceCard.tsx, metadata section
Trigger: isExpanded state change
Animation Properties:
  Entry:
    - Initial: { opacity: 0, height: 0 }
    - Animate: { opacity: 1, height: 'auto' }
  Exit:
    - Animate: { opacity: 0, height: 0 }
  Duration: 300ms
```

### 6. Expand Button
```typescript
// Location: EvidenceCard.tsx, expand button
Trigger: Mouse hover/tap
Animation Properties:
  Hover: { x: 5px }
  Tap: { scale: 0.95 }
```

## Loading Skeleton Animations

### 1. Skeleton Entry
```typescript
// Location: LoadingSkeleton.tsx, each skeleton
Trigger: Component mount
Animation Properties:
  Node/Card:
    - Initial: { opacity: 0, y: 20 }
    - Animate: { opacity: 1, y: 0 }
    - Delay: index * 0.1s
  Text:
    - Initial: { opacity: 0 }
    - Animate: { opacity: 1 }
    - Delay: index * 0.05s
```

### 2. Shimmer Effect
```typescript
// Location: LoadingSkeleton.tsx, shimmer gradient
Trigger: Always (continuous)
Animation Properties:
  - Initial Position: x: -100%
  - Animated Position: x: 100%
  - Repeat: Infinity
  - Duration: 1500ms
  - Easing: linear
```

## Edge Animations

### 1. Journey Path Edges
```typescript
// Location: GalaxyGraph.tsx, QueryTreeGraph.tsx
Trigger: Edge is on journey path
Visual Properties:
  - Type: smoothstep (curved)
  - Animated: true
  - Stroke: #10b981 (green-500)
  - Stroke Width: 3px
  - Opacity: 1.0
```

### 2. Default Edges
```typescript
// Location: GalaxyGraph.tsx, QueryTreeGraph.tsx
Visual Properties:
  - Type: smoothstep (curved)
  - Animated: false
  - Stroke: #4ade80 (green-400) or custom color
  - Stroke Width: 2px
  - Opacity: 0.6
```

## Dimming Animation

### 1. Non-related Node Dimming
```typescript
// Location: CustomNode.tsx, motion.div animate
Trigger: isDimmed prop becomes true
Animation Properties:
  - Opacity: 0.3
  - Filter: blur(2px)
  - Duration: 250ms
  - Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

## Performance Characteristics

### GPU-Accelerated Properties
All animations use GPU-accelerated CSS properties:
- ✅ transform (translate, scale, rotate)
- ✅ opacity
- ✅ filter (when necessary)

### Animation Timing Strategy
- **Instant feedback**: < 100ms (not used, too jarring)
- **Quick**: 200ms (tooltips, ripples)
- **Standard**: 250-300ms (most interactions)
- **Smooth**: 500ms (progress bars)
- **Slow**: 700-800ms (focus transitions)
- **Continuous**: 1-2s (pulse, shimmer)

### Easing Functions Used
1. `cubic-bezier(0.4, 0, 0.2, 1)` - Material Design standard
2. `easeOut` - Decelerating motion
3. `easeInOut` - Smooth start and end
4. `linear` - Continuous animations
5. `spring` - Playful, bouncy interactions

### Frame Rate Targets
- Desktop: 60fps (16.67ms per frame)
- Mobile: 30-60fps (adaptive)
- Reduced Motion: < 1ms (essentially disabled)

## Accessibility Considerations

### Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
  .motion-reduce {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Focus Indicators
All interactive elements maintain focus-visible states:
- Visible ring on keyboard focus
- Sufficient color contrast
- Not removed by animations

### ARIA Support
- Labels maintained through animations
- States updated correctly
- Expanded/collapsed states communicated

## Browser Compatibility

Tested and optimized for:
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Android)

Features used:
- CSS transforms (widely supported)
- CSS filters (blur) - IE not supported
- Framer Motion (modern browsers only)
- React 19 (latest)

## Troubleshooting

### If animations are choppy:
1. Check CPU/GPU usage
2. Reduce number of simultaneous animations
3. Verify using GPU-accelerated properties
4. Check for layout thrashing (forced reflows)

### If animations don't play:
1. Check prefers-reduced-motion setting
2. Verify Framer Motion is loaded
3. Check browser console for errors
4. Verify component is mounted correctly

## Metrics

### Bundle Impact
- Framer Motion: ~35KB (gzipped)
- Custom animation code: ~2KB (gzipped)
- Total impact: ~37KB additional

### Performance Budget
- FCP (First Contentful Paint): < 1.5s
- TTI (Time to Interactive): < 3.5s
- Animation FPS: 60fps target
- Memory: < 50MB additional for animations
