#!/usr/bin/env bash
# patch-skip-multimodal.sh
# Apply the reference_image_selector multimodal skip patch for ViMax
# This replaces the multimodal image selection with text-only fallback
# to avoid SiliconFlow timeout issues.
#
# Usage: bash scripts/patch-skip-multimodal.sh
#
# Restore: git checkout agents/reference_image_selector.py

set -euo pipefail
cd "$(dirname "$0")/.."  # project root ~/ViMax/

TARGET="agents/reference_image_selector.py"

if [ ! -f "$TARGET" ]; then
  echo "❌ $TARGET not found. Run from ViMax project root."
  exit 1
fi

# Check if already patched (look for the fallback marker)
if grep -q "text-only fallback" "$TARGET"; then
  echo "✅ Patch already applied — no action needed."
  exit 0
fi

# Verify the target code block exists
if ! grep -q "# 2. filter images using multimodal model" "$TARGET"; then
  echo "❌ Unrecognized file structure. Expected 'filter images using multimodal model' marker."
  exit 1
fi

# Apply the patch using sed (removes multimodal block, inserts text-only fallback)
sed -i '/# 2. filter images using multimodal model/,/raise e/{//!d;}' "$TARGET"
cat >> "$TARGET" << 'PATCH'

        # 2. text-only fallback (skip multimodal to avoid SiliconFlow timeout)
        # Use the text-only filter result directly if stage 1 ran, else use all images
        reference_image_path_and_text_pairs = filtered_image_path_and_text_pairs[:8]
        # Generate a simple prompt from the frame description
        prompt_parts = []
        for idx, (_, text) in enumerate(reference_image_path_and_text_pairs):
            prompt_parts.append(f"Image {idx}: {text}")
        prompt_parts.append(f"Create an image based on: {frame_description}")
        text_prompt = "\n".join(prompt_parts)
        return {
            "reference_image_path_and_text_pairs": reference_image_path_and_text_pairs,
            "text_prompt": text_prompt,
        }
PATCH

echo "✅ Patch applied. $TARGET now uses text-only reference image selection."
echo "   To restore, run: git checkout $TARGET"
