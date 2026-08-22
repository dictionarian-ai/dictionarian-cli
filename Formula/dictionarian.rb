class Dictionarian < Formula
  desc "Generate a data dictionary from a locally reachable database"
  homepage "https://dictionarian.ai"
  version "0.1.0"
  license :cannot_represent

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/dictionarian-ai/dictionarian-cli/releases/download/v#{version}/dictionarian-v#{version}-darwin-arm64.tar.gz"
      sha256 "REPLACE_FROM_RELEASE_WORKFLOW"
    else
      url "https://github.com/dictionarian-ai/dictionarian-cli/releases/download/v#{version}/dictionarian-v#{version}-darwin-x86_64.tar.gz"
      sha256 "REPLACE_FROM_RELEASE_WORKFLOW"
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/dictionarian-ai/dictionarian-cli/releases/download/v#{version}/dictionarian-v#{version}-linux-arm64.tar.gz"
      sha256 "REPLACE_FROM_RELEASE_WORKFLOW"
    else
      url "https://github.com/dictionarian-ai/dictionarian-cli/releases/download/v#{version}/dictionarian-v#{version}-linux-x86_64.tar.gz"
      sha256 "REPLACE_FROM_RELEASE_WORKFLOW"
    end
  end

  depends_on "ripgrep"

  def install
    bin.install "dictionarian"
  end

  test do
    assert_match "Generate a data dictionary", shell_output("#{bin}/dictionarian --help")
  end
end
