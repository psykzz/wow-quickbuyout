<p align="center"><img src="media/logo.png" width="160" alt="Quick Buyout logo"></p>

# wow-quickbuyout

A World of Warcraft addon that removes the Auction House buyout confirmation popup for gear. Clicking **Buyout** immediately purchases the cheapest armor or weapon auction in the group you are viewing, similar to TradeSkillMaster's quick buy.

## Features

- **One-click buyout** - no confirmation popup for armor and weapon auctions.
- **Always buys the cheapest** - the cheapest buyout in the current item group is purchased, skipping your own auctions and bid-only listings.
- **Auto-selects the cheapest row** - the Buyout button is ready to click and shows the price you will pay; after each purchase the next cheapest is selected, so you can click repeatedly.
- **Double-purchase guard** - extra clicks are ignored while a purchase is in flight, and auctions already bought are never retried while the result list catches up.
- **Everything else unchanged** - commodities, non-gear items, bids, and Blizzard's unique-crafted-item warning keep their normal confirmations.

## Compatibility

Works only with the modern (retail-style) Auction House UI (`Blizzard_AuctionHouseUI`):

- Retail
- Mists of Pandaria Classic
- Classic Era / Anniversary clients that use the new Auction House UI

Clients using the legacy Auction House UI are not supported.

## Installation

Install via CurseForge, Wago, or manually by downloading the latest release from GitHub and extracting the `QuickBuyout` folder into `World of Warcraft\<flavor>\Interface\AddOns\`.

## Usage

1. Open the Auction House and search for an armor or weapon item.
2. Click the item group to see its auctions.
3. Click **Buyout**. The cheapest auction is bought instantly.

There are no settings or slash commands.

## Development

### Creating a Release

This addon uses BigWigs Packager for automated releases. To create a new release:

1. Update the version in your local repository
2. Create and push a git tag:
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```
3. The GitHub Actions workflow will automatically:
   - Package the addon
   - Create a GitHub release
   - Upload to CurseForge (if `CF_API_KEY` secret is configured and `## X-Curse-Project-ID` is set in the TOC)
   - Upload to Wago (if `WAGO_API_TOKEN` secret is configured and `## X-Wago-ID` is set in the TOC)

### Required Secrets

To enable automatic uploads, configure these repository secrets:

- `CF_API_KEY` - CurseForge API key for uploading to CurseForge
- `WAGO_API_TOKEN` - Wago API token for uploading to Wago Addons

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### Logo

`media/logo.png` is the 1:1 (512x512) project logo for CurseForge and Wago. It is excluded from the packaged addon. Regenerate it with `python media/generate_logo.py` (requires Pillow).

## License

All Rights Reserved
