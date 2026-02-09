for dir in {A..Z}; do
  mkdir -p "$dir"
done
mkdir -p 0

# Move files into directories named after the first letter
for file in *; do
  if [[ -f "$file" ]]; then
    first_char=$(echo "$file" | head -c 1 | tr '[:lower:]' '[:upper:]')
    if [[ "$first_char" =~ [A-Z] ]]; then
      mv -n "$file" "$first_char/"
    elif [[ "$file" =~ ^[0-9] ]]; then
      mv -n "$file" "0/"
    fi
  fi
done
