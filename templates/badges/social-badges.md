# Social Badge Templates

The profile specification uses clickable Shields.io `for-the-badge` badges with spacing between each badge.

## LinkedIn

```html
<a href="https://www.linkedin.com/in/YOUR-ID/">
  <img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" />
</a>
```

**LinkedIn note:** the source documents call out a Shields.io behavior where the LinkedIn glyph may disappear when a custom background is used. Brand blue `#0A66C2` is the safe version; a base64 logo is the alternative when strict custom theming is required. fileciteturn0file1L142-L147

## Instagram

```html
<a href="https://www.instagram.com/YOUR-HANDLE/">
  <img src="https://img.shields.io/badge/Instagram-0A101F?style=for-the-badge&logo=instagram&logoColor=A78BFA&labelColor=0A101F" alt="Instagram" />
</a>
```

## Email

```html
<a href="mailto:YOU@EMAIL.COM">
  <img src="https://img.shields.io/badge/Email-0A101F?style=for-the-badge&logo=gmail&logoColor=10B981&labelColor=0A101F" alt="Email" />
</a>
```

## Recommended grouping

```html
<div align="center">
  <!-- badge 1 -->
  &nbsp;&nbsp;
  <!-- badge 2 -->
  &nbsp;&nbsp;
  <!-- badge 3 -->
</div>
```

The specification intentionally skips a GitHub badge because the GitHub profile already exposes the circular GitHub identity element. fileciteturn0file1L147-L151
