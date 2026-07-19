## Playing this hack

You'll need two things: this hack's **patch file**, and your own **legally-obtained, unmodified Pokémon Emerald ROM** (US/English, revision 0). We can't distribute Nintendo's game data ourselves -- the patch only contains the differences from vanilla Emerald, and Flips (below) combines it with your own copy to produce the finished ROM.

### 1. Get Flips (the patching tool)

Download it from the official releases page: https://github.com/Alcaro/Flips/releases

- **Windows:** download the Windows build from the "Assets" section of the latest release, unzip it, run `flips.exe`. No installation needed.
- **Mac/Linux:** see the same releases page, or build from source per the instructions in that repo.

### 2. Apply the patch

1. Open Flips
2. Click **Apply Patch**
3. Select this hack's `.bps` patch file (see the [Releases](../../releases) page of this repo for the latest one)
4. Select your own vanilla Pokémon Emerald ROM
5. Choose where to save the output -- that's your finished, patched ROM

### 3. Play

Load the patched ROM in your emulator of choice (e.g. [mGBA](https://mgba.io/)).

---

## Building from source (developers)

If you want to modify the hack yourself rather than just play it, see [`INSTALL.md`](INSTALL.md) for build toolchain setup, then check out the `my-hack` branch and run `make -j$(nproc)`. This produces `pokeemerald.gba` directly, which is already the finished hack -- no patching needed if you're building from source yourself.

If you want to produce a `.bps` patch to share (rather than the raw ROM), see [Flips](https://github.com/Alcaro/Flips) -- build it with `TARGET=cli make`, then:
```
flips --create --bps-delta baserom.gba pokeemerald.gba my-hack.bps
```
