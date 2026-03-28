#!/usr/bin/env bash
# Export an SVG icon to multiple sizes for web, iOS, and Android
# Usage: export-icons.sh <input.svg> <output-dir> [--platforms web,ios,android]
#
# Requires: rsvg-convert (librsvg) or Inkscape for SVG→PNG conversion
# Falls back to sips on macOS if neither is available
#
# Output structure:
#   output-dir/
#   ├── web/
#   │   ├── favicon-16x16.png
#   │   ├── favicon-32x32.png
#   │   ├── favicon.ico (if convert available)
#   │   ├── apple-touch-icon-180x180.png
#   │   ├── icon-192x192.png
#   │   └── icon-512x512.png
#   ├── ios/
#   │   └── AppIcon.appiconset/
#   │       ├── Contents.json
#   │       ├── icon-20x20@2x.png ... icon-1024x1024.png
#   └── android/
#       ├── mipmap-mdpi/ic_launcher.png (48x48)
#       ├── mipmap-hdpi/ic_launcher.png (72x72)
#       ├── mipmap-xhdpi/ic_launcher.png (96x96)
#       ├── mipmap-xxhdpi/ic_launcher.png (144x144)
#       └── mipmap-xxxhdpi/ic_launcher.png (192x192)

set -euo pipefail

INPUT_SVG="${1:-}"
OUTPUT_DIR="${2:-}"
PLATFORMS="${3:---platforms web,ios,android}"

if [[ -z "$INPUT_SVG" || -z "$OUTPUT_DIR" ]]; then
  echo '{"error": "Usage: export-icons.sh <input.svg> <output-dir> [--platforms web,ios,android]"}'
  exit 1
fi

if [[ ! -f "$INPUT_SVG" ]]; then
  echo "{\"error\": \"Input file not found: $INPUT_SVG\"}"
  exit 1
fi

# Parse platforms
PLATFORMS_STR="${PLATFORMS#--platforms }"
IFS=',' read -ra PLATFORM_LIST <<< "$PLATFORMS_STR"

# Find SVG converter
CONVERTER=""
if command -v rsvg-convert &>/dev/null; then
  CONVERTER="rsvg-convert"
elif command -v inkscape &>/dev/null; then
  CONVERTER="inkscape"
elif [[ "$(uname)" == "Darwin" ]] && command -v sips &>/dev/null; then
  CONVERTER="sips"
else
  echo '{"error": "No SVG converter found. Install librsvg (brew install librsvg) or Inkscape."}'
  exit 1
fi

convert_svg() {
  local input="$1" output="$2" size="$3"
  case "$CONVERTER" in
    rsvg-convert)
      rsvg-convert -w "$size" -h "$size" "$input" -o "$output"
      ;;
    inkscape)
      inkscape "$input" --export-type=png --export-filename="$output" -w "$size" -h "$size" 2>/dev/null
      ;;
    sips)
      # sips can't handle SVG directly; convert to PNG first via a temp
      local tmpfile
      tmpfile="$(mktemp /tmp/brandy-icon-XXXXX.png)"
      # Use qlmanage as fallback on macOS
      qlmanage -t -s "$size" -o /tmp "$input" 2>/dev/null || true
      local ql_output="/tmp/$(basename "$input").png"
      if [[ -f "$ql_output" ]]; then
        sips -z "$size" "$size" "$ql_output" --out "$output" 2>/dev/null
        rm -f "$ql_output"
      fi
      rm -f "$tmpfile"
      ;;
  esac
}

exported_files=()

# Web icons
if [[ " ${PLATFORM_LIST[*]} " =~ " web " ]]; then
  WEB_DIR="$OUTPUT_DIR/web"
  mkdir -p "$WEB_DIR"

  for size in 16 32 180 192 512; do
    case $size in
      16|32) name="favicon-${size}x${size}.png" ;;
      180) name="apple-touch-icon-${size}x${size}.png" ;;
      *) name="icon-${size}x${size}.png" ;;
    esac
    convert_svg "$INPUT_SVG" "$WEB_DIR/$name" "$size"
    exported_files+=("web/$name")
  done

  # Copy source SVG
  cp "$INPUT_SVG" "$WEB_DIR/icon.svg"
  exported_files+=("web/icon.svg")
fi

# iOS icons (xcassets)
if [[ " ${PLATFORM_LIST[*]} " =~ " ios " ]]; then
  IOS_DIR="$OUTPUT_DIR/ios/AppIcon.appiconset"
  mkdir -p "$IOS_DIR"

  # iOS icon sizes: point-size@scale
  declare -A IOS_ICONS=(
    ["icon-20@2x"]=40
    ["icon-20@3x"]=60
    ["icon-29@2x"]=58
    ["icon-29@3x"]=87
    ["icon-40@2x"]=80
    ["icon-40@3x"]=120
    ["icon-60@2x"]=120
    ["icon-60@3x"]=180
    ["icon-76@2x"]=152
    ["icon-83.5@2x"]=167
    ["icon-1024"]=1024
  )

  contents_images=""
  for key in "${!IOS_ICONS[@]}"; do
    size="${IOS_ICONS[$key]}"
    filename="${key}.png"
    convert_svg "$INPUT_SVG" "$IOS_DIR/$filename" "$size"
    exported_files+=("ios/AppIcon.appiconset/$filename")

    # Parse for Contents.json
    point_size="${key#icon-}"
    scale="1x"
    if [[ "$point_size" == *"@2x" ]]; then
      point_size="${point_size%@2x}"
      scale="2x"
    elif [[ "$point_size" == *"@3x" ]]; then
      point_size="${point_size%@3x}"
      scale="3x"
    fi

    contents_images="${contents_images}    {\"filename\": \"${filename}\", \"idiom\": \"universal\", \"platform\": \"ios\", \"size\": \"${point_size}x${point_size}\", \"scale\": \"${scale}\"},
"
  done

  # Write Contents.json
  cat > "$IOS_DIR/Contents.json" <<CONTENTSEOF
{
  "images": [
${contents_images%,
}
  ],
  "info": {
    "author": "brandy",
    "version": 1
  }
}
CONTENTSEOF
  exported_files+=("ios/AppIcon.appiconset/Contents.json")
fi

# Android icons (mipmap)
if [[ " ${PLATFORM_LIST[*]} " =~ " android " ]]; then
  declare -A ANDROID_DENSITIES=(
    ["mipmap-mdpi"]=48
    ["mipmap-hdpi"]=72
    ["mipmap-xhdpi"]=96
    ["mipmap-xxhdpi"]=144
    ["mipmap-xxxhdpi"]=192
  )

  for density in "${!ANDROID_DENSITIES[@]}"; do
    size="${ANDROID_DENSITIES[$density]}"
    DENSITY_DIR="$OUTPUT_DIR/android/$density"
    mkdir -p "$DENSITY_DIR"
    convert_svg "$INPUT_SVG" "$DENSITY_DIR/ic_launcher.png" "$size"
    exported_files+=("android/$density/ic_launcher.png")
  done
fi

# Output result
echo "{\"status\": \"complete\", \"output_dir\": \"$OUTPUT_DIR\", \"files\": $(printf '%s\n' "${exported_files[@]}" | jq -R . | jq -s .)}"
