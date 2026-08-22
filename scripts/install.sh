#!/bin/sh
set -eu

repository="${DICTIONARIAN_GITHUB_REPOSITORY:-dictionarian-ai/dictionarian-cli}"
install_dir="${DICTIONARIAN_INSTALL_DIR:-$HOME/.local/bin}"
version="${DICTIONARIAN_VERSION:-}"

case "$(uname -s)" in
  Darwin) platform="darwin" ;;
  Linux) platform="linux" ;;
  *) echo "Unsupported operating system: $(uname -s)" >&2; exit 1 ;;
esac

case "$(uname -m)" in
  arm64|aarch64) architecture="arm64" ;;
  x86_64|amd64) architecture="x86_64" ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

if [ -z "$version" ]; then
  version="$(curl -fsSL "https://api.github.com/repos/$repository/releases/latest" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n 1)"
fi

if [ -z "$version" ]; then
  echo "Could not determine the latest Dictionarian release." >&2
  exit 1
fi

archive="dictionarian-${version}-${platform}-${architecture}.tar.gz"
base_url="https://github.com/$repository/releases/download/$version"
temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT HUP INT TERM

curl -fsSL "$base_url/$archive" -o "$temporary_dir/$archive"
curl -fsSL "$base_url/SHA256SUMS" -o "$temporary_dir/SHA256SUMS"

expected="$(awk -v file="$archive" '$2 == file { print $1 }' "$temporary_dir/SHA256SUMS")"
if [ -z "$expected" ]; then
  echo "No checksum was published for $archive." >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  actual="$(sha256sum "$temporary_dir/$archive" | awk '{print $1}')"
else
  actual="$(shasum -a 256 "$temporary_dir/$archive" | awk '{print $1}')"
fi

if [ "$expected" != "$actual" ]; then
  echo "Checksum verification failed for $archive." >&2
  exit 1
fi

tar -xzf "$temporary_dir/$archive" -C "$temporary_dir"
mkdir -p "$install_dir"
install -m 0755 "$temporary_dir/dictionarian" "$install_dir/dictionarian"

echo "Installed dictionarian $version to $install_dir/dictionarian"
case ":$PATH:" in
  *":$install_dir:"*) ;;
  *) echo "Add $install_dir to PATH before running dictionarian." ;;
esac
