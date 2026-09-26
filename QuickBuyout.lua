local PENDING_TIMEOUT = 5

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

local function FindCheapest(itemKey)
	local cheapest
	for i = 1, C_AuctionHouse.GetNumItemSearchResults(itemKey) do
		local info = C_AuctionHouse.GetItemSearchResultInfo(itemKey, i)
		if info and info.buyoutAmount and info.buyoutAmount > 0
			and not boughtAuctionIDs[info.auctionID] and not IsOwned(info)
			and (not cheapest or info.buyoutAmount < cheapest.buyoutAmount) then
			cheapest = info
		end
	end
	return cheapest
end

local function SelectCheapest()
	local itemKey = itemBuyFrame.itemKey
	if not itemBuyFrame:IsShown() or not IsGear(itemKey) then
		return
	end

	local cheapest = FindCheapest(itemKey)
	local selected = itemBuyFrame.ItemList:GetSelectedEntry()
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

	local cheapest = FindCheapest(itemKey)
	if not cheapest then
		UIErrorsFrame:AddExternalErrorMessage(BROWSE_NO_RESULTS)
		return
	end

	if cheapest.buyoutAmount > GetMoney() then
		UIErrorsFrame:AddExternalErrorMessage(AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
		return
	end

	-- Keep Blizzard's warning for unique crafted items (retail only).
	if AuctionHouseUtil.IsAuctionIDUniqueShadowlandsCrafted
		and AuctionHouseUtil.IsAuctionIDUniqueShadowlandsCrafted(cheapest.auctionID) then
		itemBuyFrame:GetAuctionHouseFrame():StartItemBuyout(cheapest.auctionID, cheapest.buyoutAmount)
		return
	end

	pendingAuctionID = cheapest.auctionID
	pendingToken = pendingToken + 1
	local token = pendingToken
	C_Timer.After(PENDING_TIMEOUT, function()
		if token == pendingToken then
			ClearPending()
		end
	end)

	-- Runs inside the Buyout button's OnClick, which supplies the required hardware event.
	C_AuctionHouse.PlaceBid(cheapest.auctionID, cheapest.buyoutAmount)
end

local function Setup()
	if itemBuyFrame or not AuctionHouseFrame or not AuctionHouseFrame.ItemBuyFrame then
		return
	end

	itemBuyFrame = AuctionHouseFrame.ItemBuyFrame
	itemBuyFrame.BuyoutFrame:SetBuyoutCallback(QuickBuy)

	itemBuyFrame:HookScript("OnEvent", function(_, event)
		if event == "ITEM_SEARCH_RESULTS_UPDATED" or event == "ITEM_SEARCH_RESULTS_ADDED" then
			SelectCheapest()
		end
	end)
	hooksecurefunc(itemBuyFrame, "SetItemKey", SelectCheapest)
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
			SelectCheapest()
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
