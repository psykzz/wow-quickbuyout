local PENDING_TIMEOUT = 5
local NO_AUCTION_SELECTED_ERROR = "Quick Buyout: select an auction first."

local GetItemInfoInstant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant

local itemBuyFrame
local pendingAuctionID
local pendingToken = 0
-- Auctions we already bought; the result list can lag behind the server.
local boughtAuctionIDs = {}

local function IsGear(itemKey)
	if not itemKey or not itemKey.itemID then
		return false
	end
	local classID = select(6, GetItemInfoInstant(itemKey.itemID))
	return classID == Enum.ItemClass.Weapon or classID == Enum.ItemClass.Armor
end

local function IsOwned(info)
	if AuctionHouseUtil and AuctionHouseUtil.IsOwnedAuction then
		return AuctionHouseUtil.IsOwnedAuction(info)
	end
	return info.containsOwnerItem
end

local function IsBuyable(info)
	return info and info.buyoutAmount and info.buyoutAmount > 0
		and not boughtAuctionIDs[info.auctionID] and not IsOwned(info)
end

-- Returns the cheapest buyable auction, plus the fresh result for wantedAuctionID if it is still buyable.
local function ScanResults(itemKey, wantedAuctionID)
	local cheapest, wanted
	for i = 1, C_AuctionHouse.GetNumItemSearchResults(itemKey) do
		local info = C_AuctionHouse.GetItemSearchResultInfo(itemKey, i)
		if IsBuyable(info) then
			if not cheapest or info.buyoutAmount < cheapest.buyoutAmount then
				cheapest = info
			end
			if info.auctionID == wantedAuctionID then
				wanted = info
			end
		end
	end
	return cheapest, wanted
end

-- Selects the cheapest auction. Unless forced, a still-buyable selection is left alone.
local function SelectCheapest(force)
	local itemKey = itemBuyFrame.itemKey
	if not itemBuyFrame:IsShown() or not IsGear(itemKey) then
		return
	end

	local selected = itemBuyFrame.ItemList:GetSelectedEntry()
	local cheapest, current = ScanResults(itemKey, selected and selected.auctionID)
	if current and not force then
		return
	end

	if cheapest then
		if not selected or selected.auctionID ~= cheapest.auctionID then
			-- Select without scrolling: the ScrollBox may not have its data provider yet.
			itemBuyFrame.ItemList:SetSelectedEntry(cheapest)
		end
	elseif selected then
		itemBuyFrame.ItemList:SetSelectedEntry(nil)
	end
end

local function ClearPending()
	pendingAuctionID = nil
end

local function QuickBuy()
	local itemKey = itemBuyFrame.itemKey
	if not IsGear(itemKey) then
		itemBuyFrame:BuyoutItem()
		return
	end

	if pendingAuctionID then
		return
	end

	local selected = itemBuyFrame.ItemList:GetSelectedEntry()
	local _, target = ScanResults(itemKey, selected and selected.auctionID)
	if not target then
		UIErrorsFrame:AddExternalErrorMessage(NO_AUCTION_SELECTED_ERROR)
		SelectCheapest(true)
		return
	end

	if target.buyoutAmount > GetMoney() then
		UIErrorsFrame:AddExternalErrorMessage(AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
		return
	end

	-- Keep Blizzard's warning for unique crafted items (retail only).
	if AuctionHouseUtil.IsAuctionIDUniqueShadowlandsCrafted
		and AuctionHouseUtil.IsAuctionIDUniqueShadowlandsCrafted(target.auctionID) then
		itemBuyFrame:GetAuctionHouseFrame():StartItemBuyout(target.auctionID, target.buyoutAmount)
		return
	end

	pendingAuctionID = target.auctionID
	pendingToken = pendingToken + 1
	local token = pendingToken
	C_Timer.After(PENDING_TIMEOUT, function()
		if token == pendingToken then
			ClearPending()
		end
	end)

	-- Runs inside the Buyout button's OnClick, which supplies the required hardware event.
	C_AuctionHouse.PlaceBid(target.auctionID, target.buyoutAmount)
end

local function Setup()
	if itemBuyFrame or not AuctionHouseFrame or not AuctionHouseFrame.ItemBuyFrame then
		return
	end

	itemBuyFrame = AuctionHouseFrame.ItemBuyFrame
	itemBuyFrame.BuyoutFrame:SetBuyoutCallback(QuickBuy)

	itemBuyFrame:HookScript("OnEvent", function(_, event)
		if event == "ITEM_SEARCH_RESULTS_UPDATED" or event == "ITEM_SEARCH_RESULTS_ADDED" then
			SelectCheapest(false)
		end
	end)
	hooksecurefunc(itemBuyFrame, "SetItemKey", function()
		SelectCheapest(true)
	end)
end

local events = CreateFrame("Frame")
events:RegisterEvent("ADDON_LOADED")
events:RegisterEvent("AUCTION_HOUSE_PURCHASE_COMPLETED")
events:RegisterEvent("AUCTION_HOUSE_SHOW_ERROR")
events:RegisterEvent("AUCTION_HOUSE_CLOSED")
events:SetScript("OnEvent", function(_, event, arg1)
	if event == "ADDON_LOADED" then
		if arg1 == "Blizzard_AuctionHouseUI" then
			Setup()
		end
	elseif event == "AUCTION_HOUSE_PURCHASE_COMPLETED" then
		boughtAuctionIDs[arg1] = true
		if arg1 == pendingAuctionID then
			ClearPending()
		end
		if itemBuyFrame then
			SelectCheapest(true)
		end
	elseif event == "AUCTION_HOUSE_SHOW_ERROR" then
		ClearPending()
	elseif event == "AUCTION_HOUSE_CLOSED" then
		ClearPending()
		wipe(boughtAuctionIDs)
	end
end)

local IsAddOnLoaded = (C_AddOns and C_AddOns.IsAddOnLoaded) or IsAddOnLoaded
if IsAddOnLoaded("Blizzard_AuctionHouseUI") then
	Setup()
end
