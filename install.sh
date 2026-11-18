#!/usr/bin/env bash
# HannibalBB installer — sets up deps and the global `hannibal` command (no sudo).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🐘 Installing HannibalBB…"
python3 -m pip install --user -q -r "$DIR/requirements.txt" 2>/dev/null \
  || python3 -m pip install --user -q --break-system-packages -r "$DIR/requirements.txt"

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/hannibal" <<EOF
#!/usr/bin/env bash
exec python3 "$DIR/hannibal.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/hannibal"

echo "✅ Done."
case ":$PATH:" in
  *":$HOME/.local/bin:"*) echo "   Run it now:  hannibal" ;;
  *) echo "   Add ~/.local/bin to your PATH, then run:  hannibal"
     echo "   e.g.  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc" ;;
esac
