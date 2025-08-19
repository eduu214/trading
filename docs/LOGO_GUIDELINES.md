# AlphaStrat Logo Guidelines

## Logo Files

The AlphaStrat logo should be placed in the following locations:

### Required Files
1. **Main Logo**: `frontend/public/logos/alphastrat-logo.png`
   - Primary logo file used throughout the application
   - Recommended size: 512x512px or larger
   - Format: PNG with transparent background

2. **Favicon**: `frontend/public/logos/favicon.ico`
   - Browser tab icon
   - Size: 32x32px
   - Format: ICO file

3. **PWA Icons**:
   - `frontend/public/logos/alphastrat-logo-192.png` (192x192px)
   - `frontend/public/logos/alphastrat-logo-512.png` (512x512px)
   - Used for Progressive Web App manifest

## Logo Design

The AlphaStrat logo features:
- A stylized "A" shape representing growth and upward momentum
- Chart/graph elements integrated into the design
- Blue gradient color scheme (#3B82F6 to #1E40AF)
- Clean, modern aesthetic suitable for a financial technology platform

## Usage Guidelines

### Color Variations
- **Primary**: Full color on light backgrounds
- **Inverse**: White version for dark backgrounds
- **Monochrome**: Single color for specific use cases

### Spacing
- Maintain clear space around the logo equal to at least 25% of the logo's height
- Never crowd the logo with other elements

### Size Requirements
- Minimum size: 32px height for digital displays
- Always maintain aspect ratio when resizing

### Placement
- Header: 40x40px with text
- Homepage hero: 80x80px without text
- Footer: 32x32px with text

## Implementation

The logo is implemented as a React component at `frontend/src/components/Logo.tsx` with the following props:
- `width`: Logo width in pixels
- `height`: Logo height in pixels
- `showText`: Whether to display "AlphaStrat" text
- `className`: Additional CSS classes

## File Formats

Store logos in these formats:
- **PNG**: For general web use (transparent background)
- **SVG**: For scalable graphics (if available)
- **ICO**: For favicon only

## Don'ts
- Don't stretch or distort the logo
- Don't change the colors without approval
- Don't add effects like drop shadows or outlines
- Don't use low-resolution versions
- Don't place on busy backgrounds that reduce visibility