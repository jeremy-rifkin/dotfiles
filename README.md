Dotfiles and environment setup. Everyone has their own, these just happen to be mine.

The bootstrap script installs:
- Micromamba
- Oh my zsh
- Some zsh plugins:
  - zsh-autosuggestions
  - zsh-syntax-highlighting
  - zsh-completions
- A theme (an updated version of a [previous theme](https://github.com/jeremy-rifkin/zsh-aqua?tab=readme-ov-file#stingray))
- Atuin
- A handful of developer tools
  - ripgrep
  - fd
  - btop
  - bear
  - bat
  - ninja
  - cowpy
- A handful of zsh utilities and aliases
  - `up`
  - `back`
  - `forward`
  - `take`
  - `lu`
  - `fetch`
  - `sendit`
  - `venv`
  - `serve`
  - ...
- A handful of scripts I use in my workflows
  - checkoutpr.py
  - remote.py
  - bump-conan.py
  - bump-vcpkg.py
- Dotfiles for zsh, vim, gdb, and distrobox

```
mkdir -p ~/.jrenv
rm -rf ~/.jrenv/dotfiles
git clone https://github.com/jeremy-rifkin/dotfiles.git ~/.jrenv/dotfiles
bash -c "cd ~/.jrenv/dotfiles && ./bootstrap.sh"
```

Environment updates can be installed with `update_env` and updates are automatically checked for.
