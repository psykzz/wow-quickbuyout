# Agent Instructions

## Scope

Quick Buyout only targets the modern Auction House UI (`Blizzard_AuctionHouseUI`, `AuctionHouseFrame`). Do not add support for the legacy `AuctionFrame` UI.

## Hardware events and protected calls

`C_AuctionHouse.PlaceBid` requires a hardware event (`#hwevent`) and cannot be called from `/run`, timers, or event handlers.

- The purchase must happen synchronously inside the Buyout button's `OnClick` chain. This addon does that by replacing the ItemBuyFrame's buyout callback (`AuctionHouseFrame.ItemBuyFrame.BuyoutFrame:SetBuyoutCallback`).
- Never move `PlaceBid` behind `C_Timer`, an event, or any other deferred path. It will silently fail.
- Do not try to auto-accept Blizzard's `StaticPopup` dialogs. Bypass them by calling the API directly from the click instead.

## Scroll box safety

`AuctionHouseItemListMixin:SetSelectedEntryByCondition(..., scrollTo)` calls `ScrollToElementDataIndex`, which errors if the ScrollBox has no data provider yet. This is common right after `ITEM_SEARCH_RESULTS_UPDATED` or `SetItemKey`. Select rows with `ItemList:SetSelectedEntry(rowData)` instead.

## Stale results

The item search results are not refreshed immediately after a purchase. Always skip auction IDs recorded in `boughtAuctionIDs` (populated from `AUCTION_HOUSE_PURCHASE_COMPLETED`) when validating the selection or picking the cheapest auction.

## Selection behaviour

Buyout purchases the auction the user has selected. `SelectCheapest(force)` only overrides the selection when forced (new item group via `SetItemKey`, or after a purchase completes) or when the current selection is no longer buyable. Do not force it from `ITEM_SEARCH_RESULTS_*` events, or it will undo manual selections.

## Reference source

Blizzard UI source: https://github.com/Gethe/wow-ui-source (`Interface/AddOns/Blizzard_AuctionHouseUI/Shared/`).
