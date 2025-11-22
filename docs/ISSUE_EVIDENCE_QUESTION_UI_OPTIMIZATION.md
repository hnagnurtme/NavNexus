# 🎨 Tối ưu UI/UX cho Evidence Question Raise và Node Interactions

## 📝 Mô tả

Cải thiện trải nghiệm người dùng khi tương tác với evidence questions và navigation nodes thông qua việc tối ưu hiển thị, animation và focus effects.

## 🎯 Mục tiêu

Tạo trải nghiệm tương tác mượt mà, trực quan và hấp dẫn hơn cho người dùng khi:
- Xem evidence questions
- Click vào nodes
- Bắt đầu journey
- Điều hướng giữa các nodes

## ✨ Yêu cầu chi tiết

### 1. Evidence Question Display
**Hiện tại:** Evidence questions hiển thị không rõ ràng/trực quan
**Mong muốn:**
- [ ] Thêm **icon** đặc trưng cho evidence question (ví dụ: 💭, 🔍, hoặc custom icon)
- [ ] Hiển thị câu hỏi dưới dạng **tooltip nhỏ gọn** ngay phía trên node
- [ ] Tooltip xuất hiện khi:
  - Hover vào node
  - Click vào icon evidence
- [ ] Design tooltip:
  - Background: semi-transparent hoặc có shadow để nổi bật
  - Font size: nhỏ hơn node text nhưng vẫn dễ đọc
  - Max width: giới hạn để không che phủ quá nhiều nodes khác
  - Animation: fade in/out mượt mà

**Mockup/Reference:**
```
       ┌─────────────────────┐
       │ 💭 Evidence Q here? │  ← Tooltip với icon
       └──────────┬──────────┘
                  │
            ┌─────▼─────┐
            │   Node    │
            │  Content  │
            └───────────┘
```

### 2. Node Click Animation
**Hiện tại:** Click vào node có thể thiếu feedback
**Mong muốn:**
- [ ] **Ripple effect** khi click (Material Design style)
- [ ] **Scale animation**: node phóng to nhẹ (scale 1.05-1.1) khi active
- [ ] **Glow effect**: viền sáng/shadow mở rộng khi được chọn
- [ ] **Color transition**: màu nền chuyển đổi mượt mà
- [ ] Thời gian animation: ~200-300ms (không quá nhanh/chậm)

**CSS Example:**
```css
.node-active {
  transform: scale(1.08);
  box-shadow: 0 0 20px rgba(primary-color, 0.6);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### 3. Focus/Highlight Effect
**Hiện tại:** Node được chọn không đủ nổi bật
**Mong muốn:**
- [ ] **Dim/blur** các nodes không liên quan (opacity giảm xuống ~0.5)
- [ ] **Spotlight effect**: node được chọn sáng hơn so với background
- [ ] **Camera pan/zoom**: tự động center vào node được chọn (nếu sử dụng canvas/svg)
- [ ] **Breadcrumb highlight**: highlight path từ start đến node hiện tại
- [ ] **Smooth transition**: tất cả effects có animation mượt mà

### 4. Start Journey Experience
**Hiện tại:** Start journey thiếu sự hấp dẫn
**Mong muốn:**
- [ ] **Entry animation**:
  - Fade in từ giữa màn hình
  - Hoặc zoom in effect
  - Hoặc slide in từ một hướng
- [ ] **Progress indicator**: hiển thị loading/preparing journey
- [ ] **Path preview**: highlight/animate đường đi dự kiến (nếu có)
- [ ] **Welcome message**: micro-interaction chào mừng người dùng
- [ ] **Sound effect** (optional): âm thanh nhẹ khi bắt đầu

### 5. Fork/Branch Display
**Hiện tại:** Cách hiển thị ngã rẽ chưa rõ ràng
**Mong muốn:**
- [ ] **Branching visualization**:
  - Đường lines kết nối rõ ràng từ parent đến child nodes
  - Curved/bezier lines thay vì straight lines
  - Animated line drawing effect khi hiển thị
- [ ] **Fork indicator**:
  - Icon/badge hiển thị số lượng choices
  - Ví dụ: "2 paths available" hoặc fork icon với số
- [ ] **Hover preview**:
  - Khi hover vào fork, highlight tất cả paths có thể đi
  - Hiển thị preview của mỗi option
- [ ] **Color coding**:
  - Mỗi nhánh có màu khác nhau (subtle difference)
  - Maintain color consistency theo path được chọn

**Visual Example:**
```
              [Parent Node]
                    │
        ┌───────────┴───────────┐
        │                       │
   [Option A]              [Option B]
   (Color 1)               (Color 2)
```

### 6. General Animations
- [ ] **Page transitions**: smooth transitions giữa các states
- [ ] **Loading states**: skeleton screens hoặc shimmer effects
- [ ] **Micro-interactions**:
  - Button hover effects
  - Icon animations
  - Tooltip animations
- [ ] **Performance**:
  - Sử dụng CSS transforms và opacity (GPU accelerated)
  - Debounce/throttle events để tránh lag
  - Lazy load animations cho mobile

## 🎨 Design Principles

1. **Clarity**: Người dùng phải hiểu ngay được họ đang ở đâu và có thể đi đâu
2. **Feedback**: Mọi tương tác phải có visual feedback rõ ràng
3. **Smoothness**: Animations mượt mà, không giật lag
4. **Consistency**: Style và behavior nhất quán trong toàn bộ app
5. **Accessibility**: Đảm bảo animations không gây khó chịu, có option tắt nếu cần

## 🛠️ Technical Stack Suggestions

- **Animation Libraries**:
  - Framer Motion (React animations)
  - React Spring (physics-based animations)
  - GSAP (complex timeline animations)
  - CSS Animations (simple effects)

- **Graph/Node Visualization**:
  - React Flow (nếu chưa dùng)
  - D3.js (custom visualization)
  - Cytoscape.js (graph theory)

## 📋 Acceptance Criteria

- [ ] Evidence question icon hiển thị rõ ràng và có tooltip
- [ ] Node click có ít nhất 2 loại animation (scale + glow/shadow)
- [ ] Khi click node, các nodes không liên quan bị dim/blur
- [ ] Start journey có entry animation
- [ ] Fork/branches hiển thị với lines rõ ràng và có animation
- [ ] Tất cả animations chạy ở 60fps trên desktop
- [ ] Mobile responsive và performance tốt
- [ ] Pass accessibility checks (có option reduce motion)

## 🎬 Demo/References

- [Figma/Design mockup link] (nếu có)
- [Video demo của competitor/inspiration] (nếu có)
- Material Design: https://material.io/design/motion
- Framer Motion examples: https://www.framer.com/motion/

## 📊 Priority

**High** - UX improvement ảnh hưởng trực tiếp đến user engagement

## 🏷️ Labels

`enhancement` `frontend` `UI/UX` `animation` `user-experience`

## 👥 Assignee

[Assign to frontend developer]

## ⏱️ Estimate

[Estimate story points or hours based on team velocity]

---

**Note**: Issue này có thể được chia nhỏ thành multiple sub-tasks nếu scope quá lớn.
