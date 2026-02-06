# CSS Utility Classes & Styling Guide - _Tech Talent Showcase_

This is intended for developer use on implementing stylings we have in place, please refer to the design team for latest information.
At the moment we are utilizing MUI where applicable and Tailwind when necessary.

## Reference Designs

- [Design System - Colors](<https://www.figma.com/design/XzI7NG0Z3Z2lYAQqZE6Rjv/Design-System-(v1.1)?node-id=189-452&t=mYI5oMX0TgrOFqVR-0>)

## Files of Interest

- @/mui.theme.tsx
- app/ui/global.css

## Colors

### Knowing The Color Palette: our complete list of colors

##### These colors do not need to be memorized, these colors should match accordingly to any Figma designs provided by the design team.

```bash
palette: {
        primary: {
          main: "#047F9C",
          light: "#C4EBF3",
        },
        secondary: {
          main: "#014260",
        },
        success: {
          main: "#61CE70",
          bg: "#61CE70",
          text: "#001C00",
        },
        warning: {
          main: "#EC7304",
          bg: "#EC7304",
          text: "#FFFFFF",
        },
        error: {
          main: "#DB241C",
          bg: "#DB241C",
          text: "#FFFFFF",
        },
        accent: {
          main: "#61CE70",
          light: "#C1F2C8",
        },
        neutral: {
          white: "#FFFFFF",
          100: "#F6F6F6",
          200: "#E5E5E5",
          300: "#CCCCCC",
          400: "#B3B3B3",
          500: "#999999",
          600: "#8F8F8F",
          700: "#707070",
          800: "#363636",
          900: "#191919",
          black: "#000000",
        },
        blue: {
          100: "#E1F5F9",
          200: "#D6F1F7",
          300: "#81BFCD",
          400: "#4FA5BA",
          500: "#3699B0",
          600: "#006682",
          700: "#003350",
        },
        green: {
          100: "#EFFAF1",
          200: "#DFF5E2",
          300: "#A0E2A9",
          500: "#2E9B3D",
          600: "#158124",
          400: "#81D88D",
          700: "#00680A",
          800: "#003500",
        },
      },
```

### Applying the colors: Example use of our primary main and neutral white colors

MUI Component Use within a **MUI component Button's sx prop**

```js
<Button
  sx={{
    backgroundColor: "primary.main",
    color: "neutral.white",
  }}
>
  Example
</Button>
```

Tailwind Component Use within an element's className

```html
<button className="bg-primary-main text-neutral-white">Example</button>
```

Incompatible with MUI and Tailwind use (the example is only for syntax, the element is the same as other excamples for consistency and is compatible)

```html
<button
  style="background-color: var(--primary-main); color: var(--neutral-white);"
>
  Example
</button>
```

## Final Takeaways

- To ensure consistency and flexibility it is important to use the color palette variables. If design provides an update to colors in the future then we only have to update the variables to apply across our entire application if we have properly applied the above tools.
- Figma's _dev tool export_ for components/elements often uses raw values such as #047F9C, so you'll want to replace it accordingly
- Technically you can use Tailwind classnames within MUI's sx prop, it's generally not recommended as it can lead to potential conflicts and a less clean separation of concerns between the two styling approaches
- Per developer team meeting we have decided to use MUI sx props when working with MUI components, Tailwind when MUI components are not applicable, and global.css when both MUI and Tailwind utility classes are not compatible otherwise
