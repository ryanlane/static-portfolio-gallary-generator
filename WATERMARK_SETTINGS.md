# Enhanced Watermark Settings Documentation

## Overview
The Portfolio Generation settings now include comprehensive watermark customization options for adding professional watermarks to your portfolio images.

## Watermark Settings

### 🏷️ Basic Settings

#### Watermark Enabled
- **Type**: Boolean toggle
- **Description**: Master switch to enable/disable watermarks on all portfolio images
- **Default**: Disabled
- **Note**: When disabled, all other watermark settings are automatically disabled in the UI

#### Watermark Text
- **Type**: Text input
- **Description**: The text to display as watermark on images
- **Default**: Empty
- **Examples**: 
  - "© Your Name"
  - "YourStudio.com"
  - "Your Name Photography"
- **Tip**: Keep it concise for best visual impact

### 🎨 Typography Settings

#### Font Family
- **Type**: Dropdown selection
- **Description**: Google Font family for watermark text
- **Options**:
  - **Roboto** (Clean & Modern) - Default
  - **Open Sans** (Friendly)
  - **Lato** (Professional)
  - **Montserrat** (Elegant)
  - **Source Sans Pro** (Technical)
  - **Poppins** (Playful)
  - **Nunito** (Rounded)
  - **Inter** (UI Optimized)

#### Font Size
- **Type**: Number input (8-72 pixels)
- **Description**: Size of watermark text in pixels
- **Default**: 24px
- **Recommendations**:
  - Small images (thumbnails): 12-16px
  - Medium images: 20-28px
  - Large images: 32-48px

### 🎯 Positioning Settings

#### Vertical Position
- **Type**: Dropdown selection
- **Options**:
  - **Top**: Places watermark at the top of the image
  - **Bottom**: Places watermark at the bottom of the image (Default)
- **Default**: Bottom
- **Note**: Bottom placement is typically less intrusive for viewers

#### Horizontal Position  
- **Type**: Dropdown selection
- **Options**:
  - **Left**: Aligns watermark to the left edge
  - **Center**: Centers watermark horizontally
  - **Right**: Aligns watermark to the right edge (Default)
- **Default**: Right
- **Note**: Right placement follows common copyright conventions

### 🎨 Appearance Settings

#### Opacity
- **Type**: Number input (1-100%)
- **Description**: Transparency level of the watermark
- **Default**: 30%
- **Recommendations**:
  - Subtle branding: 20-40%
  - Standard protection: 40-60%
  - Strong protection: 60-80%
- **Note**: Higher opacity provides more protection but may be more distracting

## Position Combinations

The watermark can be placed in 6 different positions:

| Vertical | Horizontal | Result |
|----------|------------|---------|
| Top      | Left       | Top-left corner |
| Top      | Center     | Top center |
| Top      | Right      | Top-right corner |
| Bottom   | Left       | Bottom-left corner |
| Bottom   | Center     | Bottom center |
| Bottom   | Right      | Bottom-right corner (Default) |

## Best Practices

### ✅ Recommended Settings

**For Professional Portfolios:**
- Font: Lato or Montserrat
- Size: 24-32px
- Position: Bottom-right
- Opacity: 30-40%

**For Copyright Protection:**
- Font: Roboto or Source Sans Pro
- Size: 20-28px
- Position: Bottom-center or Top-right
- Opacity: 50-70%

**For Subtle Branding:**
- Font: Open Sans or Inter
- Size: 16-24px
- Position: Bottom-right
- Opacity: 20-30%

### ⚠️ Things to Avoid

- **Don't use Comic Sans or decorative fonts** - They look unprofessional
- **Don't set opacity too high (>80%)** - It becomes distracting
- **Don't use very large font sizes** - They overwhelm the image
- **Don't place in center of image** - It blocks the main subject

## Technical Implementation

### Backend Function
The `get_watermark_config()` function in `app/main.py` retrieves all watermark settings:

```python
def get_watermark_config():
    """Get watermark configuration from settings"""
    if not get_setting('watermark_enabled'):
        return None
        
    return {
        'enabled': True,
        'text': get_setting('watermark_text'),
        'font_family': get_setting('watermark_font_family'),
        'font_size': get_setting('watermark_font_size'),
        'opacity': get_setting('watermark_opacity'),
        'position_vertical': get_setting('watermark_position_vertical'),
        'position_horizontal': get_setting('watermark_position_horizontal')
    }
```

### Usage in Portfolio Generation
When generating static portfolios, check if watermarks are enabled:

```python
watermark_config = get_watermark_config()
if watermark_config:
    # Apply watermark to images using the configuration
    apply_watermark(image_path, watermark_config)
```

### CSS Integration
When watermarks are disabled, the UI automatically:
- Grays out dependent settings
- Disables form inputs
- Provides visual feedback with smooth transitions

## Database Schema

The following settings are stored in the `app_settings` table:

| Setting Key | Type | Category | Description |
|-------------|------|----------|-------------|
| `watermark_enabled` | boolean | portfolio | Master watermark toggle |
| `watermark_text` | text | portfolio | Watermark text content |
| `watermark_font_family` | text | portfolio | Google Font family name |
| `watermark_font_size` | integer | portfolio | Font size in pixels |
| `watermark_opacity` | integer | portfolio | Opacity percentage (1-100) |
| `watermark_position_vertical` | text | portfolio | Vertical position (top/bottom) |
| `watermark_position_horizontal` | text | portfolio | Horizontal position (left/center/right) |

## Future Enhancements

### Potential Additions
- **Color customization** - Allow custom watermark colors
- **Shadow effects** - Add drop shadows or outlines for better visibility
- **Multiple watermarks** - Support for logo + text watermarks
- **Position fine-tuning** - Pixel-perfect positioning controls
- **Conditional watermarks** - Different settings per gallery or image type

### Implementation Notes
- Google Fonts are automatically loaded when generating portfolios
- Watermark settings are cached for performance
- Settings validation ensures valid font families and position values
- All changes take effect immediately on new portfolio generations

## Testing Recommendations

1. **Test with different image sizes** - Ensure watermarks scale appropriately
2. **Check various position combinations** - Verify all 6 positions work correctly  
3. **Test opacity levels** - Ensure readability without being intrusive
4. **Verify font loading** - Confirm Google Fonts load properly in generated sites
5. **Mobile responsiveness** - Check watermarks on mobile devices

The enhanced watermark system provides professional-grade customization while maintaining ease of use! 🎉
